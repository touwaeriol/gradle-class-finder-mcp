# Gradle Class Finder MCP 使用指南

## 安装步骤

1. **安装依赖**
   ```bash
   cd gradle-class-finder-mcp
   pip install -r requirements.txt
   ```

2. **下载反编译器**
   ```bash
   python setup.py
   ```

3. **配置 MCP 客户端**
   
   在 Claude Desktop 的配置文件中添加：
   ```json
   {
     "mcpServers": {
       "gradle-class-finder": {
         "command": "python",
         "args": ["/path/to/gradle-class-finder-mcp/server.py"]
       }
     }
   }
   ```

## 使用示例

### 1. 查找类
```
使用 find_class 工具：
- workspace_dir: /path/to/your/gradle/project
- class_name: org.springframework.web.bind.annotation.RestController
```

### 2. 获取源代码
```
使用 get_source_code 工具：
- jar_path: /Users/xxx/.gradle/caches/modules-2/files-2.1/org.springframework/spring-web/5.3.9/xxx.jar
- class_name: org.springframework.web.bind.annotation.RestController
- line_start: 1 (可选)
- line_end: 50 (可选)
```

### 3. 获取元信息
```
使用 get_source_metadata 工具：
- jar_path: /path/to/dependency.jar
- class_name: com.example.MyClass
```

## 注意事项

1. **JDK 版本**：如果使用 jenv，确保设置了正确的 Java 版本
2. **Gradle 配置**：确保项目有 `gradlew` 或系统安装了 `gradle`
3. **依赖缓存**：首次运行可能需要下载项目依赖

## 故障排除

### CFR 下载失败
如果自动下载失败，可以手动下载：
1. 访问 https://www.benf.org/other/cfr/
2. 下载最新版本的 cfr.jar
3. 放置到 `~/.gradle-class-finder-mcp/cfr.jar`

### 找不到类
1. 确认类名拼写正确（使用全路径名）
2. 运行 `gradle dependencies` 确认依赖已下载
3. 检查 Gradle 缓存目录是否正确