@echo off
REM OCR Environment Fix Script for Windows
REM This script helps resolve common installation issues

echo.
echo ====================================================
echo   OCR ENVIRONMENT FIX SCRIPT FOR WINDOWS
echo ====================================================
echo.

echo [1/3] Installing Python packages with --user flag...
echo.

echo Installing pillow (Python Imaging Library)...
pip install --user pillow
if %errorlevel% equ 0 (
    echo   ✓ pillow installed successfully
) else (
    echo   ❌ Failed to install pillow
)

echo.
echo Installing EasyOCR with opencv-headless workaround...
pip install --user opencv-python-headless
pip install --user easyocr
if %errorlevel% equ 0 (
    echo   ✓ easyocr installed successfully
) else (
    echo   ❌ Failed to install easyocr
    echo   💡 Try running this script as Administrator
)

echo.
echo [2/3] Downloading Tesseract OCR...
echo Opening download page for Tesseract OCR...
echo Please download and install tesseract-ocr-w64-setup-v5.x.x.exe
start https://github.com/UB-Mannheim/tesseract/wiki
echo.
pause

echo.
echo [3/3] Verifying setup...
python scripts\setup_ocr_environment.py --check-only

echo.
echo ====================================================
echo   SETUP COMPLETE
echo ====================================================
echo.
echo Next steps:
echo 1. If Tesseract is still not found, restart your command prompt
echo 2. Test with: python scripts\analyze_guidewire_form.py --help
echo 3. Analyze your image: python scripts\analyze_guidewire_form.py "guidewire-policy-centre.png"
echo.
pause