# Home Assistant Docker 部署

基于 Docker 的 Home Assistant 部署方案，支持 Zigbee 设备接入（ZHA 集成），适用于 Windows + WSL2 和 Ubuntu 环境。

## 项目结构

```text
home-assistant/
├── docker-compose.yml       # Docker 服务配置
├── install_docker.sh        # Docker 一键安装脚本（Ubuntu/WSL2）
├── ha.sh                    # Linux/WSL 管理脚本
├── ha.ps1                   # Windows PowerShell 管理脚本
├── config/                  # Home Assistant 配置目录（挂载到容器）
│   ├── configuration.yaml   # 主配置文件
│   ├── automations.yaml     # 自动化配置
│   ├── scripts.yaml         # 脚本配置
│   ├── scenes.yaml          # 场景配置
│   ├── secrets.yaml         # 敏感信息配置
│   └── zha_quirks/          # ZHA 自定义设备适配
└── docs/                    # 文档
    ├── USBIPD使用指南.md
    └── ZHA本地OTA固件更新教程.md
```

## 前置要求

- Docker & Docker Compose
- Windows 环境需要 WSL2（用于 USB 设备直通）
- [USBIPD-WIN](https://github.com/dorssel/usbipd-win)（Windows 下共享 USB 设备到 WSL2）

## 快速开始

### 1. 克隆项目

```bash
git clone <repo-url>
cd home-assistant
```

### 2. 安装 Docker

**Ubuntu / WSL2：**

如果尚未安装 Docker，可使用项目内置脚本一键完成安装：

```bash
chmod +x install_docker.sh
./install_docker.sh
```

脚本会自动完成以下操作：

- 检测是否已安装 Docker，若已安装则直接确认服务状态并退出
- 移除旧版本的 Docker 残留包
- 添加 Docker 官方 APT 仓库并安装最新稳定版
- 启用并启动 `docker` 服务
- 将当前用户加入 `docker` 用户组（免 `sudo` 使用 Docker）

> **注意：** 安装完成后需重新登录（或重启终端）使用户组变更生效，之后才能不加 `sudo` 直接运行 `docker` 命令。

**Windows：**

安装 [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)，安装时勾选 **Use WSL 2 based engine**。安装完成后启动 Docker Desktop，确认任务栏图标显示为运行中状态即可。

### 3. 连接 USB Zigbee 设备（Windows 用户）

将 Zigbee USB Dongle 插入电脑，通过 USBIPD 共享给 WSL2：

```powershell
# 查看设备列表（PowerShell）
usbipd list

# 绑定设备（管理员权限，仅首次需要）
usbipd bind --busid <设备ID>

# 附加设备到 WSL2（每次重启后需要）
usbipd attach --wsl --busid <设备ID>
```

详细说明见 [USBIPD使用指南](docs/USBIPD使用指南.md)。

### 4. 启动服务

**Linux / WSL2：**

```bash
./ha.sh start
```

**Windows PowerShell：**

```powershell
.\ha.ps1 start
```

### 5. 访问 Web 界面

打开浏览器访问：<http://localhost:8123>

## 管理脚本

项目提供了 `ha.sh`（Linux/WSL）和 `ha.ps1`（Windows）两个脚本，支持以下命令：

| 命令 | 说明 |
| --- | --- |
| `start` | 启动 Home Assistant |
| `stop` | 停止 Home Assistant |
| `restart` | 重启 Home Assistant |
| `logs` | 查看实时日志 |
| `shell` | 进入容器命令行 |
| `open` | 显示 Web 访问地址 |
| `status` | 查看容器运行状态 |

示例：

```bash
./ha.sh logs     # 查看日志
./ha.sh restart  # 重启
./ha.sh shell    # 进入容器
```

## Zigbee 配置（ZHA）

本项目使用 ZHA（Zigbee Home Automation）集成管理 Zigbee 设备。

`config/configuration.yaml` 中的关键配置：

```yaml
zha:
  database_path: /config/zigbee.db
  enable_quirks: true
  custom_quirks_path: /config/zha_quirks
```

- **自定义 Quirks**：将设备适配文件放入 `config/zha_quirks/` 目录
- **OTA 固件更新**：参考 [ZHA本地OTA固件更新教程](docs/ZHA本地OTA固件更新教程.md)

## 常用设备

- Zigbee USB Dongle（如 Zigbee 3.0 USB Dongle Plus、ConBee II）
  - 设备路径：`/dev/ttyUSB0`

## 镜像版本说明

镜像地址：`ghcr.io/home-assistant/home-assistant`

| Tag | 说明 | 适用场景 |
| --- | --- | --- |
| `stable` | 最新稳定版（当前使用） | 生产环境，推荐 |
| `latest` | 同 `stable` | 同上 |
| `beta` | 公测版，功能较新但可能有 bug | 想尝鲜但求稳 |
| `dev` | 开发/每日构建版，最新特性 | 开发测试，不稳定 |
| `2025.2.0` | 指定具体版本号 | 锁定版本，防止意外升级 |

修改 `docker-compose.yml` 中的 `image` 字段即可切换版本：

```yaml
image: ghcr.io/home-assistant/home-assistant:beta
```

## 重置系统

如需将项目恢复到初始状态（删除所有运行时产生的未追踪文件，如日志、数据库、缓存等），可使用以下命令。

> **警告：此操作不可逆，会永久删除所有未被 git 追踪的文件和目录（包括 `.gitignore` 中忽略的文件）。执行前请确认已备份重要数据。**

### 第一步：先停止容器

```powershell
.\ha.ps1 stop
```

### 第二步：预览将被删除的文件（不实际删除）

```powershell
git clean -xfdn
```

### 第三步：确认无误后执行清理

```powershell
git clean -xfd
```

参数说明：

| 参数 | 含义 |
| --- | --- |
| `-x` | 同时删除 `.gitignore` 中忽略的文件 |
| `-f` | 强制执行（必需） |
| `-d` | 同时删除未追踪的目录 |
| `-n` | 空运行（dry run），仅预览不删除 |

清理完成后重新启动即可得到全新环境：

```powershell
.\ha.ps1 start
```

## 文档

- [USBIPD使用指南](docs/USBIPD使用指南.md) - Windows 下 USB 设备直通 WSL2
- [ZHA本地OTA固件更新教程](docs/ZHA本地OTA固件更新教程.md) - Zigbee 设备固件升级
