from pathlib import Path

ROOT_PATH = Path(__file__).parents[2]

ROOT_URLCONF = 'health_data_project.urls'

WSGI_APPLICATION = 'health_data_project.wsgi.application'


###########################################################
# Installed applications

INSTALLED_APPS = [
    'hda_privileged',
    'hda_public',
    'app_api',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]


###########################################################
# Installed middleware

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
# Template settings

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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
# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


###########################################################
# Auth module
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth

# The URL the login_required decorator will use to log in users when the request a protected page
LOGIN_URL = 'priv:login'

# The page the login page will redirect a successfully authenticated user to, if they didn't ask for somewhere in particular
LOGIN_REDIRECT_URL = 'priv:dashboard1'


STATIC_URL = '/static/'

STATICFILES_DIRS = [str(ROOT_PATH / 'static')]

MEDIA_URL = '/media/'
