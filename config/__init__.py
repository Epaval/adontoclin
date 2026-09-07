# Celery solo está disponible en el modo web.
# En escritorio las tareas se ejecutan al instante (eager).
try:
    from .celery import app as celery_app

    __all__ = ("celery_app",)
except ImportError:  # pragma: no cover
    celery_app = None
