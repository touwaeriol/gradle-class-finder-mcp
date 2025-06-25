#!/usr/bin/env python3

import os
import subprocess
import json
import zipfile
import tempfile
import shutil
import struct
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import asyncio
import mcp
from mcp.server import Server
from mcp.types import TextContent, Tool, CallToolResult

# 创建MCP服务器实例
server = Server("gradle-class-finder")

class GradleClassFinder:
    def __init__(self):
        self.cfr_path = None
        self._setup_decompiler()
    
    def _setup_decompiler(self):
        """下载并设置CFR反编译器"""
        cache_dir = Path.home() / ".gradle-class-finder-mcp"
        cache_dir.mkdir(exist_ok=True)
        self.cfr_path = cache_dir / "cfr.jar"
        
        if not self.cfr_path.exists():
            # TODO: 下载CFR
            pass
    
    def _run_gradle_command(self, workspace_dir: str, command: str) -> str:
        """运行Gradle命令"""
        try:
            # 检查是否需要使用jenv
            jenv_check = subprocess.run(["which", "jenv"], capture_output=True, text=True)
            if jenv_check.returncode == 0:
                # 设置Java版本
                subprocess.run(["jenv", "local", "11"], cwd=workspace_dir, capture_output=True)
            
            # 运行Gradle命令
            gradle_cmd = "./gradlew" if os.path.exists(os.path.join(workspace_dir, "gradlew")) else "gradle"
            result = subprocess.run(
                [gradle_cmd] + command.split(),
                cwd=workspace_dir,
                capture_output=True,
                text=True
            )
            return result.stdout
        except Exception as e:
            return str(e)
    
    def get_dependencies(self, workspace_dir: str) -> List[Dict[str, str]]:
        """获取项目的所有依赖"""
        output = self._run_gradle_command(workspace_dir, "dependencies --configuration compileClasspath")
        dependencies = []
        
        # 解析依赖输出
        lines = output.split('\n')
        for line in lines:
            if '---' in line and ':' in line:
                # 提取依赖信息
                parts = line.split('---')[-1].strip()
                if ' -> ' in parts:
                    parts = parts.split(' -> ')[0]
                
                if ':' in parts:
                    components = parts.split(':')
                    if len(components) >= 3:
                        group, artifact, version = components[0], components[1], components[-1]
                        dependencies.append({
                            'group': group,
                            'artifact': artifact,
                            'version': version.split(' ')[0],  # 去除额外信息
                            'full_name': f"{group}:{artifact}:{version.split(' ')[0]}"
                        })
        
        return dependencies
    
    def find_gradle_cache_path(self) -> Path:
        """查找Gradle缓存目录"""
        gradle_home = os.environ.get('GRADLE_USER_HOME', str(Path.home() / '.gradle'))
        return Path(gradle_home) / 'caches' / 'modules-2' / 'files-2.1'
    
    def find_class_in_dependencies(self, workspace_dir: str, class_name: str) -> List[Dict[str, str]]:
        """在依赖中查找类"""
        dependencies = self.get_dependencies(workspace_dir)
        gradle_cache = self.find_gradle_cache_path()
        results = []
        
        # 将类名转换为路径格式
        class_path = class_name.replace('.', '/') + '.class'
        
        for dep in dependencies:
            # 在Gradle缓存中查找JAR文件
            dep_path = gradle_cache / dep['group'] / dep['artifact'] / dep['version']
            
            if dep_path.exists():
                # 查找所有JAR文件
                for jar_file in dep_path.rglob('*.jar'):
                    try:
                        with zipfile.ZipFile(jar_file, 'r') as zf:
                            if class_path in zf.namelist():
                                results.append({
                                    'dependency': dep['full_name'],
                                    'group': dep['group'],
                                    'artifact': dep['artifact'],
                                    'version': dep['version'],
                                    'jar_path': str(jar_file),
                                    'class_path': class_path
                                })
                    except Exception:
                        continue
        
        return results
    
    def decompile_class(self, jar_path: str, class_name: str, 
                       line_start: Optional[int] = None, 
                       line_end: Optional[int] = None) -> str:
        """反编译类文件"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # 提取class文件
                class_path = class_name.replace('.', '/') + '.class'
                
                with zipfile.ZipFile(jar_path, 'r') as zf:
                    zf.extract(class_path, temp_dir)
                
                # 使用CFR反编译
                output_file = os.path.join(temp_dir, 'decompiled.java')
                cmd = [
                    'java', '-jar', str(self.cfr_path),
                    os.path.join(temp_dir, class_path),
                    '--outputfile', output_file
                ]
                
                subprocess.run(cmd, capture_output=True)
                
                if os.path.exists(output_file):
                    with open(output_file, 'r') as f:
                        source_code = f.read()
                    
                    # 如果指定了行范围，返回部分代码
                    if line_start is not None and line_end is not None:
                        lines = source_code.split('\n')
                        return '\n'.join(lines[line_start-1:line_end])
                    
                    return source_code
                else:
                    # 如果CFR不可用，使用javap作为备选
                    result = subprocess.run(
                        ['javap', '-c', '-p', class_name],
                        classpath=jar_path,
                        capture_output=True,
                        text=True
                    )
                    return result.stdout
        except Exception as e:
            return f"Error decompiling: {str(e)}"
    
    def get_class_metadata(self, jar_path: str, class_name: str) -> Dict[str, any]:
        """获取类的元信息"""
        source_code = self.decompile_class(jar_path, class_name)
        lines = source_code.split('\n')
        
        # 简单的方法提取
        methods = []
        for i, line in enumerate(lines):
            line = line.strip()
            if ('public' in line or 'private' in line or 'protected' in line) and '(' in line and ')' in line:
                if '{' in line or ';' in line:
                    methods.append({
                        'line': i + 1,
                        'signature': line.split('{')[0].strip() if '{' in line else line.split(';')[0].strip()
                    })
        
        return {
            'total_lines': len(lines),
            'size_bytes': len(source_code.encode('utf-8')),
            'methods_count': len(methods),
            'methods': methods
        }

# 创建全局实例
finder = GradleClassFinder()

# 定义MCP工具
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="find_class",
            description="在Gradle项目依赖中查找指定的类",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_dir": {
                        "type": "string",
                        "description": "Gradle项目的根目录路径"
                    },
                    "class_name": {
                        "type": "string",
                        "description": "要查找的类的全路径名，如: com.example.MyClass"
                    }
                },
                "required": ["workspace_dir", "class_name"]
            }
        ),
        Tool(
            name="get_source_code",
            description="获取类的反编译源代码",
            inputSchema={
                "type": "object",
                "properties": {
                    "jar_path": {
                        "type": "string",
                        "description": "JAR文件的完整路径"
                    },
                    "class_name": {
                        "type": "string",
                        "description": "类的全路径名"
                    },
                    "line_start": {
                        "type": "integer",
                        "description": "起始行号（可选）"
                    },
                    "line_end": {
                        "type": "integer",
                        "description": "结束行号（可选）"
                    }
                },
                "required": ["jar_path", "class_name"]
            }
        ),
        Tool(
            name="get_source_metadata",
            description="获取类源代码的元信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "jar_path": {
                        "type": "string",
                        "description": "JAR文件的完整路径"
                    },
                    "class_name": {
                        "type": "string",
                        "description": "类的全路径名"
                    }
                },
                "required": ["jar_path", "class_name"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    try:
        if name == "find_class":
            results = finder.find_class_in_dependencies(
                arguments["workspace_dir"],
                arguments["class_name"]
            )
            
            if results:
                content = f"Found {len(results)} occurrence(s) of {arguments['class_name']}:\n\n"
                for result in results:
                    content += f"- Dependency: {result['dependency']}\n"
                    content += f"  JAR Path: {result['jar_path']}\n\n"
            else:
                content = f"Class {arguments['class_name']} not found in dependencies"
            
            return CallToolResult(content=[TextContent(text=content)])
        
        elif name == "get_source_code":
            source_code = finder.decompile_class(
                arguments["jar_path"],
                arguments["class_name"],
                arguments.get("line_start"),
                arguments.get("line_end")
            )
            
            return CallToolResult(content=[TextContent(text=source_code)])
        
        elif name == "get_source_metadata":
            metadata = finder.get_class_metadata(
                arguments["jar_path"],
                arguments["class_name"]
            )
            
            content = json.dumps(metadata, indent=2)
            return CallToolResult(content=[TextContent(text=content)])
        
        else:
            return CallToolResult(
                content=[TextContent(text=f"Unknown tool: {name}")],
                isError=True
            )
    
    except Exception as e:
        return CallToolResult(
            content=[TextContent(text=f"Error: {str(e)}")],
            isError=True
        )

# 主函数
async def amain():
    async with mcp.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

def main():
    """Entry point for uvx/pip install"""
    asyncio.run(amain())

if __name__ == "__main__":
    main()