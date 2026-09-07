from django.core.cache import cache


def tasa_actual(request):
    t = cache.get("tasa_actual_cp")
    if t is None:
        from .models import TasaCambio
        t = TasaCambio.actual()
        cache.set("tasa_actual_cp", t, 60)
    return {"tasa_actual": t}
