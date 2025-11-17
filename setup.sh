#!/bin/bash

set -e

echo "=== 应用安装和配置脚本 ==="

# 获取当前脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "项目目录: $SCRIPT_DIR"

# 检查 main.py 是否存在
if [ ! -f "$SCRIPT_DIR/main.py" ]; then
    echo "错误: 在 $SCRIPT_DIR 中找不到 main.py"
    exit 1
fi

# 运行安装脚本
echo "步骤 1: 安装依赖..."
if [ -f "$SCRIPT_DIR/install.sh" ]; then
    chmod +x "$SCRIPT_DIR/install.sh"
    "$SCRIPT_DIR/install.sh"
else
    echo "错误: 找不到 install.sh"
    exit 1
fi

# 配置开机自启动
echo "步骤 2: 配置开机自启动..."

# 服务名称（可以根据项目名修改）
SERVICE_NAME="qq_blog"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# 创建服务文件
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=My Python Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$SERVICE_NAME

# 环境变量（如果需要）
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "服务文件已创建: $SERVICE_FILE"

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable $SERVICE_NAME.service

echo "步骤 3: 启动服务..."
sudo systemctl start $SERVICE_NAME.service

# 等待一下然后检查服务状态
sleep 2
echo "检查服务状态..."
sudo systemctl status $SERVICE_NAME.service

echo "=== 安装完成 ==="
echo ""
echo "常用命令:"
echo " 启动服务: sudo systemctl start $SERVICE_NAME"
echo " 停止服务: sudo systemctl stop $SERVICE_NAME"
echo " 重启服务: sudo systemctl restart $SERVICE_NAME"
echo " 查看状态: sudo systemctl status $SERVICE_NAME"
echo " 查看日志: sudo journalctl -u $SERVICE_NAME -f"
echo " 实时日志: sudo journalctl -u $SERVICE_NAME -f --lines=50"
echo ""
echo "服务已设置为开机自启动"
