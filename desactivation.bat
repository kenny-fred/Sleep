@echo off

set "AC=%~1"
set "DC=%~2"

if "%AC%"=="" exit /b 1
if "%DC%"=="" exit /b 1

powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION %AC%
if errorlevel 1 exit /b 1

powercfg /setdcvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION %DC%
if errorlevel 1 exit /b 1

powercfg /S SCHEME_CURRENT
if errorlevel 1 exit /b 1

exit /b 0