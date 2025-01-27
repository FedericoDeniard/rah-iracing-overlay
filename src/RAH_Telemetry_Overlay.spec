# RAH_Telemetry_Overlay.spec
import os
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = (
    collect_submodules('flask_socketio') +
    collect_submodules('socketio') +
    collect_submodules('engineio')
)
hiddenimports += collect_submodules('werkzeug')


# Function to collect all files in a directory recursively
def collect_all_files(directory):
    paths = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            # Construct the full (absolute) path
            full_path = os.path.join(root, filename)
            # Construct the destination path (relative to the root directory)
            dest_path = os.path.relpath(full_path, '.')  # Use '.' as root
            paths.append((full_path, dest_path))
    return paths

datas = [
    ('static/img/*.png', 'static/img'),  # Include all .png files in static/img
    ('static/css/*.css', 'static/css'),  # Include CSS files if needed
    ('static/js/*.js', 'static/js'),     # Include JS files if needed
    ('templates/*.html', 'templates'),
]

datas += collect_all_files('path/to/electron/app')

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=True,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RAH iRacing Overlay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    #icon='path_to_your_icon.ico',  # Optional: Add an icon
)
