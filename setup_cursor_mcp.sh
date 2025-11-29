#!/bin/bash
# Cursor MCP 配置脚本

set -e

PROJECT_DIR="/Users/gzp/Github/mymcp"
CONFIG_FILE="$PROJECT_DIR/config.yaml"
CURSOR_MCP_CONFIG="$HOME/.cursor/mcp.json"

echo "🚀 设置 Cursor MCP 配置..."
echo ""

# 检查项目目录
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 错误: 项目目录不存在: $PROJECT_DIR"
    exit 1
fi

# 检查配置文件
if [ ! -f "$CONFIG_FILE" ]; then
    echo "📝 创建配置文件..."
    if [ -f "$PROJECT_DIR/config.intellij-example.yaml" ]; then
        cp "$PROJECT_DIR/config.intellij-example.yaml" "$CONFIG_FILE"
        echo "✅ 已从示例配置创建配置文件"
    else
        cp "$PROJECT_DIR/config.yaml.example" "$CONFIG_FILE"
        echo "✅ 已从默认配置创建配置文件"
    fi
fi

# 创建 Cursor 配置目录
mkdir -p "$HOME/.cursor"

# 检查是否已有配置
if [ -f "$CURSOR_MCP_CONFIG" ]; then
    echo "⚠️  配置文件已存在: $CURSOR_MCP_CONFIG"
    echo "   将添加 mymcp 配置到现有文件中..."
    
    # 备份原配置
    cp "$CURSOR_MCP_CONFIG" "$CURSOR_MCP_CONFIG.backup"
    echo "✅ 已备份原配置到: $CURSOR_MCP_CONFIG.backup"
fi

# 创建或更新配置
echo ""
echo "📝 创建 Cursor MCP 配置..."

# 使用 Python 来安全地更新 JSON
python3 << EOF
import json
import os
from pathlib import Path

config_path = Path("$CURSOR_MCP_CONFIG")
project_dir = "$PROJECT_DIR"
config_file = "$CONFIG_FILE"

# 读取现有配置或创建新配置
if config_path.exists():
    with open(config_path, 'r') as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError:
            config = {}
else:
    config = {}

# 确保 mcpServers 存在
if "mcpServers" not in config:
    config["mcpServers"] = {}

# 添加 mymcp 配置
config["mcpServers"]["mymcp"] = {
    "command": "uvx",
    "args": [
        "mymcp",
        "--config",
        config_file
    ],
    "env": {
        "INTELLIJ_RUNCONTROL_TOKEN": os.getenv("INTELLIJ_RUNCONTROL_TOKEN", "")
    }
}

# 写入配置
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f"✅ 配置已写入: {config_path}")
EOF

echo ""
echo "✅ Cursor MCP 配置完成！"
echo ""
echo "📋 配置信息:"
echo "   - 配置文件: $CONFIG_FILE"
echo "   - Cursor MCP 配置: $CURSOR_MCP_CONFIG"
echo ""
echo "⚠️  重要提示:"
echo "   1. 如果使用 IntelliJ-RunControl，请设置环境变量:"
echo "      export INTELLIJ_RUNCONTROL_TOKEN='your_token'"
echo ""
echo "   2. 重启 Cursor 使配置生效"
echo ""
echo "   3. 在 Cursor 中测试，可以尝试:"
echo "      - '列出我的 IntelliJ 项目'"
echo "      - '列出运行配置'"
echo ""

