import os
import sys
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Inicializar variables de entorno
env = environ.Env()
env.read_env(BASE_DIR / '.env')

# =========================================================
# DETECCIÓN DE ENTORNO (PyInstaller vs Desarrollo)
# =========================================================
if getattr(sys, "frozen", False):
    # Modo Ejecutable (.exe)
    if hasattr(sys, "_MEIPASS"):
        BASE_DIR = Path(sys._MEIPASS)
    else:
        BASE_DIR = Path(sys.executable).parent / "_internal"
    ESCRITORIO = True
    os.environ["LABCLIN_MODO"] = "escritorio"
    # DATA_DIR debe estar fuera de _internal, junto al .exe, para ser persistente y writable
    DATA_DIR = Path(sys.executable).parent / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
else:
    # Modo Desarrollo o Servidor
    MODO = os.environ.get("LABCLIN_MODO", "web")
    ESCRITORIO = MODO == "escritorio"
    if ESCRITORIO:
        DATA_DIR = BASE_DIR / "data"
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    else:
        DATA_DIR = BASE_DIR / "data"

# SECRET_KEY
if ESCRITORIO:
    key_file = DATA_DIR / "secret.key"
    if not key_file.exists():
        from django.core.management.utils import get_random_secret_key
        key_file.write_text(get_random_secret_key())
    SECRET_KEY = key_file.read_text()
else:
    SECRET_KEY = env.str("DJANGO_SECRET_KEY", default="clave-por-defecto-cambiar-en-produccion")

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

MEDIA_URL = "/media/"
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

# Rol de instalacion: "clinica" (operativa) o "proveedor" (solo gestion SaaS)
LABCLIN_ROL = env("DJANGO_LABCLIN_ROL", default="clinica")

# URL del ultimo release de OdontoClin.exe (GitHub Releases)
LABCLIN_RELEASES_URL = env("DJANGO_RELEASES_URL", default="https://github.com/Epaval/adontoclin/releases/download/v0.4.0/OdontoClin.exe")

# Puerto local donde el CLIENTE corre OdontoClin (Windows default 8000)
LABCLIN_INGRESS_PORT = env("DJANGO_INGRESS_PORT", default="8000")
