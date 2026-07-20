@echo off
cls
:: Check Python availability and install / upgrade pip using TUNA mirror
echo Checking Python...
python --version || (
  echo Python not found. Please install Python first.
  pause
  exit /b 1
)

echo Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
  echo pip not found. Installing pip with ensurepip...
  python -m ensurepip --upgrade >nul 2>&1
  if errorlevel 1 (
    echo Failed to install pip with ensurepip.
    pause
    exit /b 1
  )
)

echo Upgrading pip to the latest version from TUNA...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
  echo Failed to upgrade pip.
  pause
  exit /b 1
)

set "PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple"
echo Using TUNA mirror for package downloads: %PIP_INDEX_URL%

if exist requirements.txt (
  echo Installing packages from requirements.txt...
  python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
  if errorlevel 1 (
    echo Failed to install required packages.
    pause
    exit /b 1
  )
) else (
  echo requirements.txt not found. No additional packages installed.
)

echo Installation complete. Press any key to continue...
pause