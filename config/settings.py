from pathlib import Path
from datetime import timedelta
import os
import sys

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
env.read_env(BASE_DIR / ".env")

# =========================================================
# MODO DE EJECUCIÓN
#   "web"        → servidores / hosting / laboratorios grandes
#   "escritorio" → PC local / laboratorios pequeños (sin Docker)
# =========================================================
MODO = os.environ.get("LABCLIN_MODO", "web")
ESCRITORIO = MODO == "escritorio"

if ESCRITORIO:
    DATA_DIR = Path(os.environ.get("LABCLIN_BASE", BASE_DIR)) / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
else:
    DATA_DIR = BASE_DIR / "data"

DEBUG = env.bool("DJANGO_DEBUG", default=False)

# Clave secreta: en escritorio se genera y guarda una vez en data/
SECRET_KEY = env.str("DJANGO_SECRET_KEY", default=None)
if not SECRET_KEY:
    if ESCRITORIO:
        key_file = DATA_DIR / "secret.key"
        if key_file.exists():
            SECRET_KEY = key_file.read_text().strip()
        else:
            from django.utils.crypto import get_random_string

            SECRET_KEY = get_random_string(64)
            key_file.write_text(SECRET_KEY)
    elif DEBUG:
        SECRET_KEY = "django-insecure-dev-only-key"
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY es obligatorio en producción")

# En escritorio aceptamos la red local del laboratorio
if ESCRITORIO:
    ALLOWED_HOSTS = [".trycloudflare.com", ".facdin.com", "facdin.com", "*"]
else:
    ALLOWED_HOSTS = env.list(
        "DJANGO_ALLOWED_HOSTS",
        default=["localhost", "127.0.0.1"] if DEBUG else [],
    )

CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[]) + [
    "https://*.trycloudflare.com",
    "https://*.facdin.com",
    "https://facdin.com",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",

    "axes",
    "simple_history",

    "apps.core",
    "apps.accounts",
    "apps.doctors",
    "apps.patients",
    "apps.billing",
    "apps.clinical",
    "saas",
]

# unaccent nativo solo en modo web (PostgreSQL)
if not ESCRITORIO:
    INSTALLED_APPS.append("")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "axes.middleware.AxesMiddleware",
    "apps.core.middleware.LicenciaMiddleware",
    "apps.core.middleware.ConfiguracionInicialMiddleware",
    "apps.core.middleware.TasaMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.tema_clinica",
                "apps.core.context_processors.tasa_actual",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ================= BASE DE DATOS =================
if ESCRITORIO:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": DATA_DIR / "odontoclin.db",
            "OPTIONS": {"timeout": 30},
        }
    }
else:
    DATABASES = {"default": env.db("DATABASE_URL")}
    DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
    DATABASES["default"]["ATOMIC_REQUESTS"] = True

# ================= CACHÉ =================
if ESCRITORIO:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
else:
    CACHES = {"default": env.cache("REDIS_URL", default="locmemcache://")}

AUTH_USER_MODEL = "accounts.Empleado"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

LANGUAGE_CODE = "es"
TIME_ZONE = env.str("TZ", default="America/Caracas")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
if ESCRITORIO:
    MEDIA_ROOT = DATA_DIR / "media"
else:
    MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if DEBUG:
    STORAGES["staticfiles"] = {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    }
elif ESCRITORIO:
    # Sin manifest: no requiere collectstatic previo para desarrollo
    STORAGES["staticfiles"] = {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

# ================= EMAIL =================
if ESCRITORIO:
    EMAIL_BACKEND = env.str(
        "EMAIL_BACKEND",
        default="django.core.mail.backends.console.EmailBackend",
    )
else:
    EMAIL_BACKEND = env.str(
        "EMAIL_BACKEND",
        default="django.core.mail.backends.smtp.EmailBackend",
    )

EMAIL_HOST = env.str("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="no-responder@lab.example.com")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ================= CELERY (solo web) =================
CELERY_TASK_ALWAYS_EAGER = ESCRITORIO or env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_BROKER_URL = env.str("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = env.str("CELERY_RESULT_BACKEND", default="redis://redis:6379/0")
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE

RESULT_LINK_BASE_URL = env.str("RESULT_LINK_BASE_URL", default="http://localhost:8000")
RESULT_TOKEN_TTL_HOURS = env.int("RESULT_TOKEN_TTL_HOURS", default=24)

# ================= SEGURIDAD =================
AXES_ENABLED = env.bool("AXES_ENABLED", default=not DEBUG)
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_RESET_ON_SUCCESS = True

AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesBackend",
    "django.contrib.auth.backends.ModelBackend",
]

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

# HTTPS obligatorio solo en web productivo (escritorio es HTTP local)
if not DEBUG and not ESCRITORIO:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

TESTING = "test" in sys.argv

if TESTING:
    AXES_ENABLED = False
    RATELIMIT_ENABLE = False
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


# ===== Logging a archivo en modo escritorio (diagnóstico) =====
if ESCRITORIO:
    LOGGING["formatters"] = {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    }
    LOGGING["handlers"]["file"] = {
        "class": "logging.FileHandler",
        "filename": str(DATA_DIR / "labclin.log"),
        "formatter": "verbose",
        "encoding": "utf-8",
    }
    LOGGING["root"]["handlers"].append("file")
    LOGGING["loggers"] = {
        "django.request": {
            "handlers": ["file"],
            "level": "ERROR",
            "propagate": False,
        },
    }

# === Seguridad para acceso remoto (v0.3.11 paso 4) ===
SESSION_COOKIE_AGE = 3600  # 1 hora
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_SSL_REDIRECT = False  # Cloudflare ya hace HTTPS
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

TUNNEL_URL = env("DJANGO_TUNNEL_URL", default="https://demo.facdin.com")
