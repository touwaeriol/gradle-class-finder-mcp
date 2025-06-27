# 安装指南

## 1. 复制配置到 Claude Desktop

**macOS**:
```bash
cp claude_desktop_config_final.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Windows**:
```cmd
copy claude_desktop_config_final.json %APPDATA%\Claude\claude_desktop_config.json
```

## 2. 重启 Claude Desktop

完全退出并重新启动 Claude Desktop。

## 3. 验证安装

在 Claude 中输入：
```
列出所有可用的 MCP 工具
```

应该能看到：
- find_class
- get_source_code
- get_source_metadata

## 故障排除

### 如果 uvx 启动失败

1. 确保项目路径正确
2. 确保 README.md 文件存在
3. 检查 Python 版本 >= 3.8

### 查看日志

**macOS**:
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

### 清理 uvx 缓存

如果需要重新安装：
```bash
uv tool uninstall gradle-class-finder-mcp
rm -rf ~/.cache/uv/archive-v0/
```

### 使用 Python 直接启动（备选）

如果 uvx 有问题，可以使用：
```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "python3",
      "args": [
        "/Users/erio/codes/mcps/gradle-class-finder-mcp/server.py"
      ]
    }
  }
}
```