#!/bin/bash

# Gradle Class Finder MCP Server 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAR_FILE="$SCRIPT_DIR/build/libs/gradle-class-finder-mcp.jar"

# 检查JAR文件是否存在
if [ ! -f "$JAR_FILE" ]; then
    echo "错误: JAR文件不存在: $JAR_FILE"
    echo "请先运行构建命令: ./gradlew clean shadowJar"
    exit 1
fi

# 检查Java版本
if ! command -v java &> /dev/null; then
    echo "错误: 未找到Java命令。请确保已安装Java 17+。"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | awk -F '"' '{print $2}' | awk -F '.' '{print $1}')
if [ "$JAVA_VERSION" -lt 17 ]; then
    echo "错误: 需要Java 17或更高版本。当前版本: $JAVA_VERSION"
    exit 1
fi

echo "启动 Gradle Class Finder MCP Server..."
echo "JAR文件: $JAR_FILE"
echo "Java版本: $(java -version 2>&1 | head -n 1)"
echo ""

# 启动MCP服务器
exec java -jar "$JAR_FILE" "$@"