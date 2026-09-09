# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = [
    'saas', 'saas.models', 'saas.views', 'saas.urls', 'saas.forms', 
    'saas.admin', 'saas.apps', 'saas.cloudflare_service',
    "apps.accounts.management.commands.seed_datos",
    "apps.clinical.models",
    "apps.accounts.management.commands.seed_roles",
    'environ', 'django_environ',
    'requests',
    'qrcode',
]

# Django y terceros
hiddenimports += collect_submodules('django')
hiddenimports += collect_submodules('axes')
hiddenimports += collect_submodules('simple_history')
hiddenimports += collect_submodules('whitenoise')
hiddenimports += collect_submodules('waitress')
hiddenimports += collect_submodules('openpyxl')
hiddenimports += collect_submodules('xhtml2pdf')
hiddenimports += collect_submodules('reportlab')
hiddenimports += collect_submodules('html5lib')
hiddenimports += collect_submodules('pypdf')
hiddenimports += collect_submodules('svglib')
hiddenimports += collect_submodules('tinycss2')
hiddenimports += collect_submodules('cssselect2')
hiddenimports += collect_submodules('requests')
hiddenimports += collect_submodules('qrcode')

hiddenimports += [
    'django.contrib.auth.backends.ModelBackend',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.core.cache.backends.locmem.LocMemCache',
    'django.template.context_processors.debug',
    'django.template.context_processors.request',
    'django.template.context_processors.auth',
    'django.template.context_processors.messages',
    'html5lib', 'pypdf', 'PIL',
    'openpyxl', 'svglib', 'tinycss2', 'cssselect2', 'argon2',
    'argon2.exceptions', 'argon2.low_level',
    'requests',
    'qrcode',
]

datas = [
    ('templates', 'templates'),
    ('staticfiles', 'staticfiles'),
    ('apps', 'apps'),
    ('config', 'config'),
    ('icons', 'icons'),
    ('desktop/cloudflared/cert.pem', '.cloudflared'),
]

datas += collect_data_files('reportlab')
datas += collect_data_files('xhtml2pdf')
datas += collect_data_files('qrcode')

a = Analysis(
    ['desktop/launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'pytest',
        'pydoc_data', 'doctest', 'lib2to3', 'idlelib', 'turtle',
        'django.contrib.gis',
        'django.contrib.sites',
        'django.contrib.syndication',
        'django.contrib.sitemaps',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OdontoClin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="icono.ico",
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name='OdontoClin',
)