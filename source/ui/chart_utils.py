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
HD_XLABEL_TIME_FORMAT = '%m-%d_%H:%M (%a)'

HELPDESK_STREAM_NAME = 'bldg_d_f4_helpdesk'

# --------- Not sure if following needs to go to config file or not -------
# For now hardcode local TZ to be US/Pacific
# LOCAL_TZ = 'US/Pacific'
PACIFIC_TZ = 'US/Pacific'


# TBD: Time utilities. Perhaps a good set to move to a separate utils file
def get_day_from_date(date_time_str, format=STANDARD_TIMEFORMAT_HR,
                      day_type='abbreviated'):
    ''' Returns day from the provided date_time string
        Arguments:
        ---------
          - date_time_str: Date and/or time string
          - format: format of date_time_str
          - day_type: "abbreviated" (default) returns daytype: Mon, Tue, etc.
                      Anything else returns Monday, Tuesday, etc.

        Returns:
          - day: A string that is the day of the date_time_str
    '''
    date_time_do = datetime.strptime(date_time_str, format)
    if day_type == 'abbreviated':
        return date_time_do.strftime('%a')
    else:
        return date_time_do.strftime('%A')


# TBD: Time utilities. Perhaps a good set to move to a separate utils file
def validate_time_format(date_string, date_format=STANDARD_TIMEFORMAT_HR):
    ''' Validate that the entered date/time is in the expected format
    Arguments:
        - Date string to be validated
        - The date format it needs to be validated to (optional)

    Returns:
        - None: If the format is OK
        - An error string that can be printed out or logged if
          format is incorrect
    '''
    ret_message = None
    try:
        datetime.strptime(date_string, date_format)
    except ValueError:
        ret_message = ('Time data "{}" is not in expected format:   \
                       YYYY-MM-DD_hh:mm:ss'.format(date_string))
    # Catch all other exception
    except Exception as e:
        ret_message = 'Unexpected Exception. Reason: {}'.format(e)
    return ret_message


# TBD: Time utilities. Perhaps a good set to move to a separate utils file
def validate_start_end(start, end, date_format=STANDARD_TIMEFORMAT_HR):
    ''' Validate the format and chronology of start and end times

        This function will:
            1. Validate that "start" and "end" conforms to the
               timeformat specified by date_format
            2. That start indeed is before end

    Arguments:
    ---------
        - start/end: start/end times string specified in date_format format
        - date_format: format string specyfing date/time format

    Returns:
        - None: If the format is OK
        - An error string that can be printed out or logged if
          format is incorrect
    '''

    # Validate start time
    ret_message = validate_time_format(start, date_format)
    if ret_message:
        return '{} {}'.format('Start', ret_message)
    # Validate end time
    ret_message = validate_time_format(end, date_format)
    if ret_message:
        return '{} {}'.format('End', ret_message)

    # Now that format is validated, check that start is indeed chronologically
    # before end
    start_do = datetime.strptime(start, date_format)
    end_do = datetime.strptime(end, date_format)
    if start_do > end_do:
        ret_message = 'Start Time: {} is after End Time: {}'.format(start, end)
    else:
        ret_message = None

    return ret_message


# TBD: Time utilities. Perhaps a good set to move to a separate utils file
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
    start_time = time_now_minus_24hrs.strftime(STANDARD_TIMEFORMAT_HR)
    end_time = time_now.strftime(STANDARD_TIMEFORMAT_HR)
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


# TBD: Time utilities. Perhaps a good set to move to a separate utils file
def dt_get_last_7days(time_zone):
    ''' Determine the start/end times for last 7 days.

    Arguments: None

    Returns:
        start_time = Time now minus 7 days in standard timeformat
        end_time = Current minute  in standard timeformat

    '''
    time_now = datetime.now()
    # Round the the time to nearest minute - this is the resolution supported
    time_now = time_now - timedelta(seconds=time_now.second)
    time_now_minus_7days = time_now - timedelta(days=7)
    # Convert start and end times to string
    start_time = time_now_minus_7days.strftime(STANDARD_TIMEFORMAT_HR)
    end_time = time_now.strftime(STANDARD_TIMEFORMAT_HR)
    return start_time, end_time


# Time utilities. Perhaps a good set to move to a separate utils file
def dt_get_last_week(time_zone):
    ''' Determine the start/end times of previous week.

    Arguments: time_zone - unused for now

    Returns:
        start_time = Start time beginning of last week
        end_time = End time of last week

    '''
    # Get time now and compute last week time
    time_now = datetime.now()
    tmp = time_now - timedelta(time_now.weekday())
    # Get the start and end of yesterday times
    this_week_start = tmp - timedelta(hours=tmp.hour, minutes=tmp.minute,
                                      seconds=tmp.second,
                                      microseconds=tmp.microsecond)
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end = last_week_start + timedelta(days=4, hours=23,
                                                minutes=59)   # Only weekdays

    # Format them as strings
    start_time = last_week_start.strftime(STANDARD_TIMEFORMAT_HR)
    end_time = last_week_end.strftime(STANDARD_TIMEFORMAT_HR)
    return start_time, end_time


def hd_reformat_xlabels(xlabels, in_format=STANDARD_TIMEFORMAT_HR,
                        out_format=HD_XLABEL_TIME_FORMAT):
    ''' Reformat xlabels to desired format to be shown on helpdesk chart
        Arguments:
        ---------
          - xlabels: list of date/time strings in "in_format" format
          - in_format: Date/time format of each element in "xlabels"
          - out_format: Format to convert each element of "xlabels" to
    '''
    xlabels_do = [datetime.strptime(x, in_format) for x in xlabels]
    out_xlabels = [d.strftime(out_format) for d in xlabels_do]
    return out_xlabels


SELECTIME_FUNCTION_MAP = {
    'last_24hrs': dt_get_last_24hrs,
    'last_day': dt_get_yesterday,
    'last_7days': dt_get_last_7days,
    'last_week': dt_get_last_week,
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
    return pd.to_datetime(df_epoch / 1e6, unit='s').dt.tz_localize('UTC')  \
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
                                                         .detect_time100 / 100,
                                                         PACIFIC_TZ)

    # Create a column in the helpdesk df that also contains the center point
    # of the detected object
    hd_person_df['center_pointX'] = (
        hd_person_df.endx - hd_person_df.startx) / 2
    hd_person_df['center_pointY'] = (
        hd_person_df.endy - hd_person_df.starty) / 2

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
                                                         .detect_time100 / 100,
                                                         PACIFIC_TZ)

    # Create a column in the helpdesk df that also contains the center point
    # of the detected object
    hd_person_df['center_pointX'] = (
        hd_person_df.endx - hd_person_df.startx) / 2
    hd_person_df['center_pointY'] = (
        hd_person_df.endy - hd_person_df.starty) / 2

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
    earliest_time = (pd.Timestamp.max - timedelta(days=1))    \
        .tz_localize(PACIFIC_TZ)

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
    tr_resample_map(timedelta(hours=2), timedelta(hours=4), '20T'),
    tr_resample_map(timedelta(hours=4), timedelta(hours=8), '40T'),
    tr_resample_map(timedelta(hours=8), timedelta(hours=12), '1H'),
    tr_resample_map(timedelta(hours=12), timedelta(hours=24), '2H'),
    tr_resample_map(timedelta(hours=24), timedelta(hours=48), '4H'),
    tr_resample_map(timedelta(days=4), timedelta(days=8), '8H'),
]


# ----- TBD: This is a useful general function. Mbbe move to common utils ----
def split_date_range(start_time, end_time, period):
    ''' Split the given date range (from start_time to end_time) into
        equal periods specified by period

        Parameters:
        -----------
        start_time: string in the format YYYY-MM-DD_hh:mm:ss format
        end_time: string in the format YYYY-MM-DD_hh:mm:ss format
        period: The period to split the start/emd times. For eg: '1D' will
                split the start to end times to a list in which each element
                will represent start/end times inside of a single day

        Returns:
        -------
        start_end_list: Is a list of named tuples in which each element
                        represents the start and end times of he requested
                        period

    '''

    # There probably is a cleverer way to do this, but below is best I have
    # The sub_xxxx below here refers to sub-second/min/hour etc.
    sub_start_end = namedtuple('sub_start_end', 'sub_start_time sub_end_time')
    start = datetime.strptime(start_time, STANDARD_TIMEFORMAT_HR)
    end = datetime.strptime(end_time, STANDARD_TIMEFORMAT_HR)

    if period == '1D':    # Only period implemented for now
        delta = (end - start).days
        # If start & end time are on same day, there is nothing to do.
        # Just return the parameters start_time and end_time as is
        if delta == 0:
            start_end_list = [sub_start_end(start_time, end_time)]
        # If not, loop over the number of days between start and end
        else:
            start_end_list = []
            for i in range(delta):
                if i == 0:  # This is the first day
                    # Simply set the start time to start_time
                    tmp_start = start.strftime(STANDARD_TIMEFORMAT_HR)
                    # So end time will be the last second of start_time
                    # The below .combine does this by default (see docs)
                    tmp_end = datetime.combine(start, datetime.max.time()) \
                        .strftime(STANDARD_TIMEFORMAT_HR)
                    tmp_start_end = sub_start_end(tmp_start, tmp_end)
                    start_end_list.append(tmp_start_end)

                if i == delta - 1:  # This is the last day
                    # Start time will be the beginning (midnight) of end_time
                    # The below .combine does this by default (see docs)
                    tmp_start = datetime.combine(end, datetime.min.time()) \
                        .strftime(STANDARD_TIMEFORMAT_HR)
                    # Simply set the end time to end_time
                    tmp_end = end.strftime(STANDARD_TIMEFORMAT_HR)
                    tmp_start_end = sub_start_end(tmp_start, tmp_end)
                    start_end_list.append(tmp_start_end)

                if i > 0 and i < delta:  # For the intervening days
                    # Need to get the day.
                    # So add number of days + i to start_time
                    tmp_day = start + timedelta(days=i)
                    tmp_start = datetime.combine(tmp_day, datetime.min.time()) \
                        .strftime(STANDARD_TIMEFORMAT_HR)
                    tmp_end = datetime.combine(tmp_day, datetime.max.time()) \
                        .strftime(STANDARD_TIMEFORMAT_HR)
                    tmp_start_end = sub_start_end(tmp_start, tmp_end)
                    start_end_list.append(tmp_start_end)

    else:
        # Return None as an indication of not implemented error
        # In next version, please log error as well
        return None

    # Again, perhaps sorted is not the best way to do this.
    return sorted(start_end_list)


def hd_timerange_to_resample_rate(time_range):
    ''' Return a resample rate based on the argument time_range '''
    for tr in hd_time_range_to_resample_rate:
        if tr.lower_limit < time_range < tr.upper_limit:
            return tr.resample_rate
    # If time_range is not within any specified range above, log an error
    # and return something like 10 days in the hope that it will be
    # large enough to have a decent graph.
    logging.error('Time range: {} does not fit into any of the ranges '
                  'specified in the resample rate list. Returning default '
                  ' of 1 day'.format(time_range))
    return '1D'


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
    hx_xlabels_reformated = hd_reformat_xlabels(hd_xaxis_labels)
    # For now, convert them to only return the time
    # The timestamp will be of the format: '2018-11-19_08:00:00'
    # The labels will be of the format: 08:00 after all below transformations
    hd_xaxis_labels = [x.split('_')[1] for x in hd_xaxis_labels]
    hd_xaxis_labels = [':'.join(t.split(':')[:-1]) for t in hd_xaxis_labels]

    return (hx_xlabels_reformated, hd_staff_counts, hd_employee_counts)


def get_chart_params(start_time, end_time, app='helpdesk'):
    ''' Get the various params needed for drawing a chart '''

    # cass_query currently only works for date range only within one day
    # So split the start and end times to a list of tuples with start and
    # end times so the query can be iterated over if the date range is
    # greater than 24 hrs
    start_end_list = split_date_range(start_time, end_time, period='1D')

    query_df = query_cass.make_empty_dataframe()
    for start_end in start_end_list:
        tmp_query_df = query_cass.cass_query(start_end.sub_start_time,
                                             start_end.sub_end_time)
        # If the returned df is empty (data does not exists for example)
        # simple ignore it.
        # TBD: I'm handling this totally wrong, I know. Need to somehow
        # indicate missing data. But . . . moving on . . .
        if len(tmp_query_df) > 0:
            query_df = query_df.append(tmp_query_df)

    # Now check if there is no data at all! Its possible based on the
    # query. If there ino data at all, then return this state in the
    # best possible manner currently.
    # TBD: This can improved
    if len(query_df) == 0:
        labels = ['No Data!']
        staff_counts = employee_counts = [0]
    else:
        # Get the returned full df split to staff and employee df and resampled
        # to 1m resolution
        hd_staff_1m, hd_employee_1m = hd_df_to_staff_employee_1min(query_df)

        labels, staff_counts, employee_counts =     \
            hd_1mdf_to_chart_items(hd_staff_1m, hd_employee_1m)

    return labels, staff_counts, employee_counts


if __name__ == '__main__':
    # Used for testing

    START_TIME = '2019-01-10_01:00:00'
    END_TIME = '2019-01-10_23:00:00'
    '''
    labels, staff_counts, employee_counts = get_chart_params(START_TIME,
                                                             END_TIME)
    print(f'Staff: {staff_counts}')
    print(f'Employee: {employee_counts}')
    print(f'Labels: {labels}')
    '''
    print(dt_get_last_7days(PACIFIC_TZ))
    '''
    day = get_day_from_date(START_TIME, STANDARD_TIMEFORMAT_HR, 'long')
    print(day)
    '''
