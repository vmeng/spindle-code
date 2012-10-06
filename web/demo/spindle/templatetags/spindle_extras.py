
from django import template

register = template.Library()

def duration(secs):
    secs = int(secs)

    minutes = secs/60
    secs = secs - 60*minutes

    hours = minutes/60
    minutes = minutes - 60*hours

    return "{:02d}:{:02d}:{:02d}".format(hours, minutes, secs)
    

def percent_complete(fraction):
    if fraction is None:
        return ""
    return "{}%".format(int(100 * fraction))

register.filter('duration', duration)
register.filter('percent_complete', percent_complete)
