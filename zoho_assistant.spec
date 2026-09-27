# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification File for Zoho Deluge Scraper & AI Assistant
Packages Streamlit, ChromaDB, Ollama client, and multi-page views into a standalone distribution.
"""

import os
import sys
from PyInstaller.utils.hooks import copy_metadata, collect_data_files, collect_submodules

block_cipher = None
BASE_DIR = os.path.abspath(SPECPATH)

# Collect required dynamic package data
streamlit_datas = collect_data_files('streamlit')
chromadb_datas = collect_data_files('chromadb')

# Collect package distributions / metadata
metadata_datas = (
    copy_metadata('streamlit') +
    copy_metadata('chromadb') +
    copy_metadata('ollama') +
    copy_metadata('requests')
)

# Project local files & directories
project_datas = [
    (os.path.join(BASE_DIR, 'App.py'), '.'),
    (os.path.join(BASE_DIR, 'auth.py'), '.'),
    (os.path.join(BASE_DIR, 'builtin_engine.py'), '.'),
    (os.path.join(BASE_DIR, 'views'), 'views'),
    (os.path.join(BASE_DIR, 'data'), 'data'),
    (os.path.join(BASE_DIR, 'scraper_manager.py'), '.'),
    (os.path.join(BASE_DIR, 'vector_setup.py'), '.'),
    (os.path.join(BASE_DIR, 'crawl_zoho_docs.py'), '.'),
]

if os.path.exists(os.path.join(BASE_DIR, '.streamlit')):
    project_datas.append((os.path.join(BASE_DIR, '.streamlit'), '.streamlit'))

for cfg_name in ['execution_history.json', 'schedule_config.json']:
    cfg_path = os.path.join(BASE_DIR, cfg_name)
    if os.path.exists(cfg_path):
        project_datas.append((cfg_path, '.'))

all_datas = streamlit_datas + chromadb_datas + metadata_datas + project_datas

# Hidden imports dynamically collected from installed Streamlit and ChromaDB
hidden_imports = (
    collect_submodules('streamlit') +
    collect_submodules('chromadb') +
    [
        'altair',
        'altair.vegalite.v5.api',
        'tornado',
        'pandas',
        'pydeck',
        'ollama',
        'requests',
        'auth',
        'builtin_engine',
        'scraper_manager',
        'vector_setup',
        'crawl_zoho_docs',
    ]
)

a = Analysis(
    [os.path.join(BASE_DIR, 'launcher.py')],
    pathex=[BASE_DIR],
    binaries=[],
    datas=all_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'tkinter', 'unittest', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Zoho_AI_Assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    name='Zoho_AI_Assistant',
)
