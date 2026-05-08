# sentinelx.spec
# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

ROOT = Path(SPECPATH)
block_cipher = None

datas = [
    (str(ROOT / 'frontend' / 'dist'),  'frontend/dist'),
    (str(ROOT / 'config'),             'config'),
    (str(ROOT / 'shared'),             'shared'),
]

windivert_dir = ROOT / 'windivert'
if windivert_dir.exists():
    for f in windivert_dir.iterdir():
        if f.is_file():
            datas.append((str(f), 'windivert'))

blocklist_dir = ROOT / 'data' / 'blocklists'
if blocklist_dir.exists() and any(blocklist_dir.iterdir()):
    datas.append((str(blocklist_dir), 'data/blocklists'))

models_dir = ROOT / 'data' / 'models'
if models_dir.exists() and any(models_dir.iterdir()):
    datas.append((str(models_dir), 'data/models'))

hiddenimports = [
    # uvicorn
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.asyncio',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.protocols.websockets.websockets_impl',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.main',

    # fastapi
    'fastapi',
    'fastapi.middleware.cors',
    'fastapi.staticfiles',
    'fastapi.responses',

    # webview
    'webview',
    'webview.platforms.winforms',

    # orjson
    'orjson',

    # scapy
    'scapy',
    'scapy.all',
    'scapy.layers.dns',
    'scapy.layers.inet',
    'scapy.arch.windows',
    'scapy.arch.windows.native',

    # numpy
    'numpy',
    'numpy.core._multiarray_umath',
    'numpy.core._multiarray_tests',
    'numpy.linalg',
    'numpy.fft',
    'numpy.random',

    # scipy — required by sklearn internally, must NOT be excluded
    'scipy',
    'scipy.sparse',
    'scipy.sparse.csgraph',
    'scipy.special',
    'scipy.linalg',
    'scipy.stats',

    # sklearn
    'sklearn',
    'sklearn.ensemble',
    'sklearn.ensemble._iforest',
    'sklearn.ensemble._forest',
    'sklearn.preprocessing',
    'sklearn.preprocessing._data',
    'sklearn.utils',
    'sklearn.utils._cython_blas',
    'sklearn.utils._weight_vector',
    'sklearn.utils._isfinite',
    'sklearn.utils.murmurhash',
    'sklearn.utils._openmp_helpers',
    'sklearn.neighbors._partition_nodes',
    'sklearn.neighbors._ball_tree',
    'sklearn.neighbors._kd_tree',
    'sklearn.tree._tree',
    'sklearn.tree._splitter',
    'sklearn.tree._criterion',
    'sklearn.tree._utils',
    'sklearn.metrics._dist_metrics',

    # joblib
    'joblib',
    'joblib.externals.loky',
    'joblib.externals.loky.backend',
    'joblib.externals.loky.backend.context',
    'joblib.externals.loky.backend.managers',
    'joblib.externals.loky.backend.popen_loky_win32',

    # watchdog
    'watchdog',
    'watchdog.observers',
    'watchdog.observers.winapi',
    'watchdog.events',

    # psutil
    'psutil',
    'psutil._pswindows',

    # pystray
    'pystray',
    'pystray._win32',

    # PIL
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',

    # aiohttp (used in test runner + optional backend utils)
    'aiohttp',
    'aiohttp.connector',
    'aiohttp.client',

    # other deps
    'tldextract',
    'aiofiles',
    'pydantic',
    'pydantic_settings',
    'pydivert',
    'colorlog',
    'requests',
    'websockets',
    'websockets.legacy',
    'websockets.legacy.server',

    # pythonnet / clr for pywebview WinForms backend
    'clr',
    'clr._extra',
    'System',
    'System.Windows.Forms',
    'System.Drawing',

    # backend packages
    'backend',
    'backend.main',
    'backend.core',
    'backend.core.engine',
    'backend.core.event_bus',
    'backend.core.logger',
    'backend.core.settings',
    'backend.core.state',
    'backend.network',
    'backend.network.packet_capture',
    'backend.network.connection_tracker',
    'backend.network.dns_resolver',
    'backend.network.traffic_analyzer',
    'backend.network.geo_lookup',
    'backend.vpn',
    'backend.vpn.blocklist_manager',
    'backend.vpn.blocklist_parser',
    'backend.vpn.domain_trie',
    'backend.vpn.divert_engine',
    'backend.vpn.filter_lists',
    'backend.vpn.vpn_controller',
    'backend.ai',
    'backend.ai.anomaly_detector',
    'backend.ai.feature_extractor',
    'backend.ai.heuristic_engine',
    'backend.ai.model_trainer',
    'backend.ai.rules',
    'backend.ai.threat_scorer',
    'backend.monitor',
    'backend.monitor.file_scanner',
    'backend.monitor.file_watcher',
    'backend.monitor.process_monitor',
    'backend.monitor.system_stats',
    'backend.protection',
    'backend.protection.alert_manager',
    'backend.protection.file_guard',
    'backend.protection.network_guard',
    'backend.protection.process_guardian',
    'backend.api',
    'backend.api.models',
    'backend.api.rest_router',
    'backend.api.ws_handler',
    'backend.utils',
    'backend.utils.constants',
    'backend.utils.crypto',
    'backend.utils.helpers',
    'backend.utils.throttle',
]

excludes = [
    'tkinter',
    'tkinter.ttk',
    'matplotlib',
    'pandas',
    'IPython',
    'jupyter',
    'notebook',
    'pytest',
    'unittest',
    'doctest',
    'onnxruntime',
    'torch',
    'tensorflow',
    # DO NOT exclude scipy — sklearn needs it
]

a = Analysis(
    [str(ROOT / 'backend' / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

icon_path = ROOT / 'assets' / 'icons' / 'sentinel.ico'
icon_arg  = str(icon_path) if icon_path.exists() else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SentinelX',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',
        'python310.dll',
        'python3.dll',
        'WinDivert.dll',
        'WinDivert64.sys',
        # Don't compress numpy/scipy binaries — UPX breaks them
        'numpy.core._multiarray_umath.pyd',
        'numpy.core._multiarray_tests.pyd',
        '_multiarray_umath.pyd',
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    uac_uiaccess=False,
    icon=icon_arg,
)