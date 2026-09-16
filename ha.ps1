param(
    [Parameter(Position = 0)]
    [ValidateSet("start", "stop", "restart", "logs", "logs-all", "shell", "install-hacs", "open", "status", "help")]
    [string]$Action = "help"
)

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ContainerName = "homeassistant"
$WebUrl = "http://localhost:8123"

function Show-Help {
    Write-Host ""
    Write-Host "Home Assistant Docker Helper" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\ha.ps1 start        启动 Home Assistant"
    Write-Host "  .\ha.ps1 stop         停止 Home Assistant"
    Write-Host "  .\ha.ps1 restart      重启 Home Assistant"
    Write-Host "  .\ha.ps1 logs         查看日志（实时）"
    Write-Host "  .\ha.ps1 logs-all     查看所有历史日志并持续跟随"
    Write-Host "  .\ha.ps1 shell        进入容器命令行"
    Write-Host "  .\ha.ps1 install-hacs 安装 HACS"
    Write-Host "  .\ha.ps1 open         打开 Web 页面"
    Write-Host "  .\ha.ps1 status       查看容器状态"
    Write-Host ""
}

function Go-ProjectDir {
    Set-Location $ProjectDir
}

function Start-HA {
    Go-ProjectDir
    Write-Host "==> 启动 Home Assistant..." -ForegroundColor Green
    docker compose up -d
}

function Stop-HA {
    Go-ProjectDir
    Write-Host "==> 停止 Home Assistant..." -ForegroundColor Yellow
    docker compose down
}

function Restart-HA {
    Go-ProjectDir
    Write-Host "==> 重启 Home Assistant..." -ForegroundColor Yellow
    docker compose restart homeassistant
}

function Show-Logs {
    $since = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    Write-Host "==> 查看日志（Ctrl+C 退出）" -ForegroundColor Cyan
    docker logs --since $since -f $ContainerName
}

function Show-AllLogs {
    Write-Host "==> 查看所有日志（Ctrl+C 退出）" -ForegroundColor Cyan
    docker logs -f $ContainerName
}

function Enter-Shell {
    Write-Host "==> 进入容器命令行" -ForegroundColor Cyan
    docker exec -it $ContainerName bash
}

function Install-HACS {
    # HACS 安装到持久化的 /config/custom_components 目录中。
    Go-ProjectDir
    Write-Host "==> 确保 Home Assistant 容器正在运行..." -ForegroundColor Green
    docker compose up -d homeassistant
    if ($LASTEXITCODE -ne 0) {
        return
    }

    # 等待配置文件可用，避免容器刚启动时 HACS 无法定位 /config。
    $configReady = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        docker compose exec -T homeassistant test -f /config/configuration.yaml 2>$null
        if ($LASTEXITCODE -eq 0) {
            $configReady = $true
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not $configReady) {
        Write-Host "未找到 Home Assistant 配置目录，请检查 ./config 挂载。" -ForegroundColor Red
        return
    }

    # 在容器内显式切换到 /config 后执行官方安装脚本。
    Write-Host "==> 安装 HACS..." -ForegroundColor Green
    docker compose exec -T homeassistant bash -c "cd /config && wget -O - https://get.hacs.xyz | bash -"
    $installExitCode = $LASTEXITCODE
    docker compose exec -T homeassistant test -f /config/custom_components/hacs/manifest.json 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "HACS 安装失败，请检查容器日志和网络连接。" -ForegroundColor Red
        return
    }
    if ($installExitCode -ne 0) {
        Write-Host "HACS 文件已安装，但安装脚本返回了非零状态，继续重启 Home Assistant。" -ForegroundColor Yellow
    }

    Write-Host "==> 重启 Home Assistant 以加载 HACS..." -ForegroundColor Yellow
    docker compose restart homeassistant
}

function Open-Web {
    Write-Host "==> 打开 Home Assistant Web 页面" -ForegroundColor Cyan
    Start-Process $WebUrl
}

function Show-Status {
    docker ps --filter "name=$ContainerName"
}

switch ($Action) {
    "start"    { Start-HA }
    "stop"     { Stop-HA }
    "restart"  { Restart-HA }
    "logs"     { Show-Logs }
    "logs-all" { Show-AllLogs }
    "shell"    { Enter-Shell }
    "install-hacs" { Install-HACS }
    "open"     { Open-Web }
    "status"   { Show-Status }
    "help"     { Show-Help }
    default    { Show-Help }
}
