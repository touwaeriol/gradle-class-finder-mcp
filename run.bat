@echo off
REM Gradle Class Finder MCP Server 启动脚本 (Windows)

setlocal

set SCRIPT_DIR=%~dp0
set JAR_FILE=%SCRIPT_DIR%build\libs\gradle-class-finder-mcp.jar

REM 检查JAR文件是否存在
if not exist "%JAR_FILE%" (
    echo 错误: JAR文件不存在: %JAR_FILE%
    echo 请先运行构建命令: gradlew.bat clean shadowJar
    exit /b 1
)

REM 检查Java版本
java -version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Java命令。请确保已安装Java 17+。
    exit /b 1
)

echo 启动 Gradle Class Finder MCP Server...
echo JAR文件: %JAR_FILE%
java -version
echo.

REM 启动MCP服务器
java -jar "%JAR_FILE%" %*