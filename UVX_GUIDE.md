# UVX 启动指南

## UVX 自动环境初始化

uvx 是 uv 工具的一部分，它会**自动处理**以下事项：

### 1. 虚拟环境管理
- ✅ 自动创建隔离的虚拟环境
- ✅ 环境位置：`~/.local/share/uv/tools/gradle-class-finder-mcp`
- ✅ 每个工具都有独立的环境，避免依赖冲突

### 2. 依赖安装
- ✅ 自动读取 `pyproject.toml` 中的依赖
- ✅ 自动安装所有必需的包（mcp, requests 等）
- ✅ 使用缓存加速后续启动

### 3. Python 解释器
- ✅ 自动选择合适的 Python 版本
- ✅ 如果系统 Python 不满足要求，会自动下载

## 启动命令

### 从本地目录启动
```bash
uvx --from /Users/erio/codes/mcps/gradle-class-finder-mcp gradle-class-finder-mcp
```

### 从 Git 仓库启动
```bash
uvx --from git+https://github.com/touwaeriol/gradle-class-finder-mcp.git gradle-class-finder-mcp
```

## Claude Desktop 配置

### 推荐配置（本地开发）
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

### 生产配置（从 GitHub）
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

## UVX 工作流程

1. **首次启动**：
   ```
   uvx 检测到新工具
   ↓
   创建虚拟环境
   ↓
   安装 Python 包和依赖
   ↓
   启动 MCP 服务器
   ```

2. **后续启动**：
   ```
   uvx 检测到已安装的工具
   ↓
   使用缓存的环境
   ↓
   直接启动 MCP 服务器（快速）
   ```

## 环境位置

uvx 创建的环境和缓存位于：

- **工具环境**: `~/.local/share/uv/tools/gradle-class-finder-mcp/`
- **Python 环境**: `~/.local/share/uv/python/`
- **包缓存**: `~/.cache/uv/`

## 优势

1. **零配置**：不需要手动创建虚拟环境
2. **隔离性**：每个工具独立环境
3. **可重现**：相同的命令总是产生相同的环境
4. **快速**：使用缓存，后续启动很快

## 故障排除

### 查看 uvx 工具列表
```bash
uv tool list
```

### 清理工具环境
```bash
uv tool uninstall gradle-class-finder-mcp
```

### 强制重新安装
```bash
uvx --refresh --from /path/to/project gradle-class-finder-mcp
```

### 查看详细日志
```bash
UV_DEBUG=1 uvx --from . gradle-class-finder-mcp
```

## 对比其他启动方式

| 特性 | uvx | python3 直接启动 | pip install |
|------|-----|-----------------|-------------|
| 自动创建环境 | ✅ | ❌ | ❌ |
| 依赖隔离 | ✅ | ❌ | ❌ |
| 无需手动安装 | ✅ | ❌ | ❌ |
| 启动速度 | 快（有缓存后） | 最快 | 快 |
| 维护难度 | 低 | 中 | 高 |

## 总结

使用 uvx 启动 MCP 服务是**推荐的方式**，因为它：
- 自动处理所有环境配置
- 确保依赖版本正确
- 避免污染系统 Python 环境
- 适合分发给最终用户