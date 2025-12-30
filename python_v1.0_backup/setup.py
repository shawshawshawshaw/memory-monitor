"""
py2app 打包配置
"""
from setuptools import setup

APP = ['main_simple.py']
DATA_FILES = ['config.py', 'memory_monitor.py', 'notifier.py']

OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,
    'plist': {
        'CFBundleName': '内存监控',
        'CFBundleDisplayName': '内存监控',
        'CFBundleIdentifier': 'com.memorymonitor.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    },
    'packages': ['PySide6', 'psutil', 'matplotlib'],
    'includes': ['memory_monitor', 'notifier', 'config'],
}

setup(
    app=APP,
    name='内存监控',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
