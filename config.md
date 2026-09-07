📘 Guía de instalación en red (2 PCs por WiFi)
Requisitos
Ambas PCs conectadas al mismo router WiFi
El instalador LabClinico-Setup-0.0.6.exe


🖥️ PC 1 · LABORATORIO (servidor principal)
Paso 1 — Instalar
Ejecuta LabClinico-Setup-0.0.6.exe y sigue el asistente.
Paso 2 — Primera configuración
Al abrir por primera vez:
Completa el asistente (crea tu usuario administrador)
Activa tu licencia (solo esta PC la necesita)
Paso 3 — Averiguar la IP de esta PC
Presiona Windows + R, escribe cmd, Enter
Ejecuta:    ipconfig

Anota la Dirección IPv4 (ej: 192.168.1.20)
Paso 4 — Crear acceso directo en modo servidor
Clic derecho en el escritorio → Nuevo → Acceso directo
Escribe (cambia USUARIO por tu nombre de Windows y la IP por la del Paso 3):

   "C:\Users\USUARIO\AppData\Local\Programs\LabClinico\LabClinico.exe" --lan --sin-ventana

   Nombre: Lab Clínico SERVIDOR
A partir de ahora, abre la app SIEMPRE con este acceso directo
✅ El instalador ya abrió el puerto en el firewall de Windows automáticamente.
Paso 5 — Crear usuarios para recepción
Dentro de la app: Equipo → Usuarios → crea un usuario para la recepcionista con rol recepción.


🖥️ PC 2 · RECEPCIÓN (estación)
Paso 1 — Instalar
Ejecuta el mismo instalador LabClinico-Setup-0.0.6.exe.
⚠️ No necesita licencia ni asistente: no guarda datos propios.
Paso 2 — Crear acceso directo en modo estación
Clic derecho en el escritorio → Nuevo → Acceso directo
Escribe (con la IP de la PC 1):

   "C:\Users\USUARIO\AppData\Local\Programs\LabClinico\LabClinico.exe" --conectar 192.168.1.20:8000

   Nombre: Lab Clínico RECEPCIÓN
Paso 3 — Abrir y trabajar
Doble clic al acceso directo → se abre la app → inicia sesión con el usuario de recepción.


⚠️ Importante: IP fija
Si el router le cambia la IP a la PC 1, la PC 2 dejará de conectarse. Recomendado: reserva la IP de la PC 1 en el router (o configúrala estática). Pídelo a tu técnico de redes.

En el instalador hay una casilla "Iniciar servidor al encender Windows". Si la marca, el icono se coloca en shell:startup y el servidor arranca automáticamente con Windows. El cliente nunca tiene que hacer nada después de instalar.











