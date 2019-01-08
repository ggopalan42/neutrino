#! /usr/bin/env python

import sys
import logging

import pandas as pd
import numpy as np

from datetime import datetime
from datetime import timedelta
from collections import namedtuple
# Local imports
import query_cass


# ------------- TBD: Move all following to config files ------------
# This all needs to be finessed some more
# Below line splits the staff and employee helpdesk line.
# This is not very correct. A sloghtly diagonal line is likely better
STAFF_EMPLOYEE_SPLIT_LINE = 0, 240, 1280, 240  # format is x1, y1, x2, y2
# For now, assume the line is a simple horiz line.
# This means anything greater that y1/y2 is employee and less than is staff
SPLIT_HORIZ_POINT = 100  # This is a guess at this point

# Time format - all needs to go into one giant config
# HELPDESK_TIMEFORMAT_HR = '%Y-%m-%d_%H:%M:%S'
STANDARD_TIMEFORMAT_HR = '%Y-%m-%d_%H:%M:%S'
HELPDESK_STREAM_NAME = 'bldg_d_f4_helpdesk'

# --------- Not sure if following needs to go to config file or not -------
# For now hardcode local TZ to be US/Pacific
# LOCAL_TZ = 'US/Pacific'
PACIFIC_TZ = 'US/Pacific'


# Time utilities. Perhaps a good set to move to a separate utils file
def dt_get_last_24hrs(time_zone):
    ''' Determine the start/end times for last 24 hours.

    Arguments: None

    Returns:
        start_time = Start time of 24 hrs from time now in standard timeformat
        end_time = Current minute  in standard timeformat

    '''
    time_now = datetime.now()
    # Round the the time to nearest minute - this is the resolution supported
    time_now = time_now - timedelta(seconds=time_now.second)
    time_now_minus_24hrs = time_now - timedelta(hours=24)
    # Convert start and end times to string
    start_time = time_now.strftime(STANDARD_TIMEFORMAT_HR)
    end_time = time_now_minus_24hrs.strftime(STANDARD_TIMEFORMAT_HR)
    return start_time, end_time


# Time utilities. Perhaps a good set to move to a separate utils file
def dt_get_yesterday(time_zone):
    ''' Determine the start/end times yesterday.

    Arguments: time_zone - unused for now

    Returns:
        start_time = Start time of beginning of yesterday
        end_time = End time of yesterday

    '''
    # Get time now and compute yesterday time
    time_now = datetime.now()
    yesterday = time_now - timedelta(days=1)
    # Get the start and end of yesterday times
    yesterday_start = yesterday - timedelta(hours=yesterday.hour,
                                            minutes=yesterday.minute, 
                                            seconds=yesterday.second, 
                                            microseconds=yesterday.microsecond)
    yesterday_end = yesterday_start + timedelta(hours=23, minutes=59)
    # Format them as strings
    start_time = yesterday_start.strftime(STANDARD_TIMEFORMAT_HR)
    end_time = yesterday_end.strftime(STANDARD_TIMEFORMAT_HR)
    return start_time, end_time


SELECTIME_FUNCTION_MAP = {
    'last_24hrs': dt_get_last_24hrs,
    'last_day': dt_get_yesterday,
    'last_7days': dt_get_yesterday,     # I know, I know . . .
    'last_week': dt_get_yesterday,     # I know, I know . . .
}


def selecttime_to_start_end(select_str, timezone):
    ''' Given the select string, return the start/end times for the string

    Arguments:
        select_str: that can contain the following four strings:
                     last_24hrs, last_day, last_7days, last_week
        timezone - not used here, just passed along


    Returns: start and end times appropriate for the select_str
    '''
    start_time, end_time = SELECTIME_FUNCTION_MAP[select_str](timezone)
    return start_time, end_time


def epoch_to_localtz(df_epoch, local_tz=PACIFIC_TZ):
    ''' Convert from epoch time to specified timezone'''
    return pd.to_datetime(df_epoch/1e6, unit='s').dt.tz_localize('UTC')  \
        .dt.tz_convert(local_tz)


def datetime_to_localtz_hr(dt_value, local_tz=PACIFIC_TZ):
    ''' From a datetime object, return a human readable time in local time zone
    '''
    return dt_value.tz_convert(PACIFIC_TZ).strftime(STANDARD_TIMEFORMAT_HR)


def df_to_bar_chart_items(in_df, num_buckets):
    '''  ##### This function is mostly depricated as of 12/10/2018 ###### 
       Convert a pandas dataframe in the Cass SV2 schema format to a set of
        values and labels ready for charting as a bar chart

    Argument:
        in_df: A pandas dataframe in the SV2 schema format (reproduced below)

     Returns:
         A tuple of labels and values that can be fed directly into a bar
         charting utility

     SV2 Format: detect_time100, detect_time_hr, confidence, found,
                 stream_group_name, stream_name, msg_format_version,
                 startX, endX, startY, endY
    '''

    # Filter the input dataframe into helpdesk and archimedes dataframes
    # in_df_person = in_df[in_df.found == 'person']
    # archimedes_person_df = in_df[(in_df.found == 'person') &
    #                       (in_df.stream_name == 'bldg_d_f2_conf_archimedes')]
    hd_person_df = in_df[(in_df.found == 'person') & (in_df.stream_name ==
                                                      'bldg_d_f4_helpdesk')]

    # Create a datetime object column in local timezone. This column will
    # lated be used as index
    hd_person_df['local_detect_time'] = epoch_to_localtz(hd_person_df
                                                         .detect_time100/100,
                                                         PACIFIC_TZ)

    # Create a column in the helpdesk df that also contains the center point
    # of the detected object
    hd_person_df['center_pointX'] = (hd_person_df.endx - hd_person_df.startx)/2
    hd_person_df['center_pointY'] = (hd_person_df.endy - hd_person_df.starty)/2

    # Now split them into employee and staff df
    hd_employee_df = hd_person_df[hd_person_df.center_pointX >
                                  SPLIT_HORIZ_POINT]
    hd_staff_df = hd_person_df[hd_person_df.center_pointX <
                               SPLIT_HORIZ_POINT]

    # Re-index the DataFrames so the detect time is the index.
    # This is needed to resample the df
    # hdemployee_df['local_detect_time'] = epoch_to_localtz(hd_employee_df.detect_time100/100, PACIFIC_TZ)
    # hd_staff_df['local_detect_time'] = epoch_to_localtz(hd_staff_df.detect_time100/100, PACIFIC_TZ)
    hd_employee_df.set_index('local_detect_time', inplace=True)
    hd_staff_df.set_index('local_detect_time', inplace=True)

    # print(hd_employee_df.iloc[0])
    # print(hd_employee_df.index)

    # Do some re-sampling
    hd_staff_1sec = hd_staff_df.resample('1S').sum()
    hd_employee_1sec = hd_employee_df.resample('1S').sum()

    # This is simply setting the column 'staff/employee_present' to a 1
    # if there were any numebr of persons present in that second.
    hd_staff_1sec['staff_present'] =        \
        np.where(hd_staff_1sec['confidence'] > 0, 1, 0)
    hd_employee_1sec['employee_present'] =  \
        np.where(hd_employee_1sec['confidence'] > 0, 1, 0)

    # Resample the entire thing by 1 min, but this time summing the columns.
    # hd_staff_1m = hd_staff_1sec.resample('1T').sum()
    # hd_employee_1m = hd_employee_1sec.resample('1T').sum()

    # Resample the entire thing by 10 min, but this time summing the columns.
    hd_staff_10m = hd_staff_1sec.resample('10T').sum()
    hd_employee_10m = hd_employee_1sec.resample('10T').sum()

    # Select only the staff and employee present columns
    hd_staff_10m = hd_staff_10m['staff_present']
    hd_employee_10m = hd_employee_10m['employee_present']

    # Resample the entire thing hourly, but this time summing the columns.
    # hd_staff_1h = hd_staff_1sec.resample('H').sum()
    # hd_employee_1h = hd_employee_1sec.resample('H').sum()

    # Get the start and end times in epochs. The /100 is because detect time
    # last two digits represent something else and needs to be whacked
    # start_epoch = int(in_df.iloc[0].detect_time100/100)
    # end_epoch = int(in_df.iloc[-1].detect_time100/100)

    hd_staff_10m_list = hd_staff_10m.values
    hd_employee_10m_list = hd_employee_10m.values
    # Get the values of the index for the x-axis labels (the time stamps)
    hd_xaxis_labels = [datetime_to_localtz_hr(x) for x in hd_staff_10m.index]
    # print(hd_staff_10m)
    # For now, convert them to only return the time
    hd_xaxis_labels = [x.split('_')[1] for x in hd_xaxis_labels]

    return (hd_xaxis_labels, hd_staff_10m_list, hd_employee_10m_list)


def hd_df_to_staff_employee_1min(in_df):
    ''' Convert a (full) pandas dataframe in the Cass SV2 schema
    format to two dataframes consisting of employee and staff counts
    resampled to 1 min intervals. The counts in each 1 min interval represent
    number of second-employee or second-staff presence in that interval

    Argument:
        in_df: A pandas dataframe in the SV2 schema format (reproduced below)

     Returns:
         Two dataframes:
            - hd_staff_1m: Counts of number of staff present every second
                          in that 1m interval
            - hd_employee_1m: Counts of number of employee present every
                          second in that 1m interval

     SV2 Format: detect_time100, detect_time_hr, confidence, found,
                 stream_group_name, stream_name, msg_format_version,
                 startX, endX, startY, endY
    '''

    # Filter the input dataframe into helpdesk and archimedes dataframes
    hd_person_df = in_df[(in_df.found == 'person') & (in_df.stream_name ==
                                                      HELPDESK_STREAM_NAME)]

    # Create a datetime object column in local timezone. This column will
    # later be used as index
    hd_person_df['local_detect_time'] = epoch_to_localtz(hd_person_df
                                                         .detect_time100/100,
                                                         PACIFIC_TZ)

    # Create a column in the helpdesk df that also contains the center point
    # of the detected object
    hd_person_df['center_pointX'] = (hd_person_df.endx - hd_person_df.startx)/2
    hd_person_df['center_pointY'] = (hd_person_df.endy - hd_person_df.starty)/2

    # Now split them into employee and staff df
    hd_employee_df = hd_person_df[hd_person_df.center_pointX >
                                  SPLIT_HORIZ_POINT]
    hd_staff_df = hd_person_df[hd_person_df.center_pointX <
                               SPLIT_HORIZ_POINT]

    # Re-index the DataFrames so the detect time is the index.
    # This is needed to resample the df
    hd_employee_df.set_index('local_detect_time', inplace=True)
    hd_staff_df.set_index('local_detect_time', inplace=True)

    # Resample everything to 1sec resolution
    hd_staff_1sec = hd_staff_df.resample('1S').sum()
    hd_employee_1sec = hd_employee_df.resample('1S').sum()

    # This is simply setting the column 'staff/employee_present' to a 1
    # if there were any numebr of persons present in that second.
    # This will make the count unit as (employee|staff)-seconds.
    hd_staff_1sec['staff_present'] =        \
        np.where(hd_staff_1sec['confidence'] > 0, 1, 0)
    hd_employee_1sec['employee_present'] =  \
        np.where(hd_employee_1sec['confidence'] > 0, 1, 0)

    # Resample the entire thing by 1 min, but this time summing the columns.
    hd_staff_1m = hd_staff_1sec.resample('1T').sum()
    hd_employee_1m = hd_employee_1sec.resample('1T').sum()

    # Select only the staff and employee present columns. This is all that
    # is needed for current helpdesk use cases
    hd_staff_1m = hd_staff_1m['staff_present']
    hd_employee_1m = hd_employee_1m['employee_present']

    return hd_staff_1m, hd_employee_1m


# ----- TBD: This is a useful general function. Mbbe move to common utils ----
def get_time_range_from_dfs(df_list):
    ''' Return the time range between the earliest timestamp and
        latest timestamp among dataframes '''

    # Had to convert below to local tz since the df time index is in local tz
    # Then had to subtract 1 day from the max timestamp otherwise converting
    # to local tz gave a outofbounds error
    latest_time = pd.Timestamp.min.tz_localize(PACIFIC_TZ)
    earliest_time = (pd.Timestamp.max-timedelta(days=1)).tz_localize(PACIFIC_TZ)

    for df in df_list:

        earliest_time =     \
            earliest_time if earliest_time < df.index[0] else df.index[0]
        latest_time =     \
            latest_time if latest_time > df.index[-1] else df.index[-1]

    time_delta = latest_time - earliest_time
    return time_delta


# -------------TBD: Move the resample map etc to config files ------------
# Using named tuple for comparing time delta, less than, greater than
tr_resample_map = namedtuple('td_resample_map',
                             ['lower_limit', 'upper_limit', 'resample_rate'])
hd_time_range_to_resample_rate = [
    # if df time range is > 1 min and < 1 hour, resample at 10 min
    tr_resample_map(timedelta(minutes=1), timedelta(hours=2), '10T'),
    tr_resample_map(timedelta(hours=2),   timedelta(hours=4), '20T'),
    tr_resample_map(timedelta(hours=4),   timedelta(hours=8), '40T'),
    tr_resample_map(timedelta(hours=8),   timedelta(hours=12), '1H'),
    tr_resample_map(timedelta(hours=12),   timedelta(hours=24), '2H'),
]


def hd_timerange_to_resample_rate(time_range):
    ''' Return a resample rate based on the argument time_range '''
    for tr in hd_time_range_to_resample_rate:
        if tr.lower_limit < time_range < tr.upper_limit:
            return tr.resample_rate
    # If time_range is not within any specified range above, log an error
    # and return something like 10 days in the hope that it will be large enough
    # to have a decent graph.
    logging.error('Time range: {} does not fit into any of the ranges '
                  'specified in the resample rate list. Returning default '
                  ' of 10 days'.format(time_range))
    return '1H'


def hd_1mdf_to_chart_items(hd_staff_1m, hd_employee_1m):
    ''' This takes staff and employee dataframes sampled at 1m frequency
        and returns a set of lists appropraite for charting

        Arguments:
            - hd_staff_1m, hd_employee_1m: Staff and employee dataframes
                resampled to 1 min intervals

        Returns:
            - labels: List of labels for each bar of bar plot
            - staff_counts: List of staff-seconds counts
            - employee_counts: List of employee-seconds counts

    '''

    # Get the time range from the dfs (that is the time between the
    # earliest and latest entries in the dataframes)
    time_range = get_time_range_from_dfs([hd_staff_1m, hd_employee_1m])
    # From the timerange, figure out the re-sample rate needed for a
    # decent display on the UI
    resample_rate = hd_timerange_to_resample_rate(time_range)
    # Now resample according to returned resample_rate
    hd_staff_resampled = hd_staff_1m.resample(resample_rate).sum()
    hd_employee_resampled = hd_employee_1m.resample(resample_rate).sum()

    # Get the staff/employee counts
    hd_staff_counts = hd_staff_resampled.values
    hd_employee_counts = hd_employee_resampled.values
    # Get the values of the index for the x-axis labels (the time stamps)
    hd_xaxis_labels = [datetime_to_localtz_hr(x)
                       for x in hd_staff_resampled.index]
    # For now, convert them to only return the time
    # The timestamp will be of the format: '2018-11-19_08:00:00'
    # The labels will be of the format: 08:00 after all below transformations
    hd_xaxis_labels = [x.split('_')[1] for x in hd_xaxis_labels]
    hd_xaxis_labels = [':'.join(t.split(':')[:-1]) for t in hd_xaxis_labels]

    return (hd_xaxis_labels, hd_staff_counts, hd_employee_counts)


def get_chart_params(start_time, end_time, app='helpdesk'):
    ''' Get the various params needed for drawing a chart '''

    query_df = query_cass.cass_query(start_time, end_time)
    # query_df.to_pickle('test1.pkl')
    # query_df = pd.read_pickle('test1.pkl')

    # Get the returned full df split to staff and employee df and resampled
    # to 1m resolution
    hd_staff_1m, hd_employee_1m = hd_df_to_staff_employee_1min(query_df)

    labels, staff_counts, employee_counts =     \
        hd_1mdf_to_chart_items(hd_staff_1m, hd_employee_1m)

    return labels, staff_counts, employee_counts


if __name__ == '__main__':
    # Used for testing

    START_TIME = '2018-12-17_00:00:00'
    END_TIME = '2018-12-17_23:00:00'

    start_time, end_time = selecttime_to_start_end('last_day', PACIFIC_TZ)
    print(start_time)
    print(end_time)
    sys.exit()
    labels, staff_counts, employee_counts = get_chart_params(START_TIME,
                                                             END_TIME)
    print(f'Staff: {staff_counts}')
    print(f'Employee: {employee_counts}')
    print(f'Labels: {labels}')
