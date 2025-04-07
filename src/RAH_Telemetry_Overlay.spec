# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import platform
from pathlib import Path
import eventlet

# Define the base directory
base_dir = os.path.abspath(os.path.dirname('src'))
if os.path.basename(os.getcwd()) == 'src':
    base_dir = os.getcwd()
else:
    base_dir = os.path.join(os.getcwd(), 'src')

# Define directories for data files
overlays_dir = os.path.join(base_dir, 'overlays')
interface_dir = os.path.join(base_dir, 'interface')
common_dir = os.path.join(base_dir, 'common')

# Get all data files
datas = []

# Add overlays files
for root, dirs, files in os.walk(overlays_dir):
    for file in files:
        src_path = os.path.join(root, file)
        rel_path = os.path.relpath(src_path, base_dir)
        dst_path = os.path.dirname(rel_path)
        datas.append((rel_path, dst_path))

# Add interface files
for root, dirs, files in os.walk(interface_dir):
    for file in files:
        src_path = os.path.join(root, file)
        rel_path = os.path.relpath(src_path, base_dir)
        dst_path = os.path.dirname(rel_path)
        datas.append((rel_path, dst_path))

# Add common files
for root, dirs, files in os.walk(common_dir):
    for file in files:
        src_path = os.path.join(root, file)
        rel_path = os.path.relpath(src_path, base_dir)
        dst_path = os.path.dirname(rel_path)
        datas.append((rel_path, dst_path))

block_cipher = None

# Get the path to app.py
app_path = os.path.join(base_dir, 'app.py')
if not os.path.exists(app_path):
    print(f"Warning: {app_path} does not exist!")
    app_path = 'app.py'  # Fallback to relative path

# Add additional hidden imports for Windows
hidden_imports = [
    # Import all eventlet hub types
    'eventlet.hubs.epolls',
    'eventlet.hubs.kqueue',
    'eventlet.hubs.selects',
    'eventlet.hubs.selectors',
    'eventlet.hubs.poll',
    'eventlet.hubs.hub',
    'eventlet.hubs.impl_select',
    'eventlet.hubs.impl_poll',
    'eventlet.hubs.timer',
    # Other eventlet modules
    'eventlet.greenio',
    'eventlet.greenthread',
    'eventlet.queue',
    'eventlet.patcher',
    'eventlet.corolocal',
    'eventlet.semaphore',
    'eventlet.websocket',
    'eventlet.event',
    'eventlet.green',
    'eventlet.support',
    # Other dependencies
    'selectors',
    'select',
    'socket',
    'dns',
    'dns.dnssec',
    'dns.e164',
    'dns.hash',
    'dns.namedict',
    'dns.tsigkeyring',
    'dns.update',
    'dns.version',
    'dns.zone',
    'dns.versioned',
    'dns.resolver',
    'dns.message',
    'dns.name',
    'dns.tokenizer',
    'dns.rdatatype',
    'dns.rdataclass',
    'dns.rdtypes',
    'dns.exception',
    'dns.wiredata',
    'dns.flags',
    'engineio.async_drivers.eventlet',
    'engineio.async_drivers.threading',
    'irsdk',
    'flask',
    'flask_socketio',
    'threading',
    'multiprocessing',
    'socketio',
    'socketio.client',
    'eventlet.green.subprocess',
    'eventlet.green.os',
    'eventlet.green.select',
    'eventlet.green.socket',
    'eventlet.green.thread',
    'eventlet.green.threading',
    'eventlet.green.time',
    '_thread',
    'queue',
]

# Windows-specific additional hidden imports
if platform.system() == 'Windows':
    hidden_imports.extend([
        'eventlet.hubs.hub',
        'engineio.async_drivers',
        'dns.rdtypes.ANY',
        'dns.rdtypes.IN',
        'winsock',
        'win32pipe',
        'win32file',
        'win32api',
        'win32con',
    ])
    
# Add datas to ensure eventlet modules are included
eventlet_path = os.path.dirname(os.path.abspath(eventlet.__file__))
datas.append((eventlet_path, 'eventlet'))

# Add runtime hooks to ensure eventlet is properly initialized
runtime_hooks = []

a = Analysis(
    [app_path],
    pathex=[base_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RAH_Telemetry_Overlay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Changed from True to False to hide the terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RAH_Telemetry_Overlay',
)
