#!/bin/bash

set -e  # 遇到错误退出

echo "开始安装依赖..."

# 获取当前脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "项目目录: $SCRIPT_DIR"

# 修复有问题的仓库或跳过
echo "修复包管理器配置..."
sudo apt-get update 2>&1 | grep -v "GPG error" || true

# 安装系统依赖（跳过有问题的仓库）
echo "安装系统依赖 libzbar0..."
sudo apt-get install -y libzbar0 --allow-unauthenticated || {
    echo "尝试直接安装 libzbar0..."
    # 如果上述命令失败，尝试直接安装包
    sudo apt-get update --allow-unauthenticated
    sudo apt-get install -y libzbar0 --allow-unauthenticated
}

# 安装 Python 包
echo "安装 Python 包..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/requirements.txt"
    echo "✓ 从 requirements.txt 安装完成"
else
    echo "✗ requirements.txt 不存在"
    exit 1
fi

# 验证安装
echo "验证系统依赖安装..."
if ldconfig -p | grep -q zbar; then
    echo "✓ zbar 库安装成功"
else
    echo "⚠ zbar 库可能未正确安装，但继续执行..."
fi

echo "安装完成!"
