# Gradle Class Finder MCP

基于Model Context Protocol (MCP)的Gradle类查找服务器，用于在Gradle项目依赖中查找和反编译Java类。

## 特性

- 🔍 在Gradle依赖中查找类（包括传递依赖）
- 📦 支持本地源文件、Maven依赖和flatDir仓库
- 🔧 使用CFR自动Java反编译
- ☕ 纯Java实现，仅依赖Java环境
- 💻 跨平台支持（macOS、Linux、Windows）
- 🚀 标准输入输出流通信

## 要求

- Java 17+
- Gradle项目

## 构建和安装

### 构建项目

```bash
./gradlew clean shadowJar
```

### 运行服务器

```bash
java -jar build/libs/gradle-class-finder-mcp.jar
```

## Claude Desktop配置

将以下配置添加到Claude Desktop配置文件：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "java",
      "args": [
        "-jar",
        "/path/to/gradle-class-finder-mcp/build/libs/gradle-class-finder-mcp.jar"
      ]
    }
  }
}
```

## 可用工具

### find_class
在Gradle项目依赖中查找指定类

参数:
- `workspace_dir` (string, 必需): Gradle项目根目录路径
- `class_name` (string, 必需): 类的全限定名 (例如: `com.example.MyClass`)
- `submodule_path` (string, 可选): 子模块路径

### get_source_code
获取指定类的源代码或反编译代码

参数:
- `jar_path` (string, 必需): JAR文件的完整路径
- `class_name` (string, 必需): 类的全限定名
- `line_start` (integer, 可选): 起始行号
- `line_end` (integer, 可选): 结束行号

## 工作原理

1. **依赖解析**: 使用Gradle Tooling API解析所有项目依赖
2. **类搜索**: 在本地源码、Maven依赖和flatDir仓库中搜索
3. **源码提取**: 优先从`-sources.jar`文件中提取源码
4. **代码反编译**: 源码不可用时使用CFR反编译器
5. **优先级**: 本地源码 > flatDir JAR > Maven依赖

## 架构设计

### 纯Java实现
- **MCP服务器**: 使用官方`io.modelcontextprotocol.sdk:mcp` Java SDK
- **类查找服务**: 基于Gradle Tooling API的类搜索功能
- **源码服务**: 支持源码提取和CFR反编译
- **标准IO通信**: 通过stdin/stdout进行MCP协议通信

### 模块化设计
- `GradleClassFinderMcpServer`: MCP协议服务器主类
- `ClassFinderService`: 类查找核心逻辑
- `SourceCodeService`: 源码获取和反编译服务

## 使用示例

1. **查找类**:
   ```json
   {
     "method": "tools/call",
     "params": {
       "name": "find_class",
       "arguments": {
         "workspace_dir": "/path/to/gradle/project",
         "class_name": "org.springframework.boot.SpringApplication"
       }
     }
   }
   ```

2. **获取源码**:
   ```json
   {
     "method": "tools/call",
     "params": {
       "name": "get_source_code",
       "arguments": {
         "jar_path": "/path/to/spring-boot.jar",
         "class_name": "org.springframework.boot.SpringApplication",
         "line_start": 1,
         "line_end": 50
       }
     }
   }
   ```

## 许可证

MIT License