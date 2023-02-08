"""
Django settings for ts project.

Generated by 'django-admin startproject' using Django 4.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path

###########################################################
# SITE_PATH   = /home/ubuntu/sites/ts2-bot.gaolious.com/
# VIRTUAL ENV = /home/ubuntu/sites/ts2-bot.gaolious.com/virtualenv/
# SOURCE_PATH = /home/ubuntu/sites/ts2-bot.gaolious.com/source/
# DJANGO_PATH = /home/ubuntu/sites/ts2-bot.gaolious.com/source/ts2-bot
# __file__   = /home/ubuntu/sites/ts2-bot.gaolious.com/source/ts2-bot/conf/settings/base.py
###########################################################

# Build paths inside the project like this: BASE_DIR / 'subdir'.
import pytz as pytz

DJANGO_PATH = Path(__file__).resolve().parent.parent.parent
SOURCE_PATH = DJANGO_PATH.parent
SITE_PATH = SOURCE_PATH.parent
CACHE_PATH = SITE_PATH / 'cache'

###########################################################
# gunicorn Header 의 version 정보 삭제
###########################################################

try:
    # Nginx <--> Gunicorn <--> WSGI/ASGI <--> Django
    # 와 같은 구조에서만 동작. 그 외(개발환경) 에서는 Exception.
    from gunicorn.http import wsgi


    class Response(wsgi.Response):
        def __init__(self, req, sock, cfg):
            super(Response, self).__init__(req, sock, cfg)
            self.version = 'ts'

    wsgi.Response = Response
except:
    pass


###########################################################
# Critical settings - SECRET_KEY (변경 필요) generate :
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/
# python3 -c 'import random; import string; print ("".join([random.SystemRandom().choice(string.digits + string.ascii_letters + ".!@`~|[]{})(*^$#:?<>") for i in range(50)]))'
###########################################################
SECRET_KEY = ''

#############################################################
# Critical settings - DEBUG (변경 필요)
# 개발용으로만 DEBUG = True
#############################################################

DEBUG = False


###########################################################
# Critical settings - ALLOWED_HOSTS (변경 필요)
# bind될 주소를 리스트 형태로 입력.
# https://docs.djangoproject.com/en/4.1/ref/settings/#allowed-hosts
###########################################################

ALLOWED_HOSTS = []


#############################################################
# Critical settings - Logging
# https://docs.djangoproject.com/en/4.1/ref/settings/#std:setting-LOGGING
#############################################################

LOG_PATH = SOURCE_PATH / 'log'
LOG_PATH.mkdir(0o755, True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s] [%(asctime)s] %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
        'simple': {
            'format': '[%(asctime)s] %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
        'json': {
            'format': '%(levelname)s %(asctime)s %(message)s',
        },
    },
    'handlers': {
        # RotatingFilterHandler 절대 사용 금지. 버그 존재.
        # FileHandler + logrotate 하는 것을 권장.
        'default': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_PATH / 'default.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'default': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False,
        },
        # 'django': {
        #     'handlers': ['default'],
        #     'level': 'INFO',
        #     'propagate': False,
        # },
        # 'error': {
        #     'handlers': ['error'],
        #     'level': 'INFO',
        #     'propagate': False,
        # }
    },
}


#############################################################
# Installed Apps
# https://docs.djangoproject.com/en/4.1/ref/settings/#installed-apps
#############################################################
DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django_extensions',
]

DATA_APPS = [
    'core',
    'app_root.users',
    'app_root.commands',
    'app_root.servers',
    'app_root.players',
    'app_root.strategies',
]

ADMIN_APPS = [
]

API_APPS = [
]
INSTALLED_APPS = DJANGO_APPS + DATA_APPS


#############################################################
# Critical settings - CACHES (변경 필요)
# https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-CACHES
#############################################################

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    },
}


###########################################################
# MIDDLEWARE
###########################################################
#   flow :
#       Client Request
#           -> CGI(WSGI/ASGI)
#               -> dispatch
#                   -> MIDDLEWARE(process_request)
#                   -> user code (get, post, delete, put, ...... )
#                   -> MIDDLEWARE(process_response)
###########################################################

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

###########################################################
# URL route
###########################################################

ROOT_URLCONF = 'conf.urls.local'


#############################################################
# Critical settings - Templates
# https://docs.djangoproject.com/en/4.1/ref/settings/#std:setting-TEMPLATES
#############################################################
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [DJANGO_PATH / 'templates']
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


###########################################################
# Gateway Interface. (WSGI / ASGI)
###########################################################

WSGI_APPLICATION = 'ts.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DJANGO_PATH / 'db.sqlite3',
    },
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


###########################################################
# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/
###########################################################

LOCALE_PATHS = (
    (DJANGO_PATH / 'locales'),
)
LANGUAGES = [
    ('ko', 'Korean'),
    ('en', 'English'),
]

LANGUAGE_CODE = 'ko-kr'
# TIME_ZONE = 'Asia/Seoul'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = False
USE_TZ = True
KST = pytz.timezone('Asia/Seoul')


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_USER_MODEL = 'users.User'

###########################################################
# Client Information
###########################################################
CLIENT_INFORMATION_STORE = 'google_play'
CLIENT_INFORMATION_VERSION = '2.7.0.4123'
CLIENT_INFORMATION_LANGUAGE = 'ko'

WHISTLE_INTERVAL_SECOND = 4 * 60