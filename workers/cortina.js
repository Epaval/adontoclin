const HTML = `<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OdontoClin — Servicio no disponible</title>
<style>
 body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center}
 .card{max-width:520px;margin:16px;padding:40px 32px;background:#1e293b;border-radius:16px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.5)}
 .logo{font-size:44px} h1{font-size:22px;margin:12px 0 4px;color:#38bdf8}
 p{line-height:1.6;color:#94a3b8;font-size:15px}
 .pill{display:inline-block;margin-top:18px;padding:8px 16px;border-radius:999px;background:#0ea5e922;color:#7dd3fc;font-size:13px;font-weight:600}
 small{display:block;margin-top:22px;color:#475569}
</style></head><body><div class="card">
<div class="logo">🦷</div>
<h1>Sistema temporalmente fuera de línea</h1>
<p>El equipo de la clínica donde residen sus datos está <b>apagado o sin conexión a internet</b> en este momento. Sus citas e historiales están seguros: se encuentran en el servidor local de la clínica.</p>
<p>Por favor intente nuevamente en unos minutos o comuníquese con el administrador de su clínica.</p>
<span class="pill">Sus datos no salen de la clínica por diseño de privacidad</span>
<small>OdontoClin · Sistema Integral de Odontología · soporte@facdin.com</small>
</div></body></html>`;

export default {
  async fetch(request) {
    try {
      const resp = await fetch(request);
      if (resp.status === 1033 || resp.status === 1027 || resp.status === 1031 || resp.status >= 500) {
        return new Response(HTML, { status: 503, headers: { "Content-Type": "text/html; charset=utf-8", "Retry-After": "300" } });
      }
      return resp;
    } catch (e) {
      return new Response(HTML, { status: 503, headers: { "Content-Type": "text/html; charset=utf-8", "Retry-After": "300" } });
    }
  }
};
