# Claude Desktop MCP 配置示例

## 配置文件位置

### macOS
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Windows  
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Linux
```
~/.config/Claude/claude_desktop_config.json
```

## 基本配置

### 1. 使用绝对路径（推荐）
```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "java",
      "args": [
        "-jar",
        "/Users/username/gradle-class-finder-mcp/build/libs/gradle-class-finder-mcp.jar"
      ]
    }
  }
}
```

### 2. 使用启动脚本
```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "/Users/username/gradle-class-finder-mcp/run.sh"
    }
  }
}
```

### 3. 指定Java环境（如果系统默认不是Java 17+）
```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "/usr/lib/jvm/java-17-openjdk/bin/java",
      "args": [
        "-jar",
        "/path/to/gradle-class-finder-mcp/build/libs/gradle-class-finder-mcp.jar"
      ]
    }
  }
}
```

### 4. 使用环境变量
```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "java",
      "args": [
        "-jar",
        "/path/to/gradle-class-finder-mcp/build/libs/gradle-class-finder-mcp.jar"
      ],
      "env": {
        "JAVA_HOME": "/usr/lib/jvm/java-17-openjdk",
        "PATH": "/usr/lib/jvm/java-17-openjdk/bin:${PATH}"
      }
    }
  }
}
```

### 5. 带JVM参数的配置
```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "java",
      "args": [
        "-Xmx512m",
        "-Dfile.encoding=UTF-8",
        "-jar",
        "/path/to/gradle-class-finder-mcp/build/libs/gradle-class-finder-mcp.jar"
      ]
    }
  }
}
```

## Windows特定配置

### 使用PowerShell启动
```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "powershell",
      "args": [
        "-Command",
        "java -jar 'C:\\path\\to\\gradle-class-finder-mcp\\build\\libs\\gradle-class-finder-mcp.jar'"
      ]
    }
  }
}
```

### 使用批处理文件
```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "C:\\path\\to\\gradle-class-finder-mcp\\run.bat"
    }
  }
}
```

## 开发/调试配置

### 带调试日志
```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "java",
      "args": [
        "-Dlogging.level.root=DEBUG",
        "-jar",
        "/path/to/gradle-class-finder-mcp/build/libs/gradle-class-finder-mcp.jar"
      ]
    }
  }
}
```

### 指定工作目录
```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "java",
      "args": [
        "-jar",
        "/path/to/gradle-class-finder-mcp/build/libs/gradle-class-finder-mcp.jar"
      ],
      "cwd": "/path/to/gradle-class-finder-mcp"
    }
  }
}
```

## 多实例配置

如果需要为不同项目类型配置多个实例：

```json
{
  "mcpServers": {
    "gradle-class-finder-java": {
      "command": "java",
      "args": [
        "-jar",
        "/path/to/gradle-class-finder-mcp/build/libs/gradle-class-finder-mcp.jar"
      ]
    },
    "gradle-class-finder-android": {
      "command": "java",
      "args": [
        "-jar",
        "/path/to/gradle-class-finder-mcp/build/libs/gradle-class-finder-mcp.jar"
      ]
    }
  }
}
```

## 故障排查

### 1. Java版本检查
确保使用Java 17或更高版本：
```bash
java -version
```

### 2. JAR文件路径检查
确保路径正确且文件存在：
```bash
ls -la /path/to/gradle-class-finder-mcp/build/libs/gradle-class-finder-mcp.jar
```

### 3. 权限检查
确保JAR文件有执行权限：
```bash
chmod +x /path/to/gradle-class-finder-mcp/build/libs/gradle-class-finder-mcp.jar
```

### 4. 测试启动
手动测试MCP服务器启动：
```bash
java -jar /path/to/gradle-class-finder-mcp/build/libs/gradle-class-finder-mcp.jar
```

应该看到类似输出：
```
Gradle Class Finder MCP Server 启动完成，正在监听stdin/stdout
服务器信息: gradle-class-finder v1.0.0
支持的工具: find_class, get_source_code
```