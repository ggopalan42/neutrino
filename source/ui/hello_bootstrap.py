import traceback
import sys

from flask import Flask, render_template, redirect, url_for
# from flask import Markup
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, DateField, DateTimeField
from wtforms.validators import DataRequired


# Local imports
import query_cass
import chart_utils as cu


# Constants
RADIO_FIELDS = [('last_week', ' Last Week'),
                ('last_7days', ' Last 7 Days'),
                ('last_day', ' Last Day'),
                ('last_24hrs', ' Last 24 Hours'),
                ('custom_date', ' Choose Custom Date Range Below'), ]

# Charting constants
NUM_BUCKETS = 10

DEFAULT_START_TIME = '2018-12-17_08:00:00'
DEFAULT_END_TIME = '2018-12-17_09:00:00'

PACIFIC_TZ = 'US/Pacific'

application = Flask(__name__)

# Hard config secret key. I know, I know Mr. Judgemental. A better
# implementation is needed. But this is needed for flask-wtf
application.config['SECRET_KEY'] = 'ThisNeedsToChange'


bootstrap = Bootstrap(application)


# Define a date range class. This is so it can be used in
# rendering the date range form.
class DaterangeForm(FlaskForm):
    radio_button = RadioField('Please Select', choices=RADIO_FIELDS)
    start_date = StringField('Start Date (YYYY-MM-DD_hh:mm:ss (in PST Only))')
    end_date = StringField('End Date (YYYY-MM-DD_hh:mm:ss (in PST Only))')
    submit = SubmitField('Submit')


@application.route('/')
def index():
    return render_template('index.html')


@application.route('/about')
def about():
    return render_template('about.html')

# The /chart route below is simply an example of how to use Chart.js


@application.route('/chart')
def chart():
    legend = 'Monthly Data'
    labels = ["January", "February", "March",
              "April", "May", "June", "July", "August"]
    values = [10, 9, 8, 7, 6, 4, 7, 8]
    return render_template('chart.html', values=values, labels=labels,
                           legend=legend)


@application.route('/helpdesk', methods=['GET', 'POST'])
def helpdesk():
    # Instantiate the DateRange class
    form = DaterangeForm()

    # Need to get some default values into the bar chart plotting vars
    start_time, end_time = DEFAULT_START_TIME, DEFAULT_END_TIME
    (labels, staff_counts, employee_counts) =     \
        cu.get_chart_params(start_time, end_time)
    # date_range_str needs to be initialized to something before render
    display_message = 'Please choose an option from below'
    optional_message = ('Please select an option from above. '
                        'Default Start/End times being used')
    if form.validate_on_submit():
        radio_button = form.radio_button.data
        optional_message = None
        if radio_button == 'custom_date':
            start_time = form.start_date.data
            end_time = form.end_date.data

            # Validate user inputs: start and end times
            msg = cu.validate_start_end(start_time, end_time)
            if msg:
                return render_template('date_format_error.html', message=msg)
            msg = cu.validate_time_format(end_time)
            if msg:
                return render_template('date_format_error.html', message=msg)

            (labels, staff_counts, employee_counts) =     \
                cu.get_chart_params(start_time, end_time)
        else:
            start_time, end_time = cu.selecttime_to_start_end(radio_button,
                                                              PACIFIC_TZ)
            (labels, staff_counts, employee_counts) =     \
                cu.get_chart_params(start_time, end_time)
            display_message = ('Showing for time range: {}'
                               .format(radio_button))
    counts = zip(staff_counts, employee_counts)
    count_max = max(max(staff_counts), max(employee_counts))
    scale_steps = 12
    print(labels)

    # Add day to start and end times
    st_time_day = '{} ({})'.format(start_time, cu.get_day_from_date(start_time))
    end_time_day = '{} ({})'.format(end_time, cu.get_day_from_date(end_time))

    return render_template('helpdesk.html', form=form,
                           display_message=display_message,
                           optional_message=optional_message,
                           staff_counts=staff_counts,
                           employee_counts=employee_counts, labels=labels,
                           count_max=count_max, scale_steps=scale_steps,
                           start_time=st_time_day, end_time=end_time_day,)


@application.route('/room_occ')
def room_occ():
    return render_template('room_occ.html')


# Error handling
@application.errorhandler(404)
def page_not_found(e):
    return render_template('error_404.html'), 404


@application.errorhandler(500)
def internal_server_error(e):
    return render_template('error_500.html'), 500


@application.errorhandler(Exception)
def exception_handler(e):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    err = str(e)
    tb = traceback.format_exception(exc_type, exc_value, exc_traceback)
    # tb = ''.join(tb_list)
    return render_template('hd_exception_handler.html', err=err, tb=tb), 500
