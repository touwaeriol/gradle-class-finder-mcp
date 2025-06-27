# Gradle Class Finder MCP

A Model Context Protocol (MCP) server for finding and decompiling classes in Gradle project dependencies.

## Features

- 🔍 Find classes in Gradle dependencies (including transitive dependencies)
- 📦 Support for local source files, Maven dependencies, and flatDir repositories
- 🔧 Automatic Java decompilation using CFR
- 🚀 Self-contained with automatic JRE download
- 💻 Cross-platform (macOS, Linux, Windows)

## Installation

### Using uvx (Recommended)

```bash
uvx --from /path/to/gradle-class-finder-mcp gradle-class-finder-mcp
```

### Using Python directly

```bash
python3 server.py
```

## Configuration

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gradle-class-finder": {
      "command": "uvx",
      "args": [
        "--from",
        "/path/to/gradle-class-finder-mcp",
        "gradle-class-finder-mcp"
      ]
    }
  }
}
```

## Available Tools

### find_class
Find a class in Gradle project dependencies.

Parameters:
- `workspace_dir` (string, required): Path to the Gradle project root
- `class_name` (string, required): Fully qualified class name (e.g., `com.example.MyClass`)

### get_source_code
Get the decompiled source code of a class.

Parameters:
- `jar_path` (string, required): Full path to the JAR file
- `class_name` (string, required): Fully qualified class name
- `line_start` (integer, optional): Start line number
- `line_end` (integer, optional): End line number

### get_source_metadata
Get metadata about a class source code.

Parameters:
- `jar_path` (string, required): Full path to the JAR file
- `class_name` (string, required): Fully qualified class name

## How it Works

1. **Dependency Resolution**: Uses Gradle Tooling API to resolve all project dependencies
2. **Class Search**: Searches through local sources, Maven dependencies, and flatDir repositories
3. **Source Extraction**: Extracts source from `-sources.jar` files when available
4. **Decompilation**: Falls back to CFR decompiler for classes without source
5. **Priority**: Local sources > flatDir JARs > Maven dependencies

## Requirements

- Python 3.8+
- Java 17+ (automatically downloaded if not present)
- Network connection (for first-time JRE download)

## License

MIT License