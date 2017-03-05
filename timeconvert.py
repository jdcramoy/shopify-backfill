from __future__ import division
import time
from datetime import datetime, timedelta
import iso8601

TEST_DATE = '2013-01-01T00:00:00-04:00'

def convert_timestamp(value):
    return time.mktime(datetime.strptime(value, "%Y-%m-%d").timetuple())

# convert_timestamp('')

# iso8601.parse_date("2007-01-25T12:00:00Z")

print iso8601.parse_date('2014-04-25T16:15:47-04:00')



# def totimestamp(dt, epoch=datetime(1970,1,1)):
#     td = dt - epoch
#     # return td.total_seconds()
#     return (td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6

# print totimestamp(iso8601.parse_date('2014-04-25T16:15:47-04:00'))

dt = iso8601.parse_date('2014-04-25T16:15:47-04:00')

assert dt.tzinfo is not None and dt.utcoffset() is not None
utc_naive  = dt.replace(tzinfo=None) - dt.utcoffset()
timestamp = (utc_naive - datetime(1970, 1, 1)).total_seconds()

print timestamp
