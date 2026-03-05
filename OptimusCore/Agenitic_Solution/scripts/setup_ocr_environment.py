#!/usr/bin/env python3
"""
OCR Dependencies Installer and Environment Setup

This script installs and configures OCR dependencies for image processing.
Run this before using the OCR field extractor.

Usage:
    python setup_ocr_environment.py
    python setup_ocr_environment.py --check-only
    python setup_ocr_environment.py --install-tesseract
"""

import subprocess
import sys
import os
import argparse
import platform
from pathlib import Path


def run_command(command, capture_output=True, check=False):
    """Run a system command safely."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=capture_output,
            text=True,
            check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, '', str(e)
    except Exception as e:
        return False, '', str(e)


def check_python_packages():
    """Check if required Python packages are installed."""
    required_packages = [
        'opencv-python',
        'pillow', 
        'numpy',
        'pytesseract',
        'easyocr'
    ]
    
    print("[CHECK] Checking Python packages...")
    missing = []
    installed = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_').replace('opencv_python', 'cv2'))
            print(f"  [OK] {package}")
            installed.append(package)
        except ImportError:
            print(f"  [MISSING] {package} - Missing")
            missing.append(package)
    
    return installed, missing


def install_python_packages(packages):
    """Install missing Python packages with fallback strategies."""
    if not packages:
        print("[OK] All Python packages are already installed")
        return True
    
    print(f"\n[INSTALL] Installing Python packages: {', '.join(packages)}")
    
    # Install packages one by one for better error handling
    all_success = True
    for package in packages:
        print(f"  Installing {package}...")
        
        # Try regular installation first
        success, stdout, stderr = run_command(f'pip install {package}')
        
        if success:
            print(f"  [OK] {package} installed successfully")
            continue
        
        print(f"  [WARNING] Regular install failed for {package}")
        
        # If regular install fails, try --user mode
        print(f"  Trying --user installation for {package}...")
        success, stdout, stderr = run_command(f'pip install --user {package}')
        
        if success:
            print(f"  [OK] {package} installed successfully (user mode)")
            continue
        
        # If still failing and it's opencv-related, suggest opencv-headless
        if 'easyocr' in package and ('cv2' in stderr or 'opencv' in stderr):
            print(f"  Trying opencv-headless workaround for {package}...")
            success, stdout, stderr = run_command(f'pip install --user opencv-python-headless {package}')
            if success:
                print(f"  [OK] {package} installed successfully (opencv-headless)")
                continue
        
        print(f"  [ERROR] Failed to install {package}")
        if stderr:
            print(f"     Error: {stderr[:200]}{'...' if len(stderr) > 200 else ''}")
        print(f"     [TIP] Try manually: pip install --user {package}")
        if 'easyocr' in package:
            print(f"     [TIP] Alternative: pip install --user opencv-python-headless easyocr")
        all_success = False
    
    return all_success


def check_tesseract():
    """Check if Tesseract OCR is installed and accessible."""
    print("\n[CHECK] Checking Tesseract OCR...")
    
    # Try to run tesseract command
    success, stdout, stderr = run_command('tesseract --version')
    
    if success:
        version = stdout.split('\n')[0] if stdout else 'Unknown version'
        print(f"  [OK] Tesseract found: {version}")
        return True
    else:
        print(f"  [WARNING] Tesseract not found or not in PATH")
        return False


def install_tesseract_windows():
    """Provide instructions for installing Tesseract on Windows."""
    print(f"\n[INSTALL] Tesseract Installation Instructions for Windows:")
    print(f"  1. Download Tesseract installer from:")
    print(f"     https://github.com/UB-Mannheim/tesseract/wiki")
    print(f"  2. Run the installer with default settings")
    print(f"  3. Add Tesseract to your PATH or set TESSDATA_PREFIX")
    print(f"  4. Common installation paths:")
    print(f"     - C:\\Program Files\\Tesseract-OCR")
    print(f"     - C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\Programs\\Tesseract-OCR")
    print(f"  5. After installation, restart your command prompt")


def install_tesseract_linux():
    """Provide instructions for installing Tesseract on Linux."""
    print(f"\n[INSTALL] Tesseract Installation Instructions for Linux:")
    print(f"  Ubuntu/Debian:")
    print(f"    sudo apt update && sudo apt install tesseract-ocr")
    print(f"  CentOS/RHEL/Fedora:")
    print(f"    sudo dnf install tesseract")
    print(f"  Arch Linux:")
    print(f"    sudo pacman -S tesseract")


def install_tesseract_mac():
    """Provide instructions for installing Tesseract on macOS."""
    print(f"\n[INSTALL] Tesseract Installation Instructions for macOS:")
    print(f"  Using Homebrew:")
    print(f"    brew install tesseract")
    print(f"  Using MacPorts:")
    print(f"    sudo port install tesseract")


def setup_tesseract_path():
    """Help setup Tesseract PATH on Windows."""
    system = platform.system().lower()
    
    if system == 'windows':
        # Common Tesseract installation paths on Windows
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR",
            r"C:\Program Files (x86)\Tesseract-OCR",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR"),
        ]
        
        print(f"\n[SEARCH] Searching for Tesseract installation...")
        for path in possible_paths:
            tesseract_exe = os.path.join(path, 'tesseract.exe')
            if os.path.exists(tesseract_exe):
                print(f"  [OK] Found Tesseract at: {path}")
                
                # Try to set path temporarily
                current_path = os.environ.get('PATH', '')
                if path not in current_path:
                    os.environ['PATH'] = f"{path};{current_path}"
                    print(f"  [ADDED] Added to current session PATH")
                
                # Check if it works now
                if check_tesseract():
                    return True
        
        print(f"  [ERROR] Tesseract not found in common locations")
        return False
    
    return False


def test_ocr_functionality():
    """Test OCR functionality with a simple test."""
    print(f"\n[TEST] Testing OCR functionality...")
    
    try:
        # Test PyTesseract
        import pytesseract
        from PIL import Image
        import numpy as np
        
        # Create a simple test image with text
        test_image = Image.new('RGB', (200, 50), color='white')
        
        # Use numpy array for OpenCV compatibility test
        import cv2
        test_array = np.array(test_image)
        
        print(f"  [OK] Basic image processing libraries working")
        
        # Test Tesseract (if available)
        try:
            # This might fail if Tesseract is not properly installed
            result = pytesseract.image_to_string(test_image)
            print(f"  [OK] PyTesseract working")
        except Exception as e:
            print(f"  [WARNING] PyTesseract test failed: {e}")
        
        # Test EasyOCR (if available)
        try:
            import easyocr
            reader = easyocr.Reader(['en'], verbose=False)
            print(f"  [OK] EasyOCR working")
        except Exception as e:
            print(f"  [WARNING] EasyOCR not available: {e}")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] OCR functionality test failed: {e}")
        return False


def main():
    """Main setup workflow."""
    parser = argparse.ArgumentParser(description='Setup OCR environment for image processing')
    parser.add_argument('--check-only', action='store_true', help='Only check current setup')
    parser.add_argument('--install-tesseract', action='store_true', help='Show Tesseract installation instructions')
    args = parser.parse_args()
    
    print("[OCR] OCR ENVIRONMENT SETUP")
    print("=" * 50)
    
    # Check Python packages
    installed, missing = check_python_packages()
    
    if not args.check_only and missing:
        if input(f"\nInstall missing packages ({', '.join(missing)})? [y/N]: ").lower() == 'y':
            install_python_packages(missing)
            print(f"\n[RECHECK] Rechecking packages after installation...")
            # Re-check after installation
            installed, missing = check_python_packages()
    
    # Check Tesseract
    tesseract_ok = check_tesseract()
    
    if not tesseract_ok and not args.check_only:
        # Try to find and setup Tesseract on Windows
        if platform.system().lower() == 'windows':
            tesseract_ok = setup_tesseract_path()
    
    # Show installation instructions if needed
    if not tesseract_ok and (args.install_tesseract or not args.check_only):
        system = platform.system().lower()
        if system == 'windows':
            install_tesseract_windows()
        elif system == 'linux':
            install_tesseract_linux()
        elif system == 'darwin':
            install_tesseract_mac()
    
    # Test functionality if not just checking
    if not args.check_only:
        test_ok = test_ocr_functionality()
    else:
        test_ok = True
    
    # Final summary
    print(f"\n{'='*50}")
    print(f"SETUP SUMMARY")
    print(f"{'='*50}")
    print(f"Python packages: {'[OK]' if not missing else '[ERROR]'} ({len(installed)} installed, {len(missing)} missing)")
    print(f"Tesseract OCR:   {'[OK]' if tesseract_ok else '[ERROR]'} {'Available' if tesseract_ok else 'Not found'}")
    print(f"OCR Test:        {'[OK]' if test_ok else '[FAILED]'} {'Passed' if test_ok else 'Failed'}")
    
    if not missing and tesseract_ok and test_ok:
        print(f"\n[SUCCESS] OCR environment is ready!")
        print(f"   You can now use the ocr_field_extractor.py script")
    else:
        print(f"\n[WARNING] Setup incomplete. Please address the issues above.")
        print(f"\n[TROUBLESHOOT] TROUBLESHOOTING STEPS:")
        
        if missing:
            print(f"\n[PACKAGES] For missing Python packages ({', '.join(missing)}):")
            print(f"   Option 1: pip install --user {' '.join(missing)}")
            print(f"   Option 2: Run command prompt as Administrator, then: pip install {' '.join(missing)}")
            if 'easyocr' in missing:
                print(f"   Option 3 (for EasyOCR conflicts): pip install --user opencv-python-headless easyocr")
                
        if not tesseract_ok:
            print(f"\n[HELP] For Tesseract OCR installation:")
            print(f"   1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
            print(f"   2. Choose 'tesseract-ocr-w64-setup-v5.3.0.20221214.exe' (or latest)")
            print(f"   3. Install to default location (C:\\Program Files\\Tesseract-OCR)")
            print(f"   4. Restart command prompt after installation")
            print(f"   5. Test with: tesseract --version")
            
        print(f"\n[TIP] After fixing issues, run this script again to verify setup.")
    
    return 0 if (not missing and tesseract_ok and test_ok) else 1


if __name__ == '__main__':
    sys.exit(main())