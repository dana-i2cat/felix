from core import log
from datetime import datetime
#from dateutil import parser as dateparser
import dateutil
import re

logger = log.getLogger("coreutils.dates")

# ---- Date utils ----

RFC3339_FORMAT_STRING = "%Y-%m-%d %H:%M:%S.%fZ"

def rfc3339_to_datetime(date):
    """
    Returns a datetime object from an input string formatted
    according to RFC3339.

    Ref: https://github.com/fp7-ofelia/ocf/blob/ofelia.development/core/
         lib/am/ambase/src/geni/v3/handler/handler.py#L321-L332
    """
    try:
        date_form = re.sub(r'[\+|\.].+', "", date)
        formatted_date = datetime.strptime(
            date_form.replace("T", " ").
            replace("Z", ""), "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        formatted_date = date
    logger.debug("Converted datetime object (%s): %s" %
                 (type(formatted_date), formatted_date))
    return formatted_date

def datetime_to_rfc3339(date):
    """
    Returns a string that is formatted according to RFC3339.

    Ref: OMNI code at src/gcf/geni/am/am3.py
    """
#    try:
#        formatted_date = date.replace(tzinfo=dateutil.tz.tzutc()).\
#            strftime("%Y-%m-%d %H:%M:%S").replace(" ", "T")+"Z"
#    except:
#        formatted_date = date
#    return formatted_date
    return rfc3339format(date)

def naiveUTC(dt):
    """
    Converts dt to a naive datetime in UTC.

    if 'dt' has a timezone then
    convert to UTC
    strip off timezone (make it "naive" in Python parlance)
    """
    if dt.tzinfo:
        tz_utc = dateutil.tz.tzutc()
        dt = dt.astimezone(tz_utc)
        dt = dt.replace(tzinfo=None)
    return dt

def rfc3339format(dt):
    """
    Return a string representing the given datetime in rfc3339 format.
    """
    # Add UTC TZ, to have an RFC3339 compliant datetime, per the AM API
    naiveUTC(dt)
    time_with_tz = dt.replace(tzinfo=dateutil.tz.tzutc())
    d1 = time_with_tz.isoformat()
    return time_with_tz.isoformat()

def is_date(dt):
    if isinstance(dt, datetime):
        return True
    return False

