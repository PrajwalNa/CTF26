@echo off
setlocal

set GCC=D:\msys64\mingw64\bin\gcc.exe
set STRIP=D:\msys64\mingw64\bin\strip.exe

%GCC% -O2 -s -Wall -Wextra -o Oath.exe guard.c

if %ERRORLEVEL% EQU 0 (
    echo Build successful.
     %STRIP% --keep-symbol=main Oath.exe
    echo Output: Oath.exe
) else (
    echo Build failed with error code %ERRORLEVEL%
    exit /b 1
)

endlocal
