@echo off
rem Windows: bu dosyaya cift tiklayin. Program tarayicinizda acilir.
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 arayuz.py
  goto son
)
where python >nul 2>nul
if %errorlevel%==0 (
  python arayuz.py
  goto son
)
echo.
echo Python bulunamadi.
echo Once https://www.python.org/downloads/ adresinden Python kurun.
echo Kurulumda "Add python.exe to PATH" kutusunu isaretlemeyi unutmayin.
echo Sonra bu dosyaya yeniden cift tiklayin.
echo.
:son
pause
