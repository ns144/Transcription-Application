@echo off
:: BatchGotAdmin
::-------------------------------------
REM  --> Check for permissions
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

REM --> If error flag set, we do not have admin.
if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params = %*:"="
    echo UAC.ShellExecute "cmd.exe", "/c %~s0 %params%", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"
::--------------------------------------

:: Setup Virtual Environment

python -m venv env \
call .\env\Scripts\activate.bat

:: Update PIP

python.exe -m pip install --upgrade pip
pip cache purge

:: Install requirements
pip install -r requirements.txt

:: Get FFmpeg (For Ubuntu: sudo apt install ffmpeg)
curl -L https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip -o "ffmpeg.zip"

tar -xf "ffmpeg.zip"

move "ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe" "ffmpeg.exe"
move "ffmpeg-master-latest-win64-gpl\bin\ffprobe.exe" "ffprobe.exe"

del "ffmpeg.zip"
rmdir /s /q "ffmpeg-master-latest-win64-gpl"