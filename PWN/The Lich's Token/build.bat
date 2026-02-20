@echo off
REM Compile Lich Protocol Server with obfuscation and static linking
REM Updated for msys64 at D:\msys64

set GCC=D:\msys64\mingw64\bin\gcc.exe
set STRIP=D:\msys64\mingw64\bin\strip.exe

REM Compile with optimization and obfuscation
%GCC% -O3 -fomit-frame-pointer -fno-unwind-tables -fno-asynchronous-unwind-tables ^
    -ffunction-sections -fdata-sections -fvisibility=hidden ^
    -Wall -Wextra -Iinclude ^
    -Wl,--gc-sections ^
    src/main.c src/proto.c src/net.c src/state.c ^
    src/handlers.c src/crypto.c src/config.c src/error.c ^
    -static -o lichServer.exe -lcrypto -lblake3 -lws2_32

if %ERRORLEVEL% EQU 0 (
    echo Build successful!
    echo Stripping symbols...
    %STRIP% --keep-symbol=main lichServer.exe
    echo Done. Output: lichServer.exe
    echo Binary size: 
    for %%F in (lichServer.exe) do echo %%~zF bytes
) else (
    echo Build failed with error code %ERRORLEVEL%
    exit /b 1
)