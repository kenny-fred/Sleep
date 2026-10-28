@echo off

powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
if errorlevel 1 exit /b 1

powercfg /setdcvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
if errorlevel 1 exit /b 1

powercfg /S SCHEME_CURRENT
if errorlevel 1 exit /b 1

exit /b 0