# Gradle Class Finder MCP 配置指南

## 配置文件位置

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

## 启动方式

### 方式 1：uvx 本地启动（推荐开发使用）

```json
{
  "mcpServers": {
    "gradle-class-finder": {
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

### 方式 2：Python 直接启动（最稳定）

```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "python3",
      "args": [
        "/Users/erio/codes/mcps/gradle-class-finder-mcp/server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### 方式 3：uvx GitHub 启动（生产使用）

```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/touwaeriol/gradle-class-finder-mcp.git",
        "gradle-class-finder-mcp"
      ]
    }
  }
}
```

## 完整配置示例

这是一个包含多个 MCP 服务的完整配置示例：

```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "python3",
      "args": [
        "/Users/erio/codes/mcps/gradle-class-finder-mcp/server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/erio/codes"
      ]
    },
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your-token-here"
      }
    }
  }
}
```

## 验证配置

1. 保存配置文件
2. 完全退出 Claude Desktop（macOS: Cmd+Q，Windows: Alt+F4）
3. 重新启动 Claude Desktop
4. 在对话中测试：

```
使用 gradle-class-finder 的 find_class 工具查找类 org.springframework.boot.SpringApplication，
项目路径是 /path/to/your/gradle/project
```

## 故障排除

### 检查 MCP 是否加载

在 Claude 对话中输入：
```
列出所有可用的 MCP 工具
```

### 查看日志

- **macOS**: 
  ```bash
  tail -f ~/Library/Logs/Claude/mcp*.log
  ```

- **Windows**: 
  ```
  Get-Content "$env:LOCALAPPDATA\Claude\logs\mcp*.log" -Tail 50 -Wait
  ```

### 常见问题

1. **"MCP server failed to start"**
   - 检查 Python 3.8+ 是否安装
   - 检查路径是否正确
   - 尝试在终端手动运行命令

2. **"Tool not found"**
   - 确认配置文件已保存
   - 确认 Claude Desktop 已重启
   - 检查 MCP 服务名称是否正确

3. **性能问题**
   - 首次运行会下载 JRE，需要等待
   - 大型项目首次分析可能需要较长时间

## 环境变量

可选的环境变量：

```json
{
  "env": {
    "PYTHONUNBUFFERED": "1",
    "GRADLE_CLASS_FINDER_LOG_LEVEL": "DEBUG",
    "JAVA_HOME": "/path/to/java17"
  }
}
```