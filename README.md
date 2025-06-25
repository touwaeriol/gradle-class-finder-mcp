# Gradle Class Finder MCP

一个用于在 Gradle 项目依赖中查找类并提供反编译功能的 MCP 服务。

## 功能特性

- 在 Gradle 项目的依赖库中查找指定的类
- 返回类所在的依赖信息（依赖名、版本、路径）
- 提供 Java 类的反编译源代码
- 支持获取部分源代码（指定行范围）
- 提供源代码元信息（长度、方法列表等）

## 使用方法

通过 nvx 启动：
```bash
nvx gradle-class-finder
```

## MCP 方法

1. **find_class**
   - 参数：workspace_dir（Gradle项目目录）、class_name（全路径类名）
   - 返回：包含该类的依赖列表

2. **get_source_code**
   - 参数：dependency（依赖名）、version（版本）、class_name（类名）、line_start（可选）、line_end（可选）
   - 返回：反编译的源代码

3. **get_source_metadata**
   - 参数：dependency（依赖名）、version（版本）、class_name（类名）
   - 返回：源代码元信息（行数、方法列表等）