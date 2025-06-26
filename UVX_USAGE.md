# UVX 启动配置

## 1. 直接从 GitHub 运行（推荐）

```bash
# 一次性运行
uvx --from git+https://github.com/touwaeriol/gradle-class-finder-mcp.git gradle-class-finder-mcp

# 或者使用简短命令
uvx gradle-class-finder-mcp
```

## 2. Claude Desktop 配置

在 Claude Desktop 配置文件中添加：

```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "uvx",
      "args": ["gradle-class-finder-mcp"]
    }
  }
}
```

## 3. 从本地目录运行（开发时使用）

```bash
# 在项目目录下
uvx --from . gradle-class-finder-mcp
```

### Claude Desktop 本地开发配置

```json
{
  "mcpServers": {
    "gradle-class-finder-local": {
      "command": "uvx",
      "args": [
        "--from",
        "/Users/erio/codes/mcps/gradle-class-finder-mcp",
        "gradle-class-finder-mcp"
      ]
    }
  }
}
```

## 4. 使用 uv 工具安装后运行

```bash
# 全局安装
uv tool install gradle-class-finder-mcp

# 然后直接运行
gradle-class-finder-mcp
```

## 5. 特性说明

- **自动下载 JRE**：首次运行时会自动下载合适的 Java 运行环境
- **无需配置 JAVA_HOME**：完全自包含，不依赖系统 Java
- **跨平台支持**：自动适配 Windows/macOS/Linux

## 配置文件位置

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

## 验证安装

重启 Claude Desktop 后，可以通过以下方式验证：
1. 在 Claude 中输入："帮我查找类 java.util.ArrayList"
2. 如果配置正确，Claude 会自动调用 MCP 工具

## 故障排除

### 问题：uvx 命令未找到
```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 问题：找不到包
```bash
# 确保已发布到 PyPI 或使用 git URL
uvx --from git+https://github.com/touwaeriol/gradle-class-finder-mcp.git gradle-class-finder-mcp
```

### 问题：首次运行下载 JRE
```bash
# 首次运行会自动下载 JRE（约 40-50MB）
# 下载完成后会保存在项目的 .java_runtime 目录
# 后续运行会直接使用已下载的 JRE
```