# install.ps1 - PowerShell 快速安装脚本
#
# 用法:
#   irm https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.ps1 | iex
#   或者在 PowerShell 中运行:
#   . { iwr -useb https://raw.githubusercontent.com/huangwb8/skills/main/@install/install.ps1 } | iex
#
# 默认行为: python install-bensz-skills/scripts/install.py --remote --auto
#

$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 主安装器 URL
$InstallerRepo = "https://github.com/huangwb8/skills"
$InstallerRawBase = "https://raw.githubusercontent.com/huangwb8/skills/main"
$InstallerScriptPath = "install-bensz-skills/scripts/install.py"

# 创建临时目录
$TempDir = Join-Path $env:TEMP "install-bensz-skills-$([Guid]::NewGuid())"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

# 清理函数
$Cleanup = {
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}

# 注册清理（即使出错也执行）
trap {
    Write-Error $_.Exception.Message
    & $Cleanup
    exit 1
}

try {
    Write-Info "开始安装 bensz 技能..."
    Write-Host ""

    # 检查 Python
    $PythonCmd = Get-Command python -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty Source

    if (-not $PythonCmd) {
        $PythonCmd = Get-Command python3 -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty Source
    }

    if (-not $PythonCmd) {
        Write-Error "未找到 Python。请先安装 Python 3.7 或更高版本。"
        Write-Info "下载地址: https://www.python.org/downloads/"
        exit 1
    }

    # 获取 Python 版本
    $PythonVersion = & $PythonCmd --version 2>&1
    Write-Info "检测到 Python: $PythonVersion"

    # 创建临时目录结构
    $InstallerDir = Join-Path $TempDir "install-bensz-skills\scripts"
    New-Item -ItemType Directory -Path $InstallerDir -Force | Out-Null

    # 下载安装脚本
    $InstallerUrl = "$InstallerRawBase/$InstallerScriptPath"
    Write-Info "下载安装脚本: $InstallerUrl"

    $InstallerDest = Join-Path $InstallerDir "install.py"
    Invoke-WebRequest -Uri $InstallerUrl -OutFile $InstallerDest -UseBasicParsing

    # 下载 i18n 模块
    $I18nUrl = "$InstallerRawBase/install-bensz-skills/scripts/i18n.py"
    Write-Info "下载 i18n 模块: $I18nUrl"

    $I18nDest = Join-Path $InstallerDir "i18n.py"
    Invoke-WebRequest -Uri $I18nUrl -OutFile $I18nDest -UseBasicParsing

    # 下载 config.yaml
    $ConfigDir = Join-Path $TempDir "install-bensz-skills"
    $ConfigUrl = "$InstallerRawBase/install-bensz-skills/config.yaml"
    Write-Info "下载配置文件: $ConfigUrl"

    $ConfigDest = Join-Path $ConfigDir "config.yaml"
    Invoke-WebRequest -Uri $ConfigUrl -OutFile $ConfigDest -UseBasicParsing

    # 尝试安装 PyYAML（如果未安装）
    $PyYamlCheck = & $PythonCmd -c "import yaml" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Info "安装 PyYAML 依赖..."
        & $PythonCmd -m pip install pyyaml --user -q 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Warn "PyYAML 安装失败，将尝试继续..."
        }
    }

    Write-Host ""
    Write-Info "运行安装程序 (远程自动模式)..."
    Write-Host ""

    # 运行安装脚本（远程自动模式）
    Push-Location $TempDir
    & $PythonCmd "install-bensz-skills/scripts/install.py" --remote --auto
    $ExitCode = $LASTEXITCODE
    Pop-Location

    Write-Host ""
    if ($ExitCode -eq 0) {
        Write-Success "安装完成！"
        Write-Host ""
        Write-Info "提示: 技能已安装到 ~/.claude/skills/ 和 ~/.codex/skills/"
    } else {
        Write-Error "安装失败 (退出代码: $ExitCode)"
        Write-Host ""
        Write-Info "如需帮助，请访问: $InstallerRepo/issues"
    }

    exit $ExitCode

} finally {
    & $Cleanup
}
