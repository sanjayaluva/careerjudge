from . import models
from datetime import date, timedelta

from django.contrib.auth import get_user_model
User = get_user_model()

from django_cron import CronJobBase, Schedule


"""
Define Cron job for counselling notifications        
"""        
class CronJobs(CronJobBase):
    RUN_EVERY_MINS = 1 # every 2 hours

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'counselling.cron.CronJobs'    # a unique code

    def do(self):
        availability_checker()

"""
Check all counsellors for minimum availability timeslots, ie: atleast 7 days timeslots. otherwise notify users.
"""
def availability_checker():
    counsellors = User.objects.filter(role=User.COUNSELLOR)
    
    startdate = date.today()
    enddate = startdate + timedelta(days=21)

    for counsellor in counsellors:
        avail = models.Availability.objects.filter(counsellor=counsellor, date__range=[startdate, enddate])
        recordCount = avail.count()
        if (recordCount < 7):
            # send notifications
            pass
