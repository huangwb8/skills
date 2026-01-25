@echo off
REM install.bat - CMD 快速安装脚本
REM
REM 用法:
REM   在 cmd 中运行以下命令下载并执行:
REM   bitsadmin /transfer myDownloadJob /download /priority normal https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.bat %TEMP%\install.bat && %TEMP%\install.bat
REM
REM 或者直接复制此脚本到本地后运行
REM
REM 默认行为: python install-bensz-skills/scripts/install.py --remote --auto
#

setlocal enabledelayedexpansion

REM 主安装器 URL
set INSTALLER_RAW_BASE=https://raw.githubusercontent.com/huangwb8/skills/main
set INSTALLER_REPO=https://github.com/huangwb8/skills

echo [INFO] 开始安装 bensz 技能...
echo.

REM 检查 Python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    goto :python_found
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python3
    goto :python_found
)

echo [ERROR] 未找到 Python。请先安装 Python 3.7 或更高版本。
echo [INFO] 下载地址: https://www.python.org/downloads/
echo        安装时请勾选 "Add Python to PATH"
pause
exit /b 1

:python_found
REM 获取 Python 版本
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] 检测到 Python: %PYTHON_VERSION%

REM 创建临时目录
set TEMP_DIR=%TEMP%\install-bensz-skills-%RANDOM%
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
mkdir "%TEMP_DIR%"

set INSTALLER_DIR=%TEMP_DIR%\install-bensz-skills\scripts
mkdir "%INSTALLER_DIR%"

REM 检查是否有可用的下载工具
set HAS_CURL=0
set HAS_WGET=0
set HAS_BITSADMIN=0

where curl >nul 2>&1
if %ERRORLEVEL% EQU 0 set HAS_CURL=1

where wget >nul 2>&1
if %ERRORLEVEL% EQU 0 set HAS_WGET=1

REM Windows 自带 bitsadmin
set HAS_BITSADMIN=1

REM 下载文件的函数
:download_file
set URL=%~1
set DEST=%~2
echo [INFO] 下载: %URL%

if %HAS_CURL% EQU 1 (
    curl -fsSL "%URL%" -o "%DEST%"
    goto :download_done
)

if %HAS_WGET% EQU 1 (
    wget -q "%URL%" -O "%DEST%"
    goto :download_done
)

if %HAS_BITSADMIN% EQU 1 (
    bitsadmin /transfer dlJob%RANDOM% /download /priority normal "%URL%" "%DEST%"
    goto :download_done
)

echo [ERROR] 未找到可用的下载工具 (curl/wget/bitsadmin)
goto :cleanup_exit

:download_done
if not exist "%DEST%" (
    echo [ERROR] 下载失败: %DEST%
    goto :cleanup_exit
)
exit /b 0

REM 下载安装脚本
set INSTALLER_URL=%INSTALLER_RAW_BASE%/install-bensz-skills/scripts/install.py
set INSTALLER_DEST=%INSTALLER_DIR%\install.py

call :download_file "%INSTALLER_URL%" "%INSTALLER_DEST%"
if %ERRORLEVEL% NEQ 0 goto :cleanup_exit

REM 下载 i18n 模块
set I18N_URL=%INSTALLER_RAW_BASE%/install-bensz-skills/scripts/i18n.py
set I18N_DEST=%INSTALLER_DIR%\i18n.py

call :download_file "%I18N_URL%" "%I18N_DEST%"
if %ERRORLEVEL% NEQ 0 goto :cleanup_exit

REM 下载 config.yaml
set CONFIG_DIR=%TEMP_DIR%\install-bensz-skills
set CONFIG_URL=%INSTALLER_RAW_BASE%/install-bensz-skills/config.yaml
set CONFIG_DEST=%CONFIG_DIR%\config.yaml

call :download_file "%CONFIG_URL%" "%CONFIG_DEST%"
if %ERRORLEVEL% NEQ 0 goto :cleanup_exit

REM 尝试安装 PyYAML
%PYTHON_CMD% -c "import yaml" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] 安装 PyYAML 依赖...
    %PYTHON_CMD% -m pip install pyyaml --user -q >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [WARN] PyYAML 安装失败，将尝试继续...
    )
)

echo.
echo [INFO] 运行安装程序 (远程自动模式)...
echo.

REM 运行安装脚本（远程自动模式）
cd /d "%TEMP_DIR%"
%PYTHON_CMD% "install-bensz-skills\scripts\install.py" --remote --auto
set EXIT_CODE=%ERRORLEVEL%

REM 清理临时目录
:cleanup
cd /d "%TEMP%"
rmdir /s /q "%TEMP_DIR%" >nul 2>&1

echo.
if %EXIT_CODE% EQU 0 (
    echo [SUCCESS] 安装完成！
    echo.
    echo [INFO] 提示: 技能已安装到 %%USERPROFILE%%\.claude\skills\ 和 %%USERPROFILE%%\.codex\skills\
) else (
    echo [ERROR] 安装失败 (退出代码: %EXIT_CODE%)
    echo.
    echo [INFO] 如需帮助，请访问: %INSTALLER_REPO%/issues
)

pause
exit /b %EXIT_CODE%

:cleanup_exit
cd /d "%TEMP%"
rmdir /s /q "%TEMP_DIR%" >nul 2>&1
pause
exit /b 1
