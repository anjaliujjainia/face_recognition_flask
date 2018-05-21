from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from crontab import CronTab
import os

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cair_project.settings")
#init cron
cron = CronTab(user=True)

python_path = '~/DjangoProject/venv/bin/python'
folder = '~/DjangoProject/face_recognition_flask/'
file_name1 = folder + 'lazy_delete_people.py'
file_name2 = 'update_similar_people.py'

#add new cron job
job = cron.new(command= python_path + ' ' + file_name1, comment='delete_lazy_people')
# run at the end of the day
job.every().day()


#add new cron job
# job2 = cron.new(command= python_path + ' ' + file_name2, comment='update_similar_people')
# run every hour
# job2.hour.every(1)

cron.write()
