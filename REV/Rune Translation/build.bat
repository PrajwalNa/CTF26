@echo off
setlocal

set GCC=D:\msys64\mingw64\bin\gcc.exe
set STRIP=D:\msys64\mingw64\bin\strip.exe

if not exist "%GCC%" (
    echo GCC not found at %GCC%
    exit /b 1
)

if not exist "%STRIP%" (
    echo strip not found at %STRIP%
    exit /b 1
)

%GCC% -O2 -Wall -Wextra -o RuneTranslation.exe rune.c
if %ERRORLEVEL% NEQ 0 (
    echo Build failed with error code %ERRORLEVEL%
    exit /b 1
)

%STRIP% --strip-debug RuneTranslation.exe
if %ERRORLEVEL% NEQ 0 (
    echo Strip failed with error code %ERRORLEVEL%
    exit /b 1
)

echo Build successful.
echo Output: RuneTranslation.exe

endlocal
