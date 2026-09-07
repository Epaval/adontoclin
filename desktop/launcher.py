"""
Lanzador de Lab Clínico - Modo Escritorio
"""
import argparse
import os
import socket
import sys
import threading
import traceback

FROZEN = getattr(sys, "frozen", False)

# CRÍTICO: Forzar UTF-8 en Windows para evitar UnicodeEncodeError
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def exe_dir():
    if FROZEN:
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


EXE_DIR = exe_dir()

if FROZEN:
    DATA_BASE = os.environ.get(
        "LABCLIN_DATA",
        os.path.join(os.path.expanduser("~"), "LabClinico"),
    )
else:
    DATA_BASE = EXE_DIR

ERROR_LOG = os.path.join(DATA_BASE, "launcher_error.log")
ESTACION_CFG = os.path.join(DATA_BASE, "estacion.cfg")


def reportar_error(exc_texto):
    try:
        os.makedirs(DATA_BASE, exist_ok=True)
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(exc_texto + "\n")
    except Exception:
        pass

    print(exc_texto, file=sys.stderr)

    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            f"Error al iniciar Lab Clínico:\n\n{exc_texto[:800]}\n\n"
            f"Detalle completo en:\n{ERROR_LOG}",
            "Lab Clínico - Error",
            0x10,
        )
    except Exception:
        pass


def pedir_ip_servidor(ip_actual=""):
    """Asistente gráfico para pedir la IP del servidor (modo estación)"""
    import tkinter as tk
    from tkinter import ttk, messagebox

    resultado = {"ip": None}

    root = tk.Tk()
    root.title("Lab Clínico - Conectar al servidor")
    root.geometry("460x320")
    root.resizable(False, False)
    root.configure(bg="#f8fafc")

    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    # Frame principal
    frame = tk.Frame(root, bg="#f8fafc", padx=30, pady=25)
    frame.pack(fill="both", expand=True)

    # Título
    titulo = tk.Label(
        frame, text="Lab Clínico",
        font=("Segoe UI", 20, "bold"),
        bg="#f8fafc", fg="#0f172a",
    )
    titulo.pack(pady=(0, 5))

    subtitulo = tk.Label(
        frame, text="Conectar como estación",
        font=("Segoe UI", 11),
        bg="#f8fafc", fg="#64748b",
    )
    subtitulo.pack(pady=(0, 20))

    # Etiqueta
    label = tk.Label(
        frame, text="IP del servidor (PC del laboratorio):",
        font=("Segoe UI", 10, "bold"),
        bg="#f8fafc", fg="#334155",
        anchor="w",
    )
    label.pack(fill="x", pady=(0, 5))

    # Campo de entrada
    entry_ip = ttk.Entry(frame, font=("Consolas", 13))
    entry_ip.insert(0, ip_actual)
    entry_ip.pack(fill="x", ipady=6, pady=(0, 20))
    entry_ip.focus_set()

    def conectar():
        ip = entry_ip.get().strip()
        if not ip:
            messagebox.showwarning("Atención", "Ingresa la IP del servidor")
            return
        resultado["ip"] = ip
        root.destroy()

    def cancelar():
        resultado["ip"] = None
        root.destroy()

    # Frame de botones con altura fija
    btn_frame = tk.Frame(frame, bg="#f8fafc")
    btn_frame.pack(fill="x", pady=(0, 15))
    btn_frame.columnconfigure(0, weight=1)
    btn_frame.columnconfigure(1, weight=1)

    btn_cancelar = tk.Button(
        btn_frame, text="Cancelar", command=cancelar,
        font=("Segoe UI", 10),
        bg="#e2e8f0", fg="#334155",
        activebackground="#cbd5e1",
        relief="flat",
        padx=20, pady=10,
        cursor="hand2",
    )
    btn_cancelar.grid(row=0, column=0, sticky="ew", padx=(0, 8))

    btn_conectar = tk.Button(
        btn_frame, text="Conectar", command=conectar,
        font=("Segoe UI", 10, "bold"),
        bg="#0ea5e9", fg="white",
        activebackground="#0284c7", activeforeground="white",
        relief="flat",
        padx=20, pady=10,
        cursor="hand2",
    )
    btn_conectar.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    # Enter para conectar
    entry_ip.bind("<Return>", lambda e: conectar())

    # Nota al pie
    nota = tk.Label(
        frame,
        text="Pregunta la IP al laboratorio principal.\nSe guardará para no volver a pedirla.",
        font=("Segoe UI", 8),
        bg="#f8fafc", fg="#94a3b8",
        justify="center",
    )
    nota.pack(fill="x", pady=(5, 0))

    # Ajustar la ventana al contenido real (respetando escalado del sistema)
    root.update_idletasks()
    req_w = max(root.winfo_reqwidth() + 20, 460)
    req_h = max(root.winfo_reqheight() + 20, 340)
    root.geometry(f"{req_w}x{req_h}")
    try:
        root.eval("tk::PlaceWindow . center")
    except Exception:
        pass

    root.protocol("WM_DELETE_WINDOW", cancelar)
    root.mainloop()

    return resultado["ip"]


def leer_ip_guardada():
    try:
        return open(ESTACION_CFG, "r", encoding="utf-8").read().strip()
    except Exception:
        return ""


def guardar_ip(ip):
    try:
        os.makedirs(os.path.dirname(ESTACION_CFG), exist_ok=True)
        with open(ESTACION_CFG, "w", encoding="utf-8") as f:
            f.write(ip)
    except Exception:
        pass


def detectar_otro_servidor(puerto):
    """Busca otro Lab Clinico Servidor activo en la subred local"""
    import socket
    import concurrent.futures
    import urllib.request

    try:
        mi_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        return None

    def probar(ip):
        try:
            req = urllib.request.urlopen(f"http://{ip}:{puerto}/", timeout=0.5)
            html = req.read(4000).decode("utf-8", "ignore")
            if "Lab Clínico" in html or "configuracion-inicial" in html or "accounts/login" in html:
                return ip
        except Exception:
            pass
        return None

    base = ".".join(mi_ip.split(".")[:3])
    candidatos = [f"{base}.{i}" for i in range(1, 255) if f"{base}.{i}" != mi_ip]
    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as ex:
        for resultado in ex.map(probar, candidatos):
            if resultado:
                return resultado
    return None


def asegurar_firewall():
    """Agrega la regla de firewall (una vez) si no existe; pide permisos de admin"""
    if sys.platform != "win32":
        return
    import subprocess
    CREATE_NO_WINDOW = 0x08000000
    try:
        check = subprocess.run(
            ["netsh", "advfirewall", "firewall", "show", "rule", "name=Lab Clinico"],
            capture_output=True, text=True, creationflags=CREATE_NO_WINDOW, timeout=15,
        )
        if check.returncode == 0 and "Lab Clinico" in check.stdout:
            return  # ya existe
    except Exception:
        return
    try:
        import ctypes
        params = ('advfirewall firewall add rule name="Lab Clinico" dir=in '
                  'action=allow enable=yes protocol=TCP localport=8000')
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", "netsh", params, None, 0
        )
    except Exception:
        pass


def abrir_ventana(url, mantener_vivo=False):
    """Abre la app en ventana nativa; si no hay GUI, usa el navegador"""
    try:
        import webview
        webview.create_window(
            "Lab Clínico", url,
            width=1360, height=860, min_size=(1024, 700),
        )
        webview.start()
    except Exception:
        import webbrowser
        print(f"[i] Sin GUI nativa: abriendo navegador en {url}")
        webbrowser.open(url)
        if mantener_vivo and not FROZEN:
            import time
            while True:
                time.sleep(3600)


def main():
    if FROZEN:
        sys.path.insert(0, getattr(sys, "_MEIPASS", EXE_DIR))
    else:
        sys.path.insert(0, EXE_DIR)

    parser = argparse.ArgumentParser(description="Lab Clínico - Modo Escritorio")
    parser.add_argument("--lan", action="store_true")
    parser.add_argument("--puerto", type=int, default=8000)
    parser.add_argument("--sin-ventana", action="store_true")
    parser.add_argument(
        "--conectar", nargs="?", const="pedir", metavar="IP_PUERTO",
        help="Modo estacion. Sin argumento: pide la IP. Con argumento: conecta directo.",
    )
    args = parser.parse_args()

    # Modo estacion: conectar al servidor
    if args.conectar is not None:
        ip_puerto = args.conectar

        if ip_puerto == "pedir":
            ip_puerto = leer_ip_guardada()
            if not ip_puerto:
                # IP escrita por el instalador al elegir modo estacion
                try:
                    with open(os.path.join(os.path.dirname(sys.executable), "ip_servidor.txt"), encoding="utf-8") as f:
                        ip_puerto = f.read().strip() or None
                except Exception:
                    ip_puerto = None
            if not ip_puerto:
                ip_puerto = pedir_ip_servidor()
                if not ip_puerto:
                    sys.exit(0)
                guardar_ip(ip_puerto)

        url = ip_puerto
        if not url.startswith("http"):
            url = "http://" + url

        # Si no escribio el puerto, usar 8000 por defecto
        resto = url.split("://", 1)[1]
        if ":" not in resto:
            url += ":8000"

        abrir_ventana(url)
        sys.exit(0)

    os.environ["LABCLIN_MODO"] = "escritorio"
    os.environ["LABCLIN_BASE"] = DATA_BASE
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django
    django.setup()

    from django.core.management import call_command
    call_command("migrate", interactive=False, verbosity=0)
    try:
        # Import directo: garantiza que PyInstaller empaquete los comandos en el exe
        from apps.exams.management.commands import seed_catalogo
        from apps.accounts.management.commands import seed_roles  # noqa: F401
        from apps.exams.models import Examen
        # Solo si falta el bloque de orina (instalaciones existentes).
        # Instalación nueva ya lo trae el bootstrap normal; no re-sembrar después.
        if not Examen.objects.filter(nombre_completo="Color orina").exists():
            import io as _io
            _buf = _io.StringIO()
            call_command("seed_catalogo", stdout=_buf, stderr=_buf)
            _out = _buf.getvalue()
            from datetime import datetime as _dt
            with open(os.path.join(DATA_BASE, "launcher.log"), "a", encoding="utf-8") as _f:
                _f.write(f"[{_dt.now()}] seed_datos (orina faltaba):\n{_out}\n")
            print(f"[seed] ejecutado: {Examen.objects.count()} exámenes en BD")
        else:
            print(f"[seed_catalogo] omitido: orina ya existe ({Examen.objects.count()} exámenes)")

        # Caché JSON del catálogo para consultas rápidas
        try:
            import json
            catalogo = list(Examen.objects.values(
                "id", "nombre_completo", "perfil", "tipo_resultado", "valores_ref", "activo"))
            with open(os.path.join(DATA_BASE, "catalogo_cache.json"), "w", encoding="utf-8") as f:
                json.dump(catalogo, f, ensure_ascii=False, indent=2)
            print(f"[caché] catalogo_cache.json generado ({len(catalogo)} exámenes)")
        except Exception as ce:
            print(f"[caché] aviso: {ce}")

    except Exception as e:
        print(f"[seed] aviso: {e}")
    
    # Sincronizar roles/permisos en CADA arranque (idempotente),
    # antes de iniciar el servidor, con registro en archivo
    import io
    buf = io.StringIO()
    try:
        call_command("seed_roles", verbosity=1, stdout=buf)
        resultado_roles = buf.getvalue() or "(sin salida)"
    except Exception as e:
        resultado_roles = f"ERROR: {e}"

    try:
        from datetime import datetime
        log_path = os.path.join(DATA_BASE, "launcher.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] seed_roles:\n{resultado_roles}\n")
    except Exception:
        pass

    # Sincronizar rol <-> groups de empleados existentes
    # (repara instalaciones donde el seed fallo alguna vez)
    sync_msg = ""
    try:
        from apps.accounts.models import Empleado, Rol as RolModel
        for emp in Empleado.objects.select_related("rol").all():
            if emp.rol and emp.rol.group and not emp.groups.filter(pk=emp.rol.group.pk).exists():
                emp.groups.set([emp.rol.group])
                sync_msg += f"  {emp.nombre_usuario}: grupo asignado desde rol\n"
            elif not emp.rol and emp.groups.exists():
                r = RolModel.objects.filter(group=emp.groups.first()).first()
                if r:
                    emp.rol = r
                    emp.save(update_fields=["rol"])
                    sync_msg += f"  {emp.nombre_usuario}: rol asignado desde grupo\n"
    except Exception as e:
        sync_msg += f"SYNC ERROR: {e}"

    if sync_msg:
        try:
            from datetime import datetime
            with open(os.path.join(DATA_BASE, "launcher.log"), "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] sync_roles:\n{sync_msg}\n")
        except Exception:
            pass

    host = "0.0.0.0" if args.lan else "127.0.0.1"

    from waitress import serve
    from django.core.wsgi import get_wsgi_application

    threading.Thread(
        target=serve,
        kwargs={"app": get_wsgi_application(), "host": host,
                "port": args.puerto, "threads": 8},
        daemon=True,
    ).start()

    url = f"http://127.0.0.1:{args.puerto}"

    if args.lan:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "TU_IP"
        print("=" * 60)
        print("  Lab Clínico disponible en la red local:")
        print(f"  → Esta PC:   {url}")
        print(f"  → Otras PCs: http://{ip}:{args.puerto}")
        print("=" * 60)

    if args.sin_ventana:
        print(f"Servidor activo en {url}  (Ctrl+C para salir)")
        
        # Mostrar ventana de estado en modo LAN para que el usuario sepa que está corriendo
        if args.lan:
            import tkinter as tk
            from tkinter import messagebox
            
            ventana = tk.Tk()
            ventana.title("Lab Clínico - Servidor Activo")
            ventana.geometry("480x280")
            ventana.resizable(False, False)
            ventana.configure(bg="#f8fafc")
            ventana.attributes("-topmost", True)
            
            try:
                ventana.eval("tk::PlaceWindow . center")
            except Exception:
                pass
            
            frame = tk.Frame(ventana, bg="#f8fafc", padx=30, pady=25)
            frame.pack(fill="both", expand=True)
            
            tk.Label(
                frame, text="Lab Clínico",
                font=("Segoe UI", 20, "bold"),
                bg="#f8fafc", fg="#0f172a",
            ).pack(pady=(0, 5))
            
            tk.Label(
                frame, text="Servidor activo en la red local",
                font=("Segoe UI", 11),
                bg="#f8fafc", fg="#059669",
            ).pack(pady=(0, 15))
            
            try:
                ip = socket.gethostbyname(socket.gethostname())
            except Exception:
                ip = "TU_IP"
            
            tk.Label(
                frame, text=f"IP del servidor: {ip}",
                font=("Consolas", 12, "bold"),
                bg="#f8fafc", fg="#1e40af",
            ).pack(pady=(0, 5))
            
            tk.Label(
                frame, text=f"Puerto: {args.puerto}",
                font=("Segoe UI", 10),
                bg="#f8fafc", fg="#64748b",
            ).pack(pady=(0, 20))
            
            tk.Label(
                frame, text="Esta ventana debe quedar abierta.",
                font=("Segoe UI", 9),
                bg="#f8fafc", fg="#64748b",
            ).pack()

            tk.Label(
                frame, text="Las estaciones se conectan usando esta IP.",
                font=("Segoe UI", 9),
                bg="#f8fafc", fg="#64748b",
            ).pack(pady=(0, 20))
            
            def detener():
                ventana.destroy()
                import os, signal
                os.kill(os.getpid(), signal.SIGTERM)
            
            btn = tk.Button(
                frame, text="Detener servidor",
                command=detener,
                font=("Segoe UI", 10, "bold"),
                bg="#dc2626", fg="white",
                activebackground="#b91c1c",
                relief="flat",
                padx=20, pady=8,
                cursor="hand2",
            )
            btn.pack()
            
            # Ajustar la ventana al contenido real (respeta el escalado del sistema)
            ventana.update_idletasks()
            req_w = max(ventana.winfo_reqwidth() + 20, 480)
            req_h = max(ventana.winfo_reqheight() + 20, 300)
            ventana.geometry(f"{req_w}x{req_h}")
            try:
                ventana.eval("tk::PlaceWindow . center")
            except Exception:
                pass

            ventana.protocol("WM_DELETE_WINDOW", detener)
            ventana.mainloop()
        else:
            import time
            while True:
                time.sleep(3600)

    abrir_ventana(url, mantener_vivo=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        reportar_error(traceback.format_exc())
        sys.exit(1)
