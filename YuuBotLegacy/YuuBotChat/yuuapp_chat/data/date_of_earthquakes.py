import pytz
from datetime import datetime

def JSTSorter(the_time):
    dt = datetime.strptime(the_time, '%Y-%m-%d %H:%M:%S')
    timezone = pytz.timezone('Asia/Tokyo')
    jst = timezone.localize(dt)
    return jst.strftime('%Y-%m-%d %H:%M:%S')

def extract_date(item):
    date_string = item[0]
    return JSTSorter(date_string)
