"""
Setup and Packaging Script for Zoho Deluge Scraper & AI Assistant
Uses PyInstaller to package the Streamlit application and Python runtime into a standalone executable.
"""

import os
import sys
import shutil
import time
import argparse
import subprocess

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPEC_FILE = os.path.join(BASE_DIR, "zoho_assistant.spec")
LAUNCHER_FILE = os.path.join(BASE_DIR, "launcher.py")
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")


def check_prerequisites(auto_install: bool = True):
    """Verify that Python and all required packaging libraries are available."""
    print("🔍 Checking build prerequisites...")
    print(f"   • Python Runtime  : {sys.version.split()[0]} ({sys.executable})")

    # Required runtime packages
    required_packages = {
        "streamlit": "streamlit",
        "chromadb": "chromadb",
        "ollama": "ollama",
        "requests": "requests",
        "pandas": "pandas",
        "PyInstaller": "pyinstaller",
    }

    missing = []
    for pkg_import, pkg_name in required_packages.items():
        try:
            __import__(pkg_import)
            print(f"   • {pkg_name:<16}: ✅ Installed")
        except ImportError:
            print(f"   • {pkg_name:<16}: ❌ Missing")
            missing.append(pkg_name)

    if missing:
        if auto_install:
            print(f"\n📦 Automatically installing missing build packages: {', '.join(missing)}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
                print("✅ Dependencies installed successfully.\n")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install dependencies: {e}")
                sys.exit(1)
        else:
            print(f"\n❌ Missing required dependencies: {', '.join(missing)}")
            print(f"Please install them via: pip install {' '.join(missing)}")
            sys.exit(1)


def clean_build_artifacts():
    """Remove previous build and dist directories."""
    print("🧹 Cleaning previous build artifacts...")
    for target in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(target):
            try:
                shutil.rmtree(target)
                print(f"   • Removed: {os.path.basename(target)}/")
            except Exception as e:
                print(f"   ⚠️ Could not remove {target}: {e}")


def create_distribution_helpers(dist_path: str):
    """Generate convenient launcher batch scripts and deployment documentation."""
    # Create batch launcher
    bat_content = """@echo off
title Zoho Deluge Scraper & AI Assistant
echo ======================================================================
echo  Launching Zoho Deluge Scraper & AI Assistant Desktop Application
echo ======================================================================
echo.

:: Check if Ollama is running locally
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Local Ollama service was not detected at http://localhost:11434!
    echo For AI Assistant chat and embeddings, please launch Ollama in a separate terminal:
    echo    ollama run llama3
    echo    ollama pull nomic-embed-text
    echo.
)

:: Launch the standalone application
if exist "%~dp0Zoho_AI_Assistant\\Zoho_AI_Assistant.exe" (
    start "" "%~dp0Zoho_AI_Assistant\\Zoho_AI_Assistant.exe"
) else if exist "%~dp0Zoho_AI_Assistant.exe" (
    start "" "%~dp0Zoho_AI_Assistant.exe"
) else (
    echo [ERROR] Zoho_AI_Assistant.exe not found!
    pause
)
"""
    bat_file = os.path.join(DIST_DIR, "Launch_Assistant.bat")
    try:
        with open(bat_file, "w", encoding="utf-8") as f:
            f.write(bat_content)
        print(f"📄 Generated batch launcher: {bat_file}")
    except Exception as e:
        print(f"⚠️ Could not write batch launcher: {e}")

    # Create README in dist
    readme_content = """Zoho Deluge Scraper & AI Assistant - Standalone Distribution
============================================================

Overview:
---------
This standalone package runs the multi-page Streamlit dashboard, vector database,
and AI assistant locally on Windows without requiring a global Python installation.

How to Run:
-----------
1. Start your local Ollama instance (required for Llama-3 chat & local embeddings):
   ollama run llama3
   ollama pull nomic-embed-text

2. Double-click 'Launch_Assistant.bat' or open 'Zoho_AI_Assistant/Zoho_AI_Assistant.exe'.

3. The application will automatically find an open port (default 8501) and launch
   your web browser directly to the dashboard!

Included Features:
------------------
- Multi-page Streamlit Dashboard & Control Panel
- Zoho Deluge Scraper with immediate trigger & scheduled jobs
- ChromaDB vector store with adaptive semantic chunking & nomic-embed-text embeddings
- Llama-3 AI Assistant with strict Zoho Creator domain guardrails
"""
    readme_file = os.path.join(DIST_DIR, "README_DISTRIBUTION.txt")
    try:
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(readme_content)
        print(f"📄 Generated distribution README: {readme_file}")
    except Exception as e:
        print(f"⚠️ Could not write distribution README: {e}")


def build_executable(clean: bool = False, onefile: bool = False, noconsole: bool = False):
    """Run PyInstaller build process."""
    t_start = time.time()
    print("\n" + "=" * 70)
    print("🛠️  Building Standalone Executable with PyInstaller")
    print(f"📁 Project Root    : {BASE_DIR}")
    print(f"🚀 Launcher Script : {LAUNCHER_FILE}")
    print(f"📑 Specification   : {SPEC_FILE}")
    print(f"📦 Packaging Mode  : {'OneFile (.exe single archive)' if onefile else 'OneDir (Folder distribution - Recommended)'}")
    print("=" * 70 + "\n")

    if clean:
        clean_build_artifacts()

    # Import PyInstaller main build runner
    import PyInstaller.__main__

    # Build command arguments
    pyinstaller_args = [
        SPEC_FILE,
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
    ]

    if noconsole:
        pyinstaller_args.append("--noconsole")

    print(f"⚙️ Running PyInstaller with arguments: {' '.join(pyinstaller_args)}\n")

    try:
        PyInstaller.__main__.run(pyinstaller_args)
    except Exception as e:
        print(f"\n❌ PyInstaller build encountered an error: {e}")
        return False

    elapsed = round(time.time() - t_start, 2)
    print("\n" + "=" * 70)
    print(f"✅ Build finished in {elapsed} seconds!")

    # Verify executable output
    expected_exe = os.path.join(DIST_DIR, "Zoho_AI_Assistant", "Zoho_AI_Assistant.exe")
    if not os.path.exists(expected_exe):
        # Check if onefile mode
        expected_exe_single = os.path.join(DIST_DIR, "Zoho_AI_Assistant.exe")
        if os.path.exists(expected_exe_single):
            expected_exe = expected_exe_single

    if os.path.exists(expected_exe):
        size_mb = os.path.getsize(expected_exe) / (1024 * 1024)
        print(f"🎯 Output Executable: {expected_exe}")
        print(f"📦 Binary Size      : {size_mb:.2f} MB")
        create_distribution_helpers(DIST_DIR)
        print("=" * 70 + "\n")
        return True
    else:
        print(f"⚠️ Warning: Could not locate expected binary at {expected_exe}")
        print("=" * 70 + "\n")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Package Zoho Deluge Scraper & AI Assistant into a standalone Windows executable."
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build and dist directories before starting compilation"
    )
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="Bundle into a single self-extracting executable (Note: OneDir is recommended for ChromaDB/Streamlit persistence)"
    )
    parser.add_argument(
        "--noconsole",
        action="store_true",
        help="Hide the terminal console window when launching the application"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check prerequisites, spec file, and paths without invoking PyInstaller"
    )

    args = parser.parse_args()

    # Step 1: Check prerequisites
    check_prerequisites(auto_install=True)

    # Step 2: Validate core files
    for req_file in [LAUNCHER_FILE, SPEC_FILE, os.path.join(BASE_DIR, "App.py")]:
        if not os.path.exists(req_file):
            print(f"❌ Error: Required file missing: {req_file}")
            sys.exit(1)

    if args.dry_run:
        print("\n✨ Dry run validation complete. Everything is configured and ready for compilation.")
        return

    # Step 3: Run build
    success = build_executable(clean=args.clean, onefile=args.onefile, noconsole=args.noconsole)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
