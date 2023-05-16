from .base import *


from pathlib import Path


#############################################################
# Critical settings - DEBUG (변경 필요)
# 개발용으로만 DEBUG = True
#############################################################
DEBUG = True
SECRET_KEY = "django-insecure-5o)oh8%m&z3*q91b9m&#4r!hzxd0a3_q#_vm8hrsx(n3mtq35e"

ALLOWED_HOSTS = [
    "ts2-bot.gaolious.com",
]


# Application definition

INSTALLED_APPS = list(set(INSTALLED_APPS + DJANGO_APPS + DATA_APPS + ADMIN_APPS))

ROOT_URLCONF = "conf.urls.local"
