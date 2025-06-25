#!/bin/bash

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed."
    exit 1
fi

# 检查是否安装了依赖
if ! python3 -c "import mcp" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
fi

# 检查CFR是否存在
CFR_PATH="$HOME/.gradle-class-finder-mcp/cfr.jar"
if [ ! -f "$CFR_PATH" ]; then
    echo "Setting up CFR decompiler..."
    python3 "$SCRIPT_DIR/setup.py"
fi

# 运行MCP服务
exec python3 "$SCRIPT_DIR/server.py"