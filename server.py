#!/usr/bin/env python3

import platform
import os
import subprocess
import json
import shutil
import requests
import zipfile
import tarfile
from typing import Any
import logging

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants ---
HELPER_JAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "java_helper", "helper.jar")
CFR_JAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib", "cfr-0.152.jar")

# Create server instance
server = Server("gradle-class-finder")

# --- Java Environment Management ---
def find_java_executable():
    """Find Java executable from system JDK/JRE."""
    logger.info("Looking for system Java/JDK installation...")
    
    # Method 1: Check 'which java' command
    try:
        result = subprocess.run(["which", "java"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            java_path = result.stdout.strip()
            if check_java_version(java_path):
                logger.info(f"Found Java at: {java_path}")
                return java_path
    except Exception as e:
        logger.debug(f"'which java' failed: {e}")
    
    # Method 2: Check java command directly in PATH
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            if check_java_version("java"):
                logger.info("Using 'java' command from PATH")
                return "java"
    except Exception as e:
        logger.debug(f"'java -version' failed: {e}")
    
    # Method 3: Check JAVA_HOME environment variable
    java_home = os.environ.get('JAVA_HOME')
    if java_home:
        system = platform.system().lower()
        java_exe = os.path.join(java_home, "bin", "java.exe" if system.startswith("win") else "java")
        if os.path.exists(java_exe) and check_java_version(java_exe):
            logger.info(f"Found Java from JAVA_HOME: {java_exe}")
            return java_exe
    
    # Method 4: Check common JDK installation paths
    system = platform.system().lower()
    common_paths = []
    
    if system == "darwin":
        # macOS common paths
        common_paths.extend([
            "/usr/bin/java",
            "/System/Library/Frameworks/JavaVM.framework/Versions/Current/Commands/java",
        ])
        # Check installed JDKs
        jvm_dir = "/Library/Java/JavaVirtualMachines"
        if os.path.exists(jvm_dir):
            for jdk in os.listdir(jvm_dir):
                java_path = os.path.join(jvm_dir, jdk, "Contents", "Home", "bin", "java")
                if os.path.exists(java_path):
                    common_paths.append(java_path)
                    
    elif system == "linux":
        # Linux common paths
        common_paths.extend([
            "/usr/bin/java",
            "/usr/lib/jvm/default-java/bin/java",
        ])
        # Check /usr/lib/jvm for installed JDKs
        jvm_dir = "/usr/lib/jvm"
        if os.path.exists(jvm_dir):
            for jdk in os.listdir(jvm_dir):
                java_path = os.path.join(jvm_dir, jdk, "bin", "java")
                if os.path.exists(java_path):
                    common_paths.append(java_path)
                    
    elif system.startswith("win"):
        # Windows common paths
        program_files = [
            "C:\\Program Files\\Java",
            "C:\\Program Files (x86)\\Java"
        ]
        for pf in program_files:
            if os.path.exists(pf):
                for jdk in os.listdir(pf):
                    java_path = os.path.join(pf, jdk, "bin", "java.exe")
                    if os.path.exists(java_path):
                        common_paths.append(java_path)
    
    # Test common paths
    for java_path in common_paths:
        if os.path.exists(java_path) and check_java_version(java_path):
            logger.info(f"Found Java at: {java_path}")
            return java_path
    
    raise Exception("No suitable Java installation found. Please install JDK 8 or higher and ensure 'java' is in your PATH or set JAVA_HOME environment variable.")

def check_java_version(java_cmd):
    """Check if Java version is suitable (8 or higher)."""
    try:
        result = subprocess.run([java_cmd, "-version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_output = result.stderr or result.stdout
            logger.debug(f"Java version output: {version_output}")
            
            # Look for version pattern like "1.8.0", "11.0.1", "17.0.1", etc.
            import re
            # Handle both old format (1.8.0_xxx) and new format (11.0.x, 17.0.x)
            version_patterns = [
                r'version "1\.(\d+)\.', # Old format: 1.8.0_xxx
                r'version "(\d+)\.', # New format: 11.0.x, 17.0.x
            ]
            
            for pattern in version_patterns:
                version_match = re.search(pattern, version_output)
                if version_match:
                    major_version = int(version_match.group(1))
                    # For old format (1.8), version 8 is minimum
                    # For new format (11, 17), version 8+ is minimum
                    if pattern.startswith(r'version "1\.'):
                        suitable = major_version >= 8
                    else:
                        suitable = major_version >= 8
                    
                    logger.debug(f"Java major version: {major_version}, suitable: {suitable}")
                    return suitable
            
            logger.warning(f"Could not parse Java version from: {version_output}")
            return False
    except Exception as e:
        logger.debug(f"Failed to check Java version for {java_cmd}: {e}")
        return False

# --- Main Logic ---
def find_class_source(project_path, class_name, submodule_path=None):
    java_exe = find_java_executable()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    helper_jar = os.path.join(base_dir, "build", "libs", "gradle-class-finder-helper.jar")
    if os.path.exists(helper_jar):
        helper_cmd = [java_exe, "-jar", helper_jar, project_path, class_name]
    else:
        build_classes_dir = os.path.join(base_dir, "build", "classes", "java", "main")
        dependencies_dir = os.path.join(base_dir, "build", "dependencies")
        
        classpath_elements = [build_classes_dir]
        if os.path.exists(dependencies_dir):
            classpath_elements.extend([os.path.join(dependencies_dir, f) for f in os.listdir(dependencies_dir) if f.endswith(".jar")])
        
        classpath = os.pathsep.join(classpath_elements)
        helper_cmd = [java_exe, "-cp", classpath, "com.open_care.ClassFinder", project_path, class_name]
    
    if submodule_path:
        helper_cmd.append(submodule_path)
    
    logger.debug(f"Running helper.jar: {' '.join(helper_cmd)}")
    try:
        helper_process = subprocess.run(helper_cmd, capture_output=True, text=True, check=True)
        output = helper_process.stdout.strip()
        
        try:
            all_results = json.loads(output)
        except json.JSONDecodeError:
            stderr_output = helper_process.stderr.strip()
            return {"status": "error", "message": f"Failed to parse helper output: {output[:100]}... stderr: {stderr_output}", "matches": []}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Failed to get dependency info from Gradle project.", "matches": []}
    
    final_results = []
    
    for result in all_results:
        jar_path = result.get("jarPath", "")
        source_jar_path = result.get("sourceJarPath", jar_path)
        dependency_coordinates = result.get("dependencyCoordinates", "")
        found_class_name = result.get("className", class_name)
        is_local = result.get("isLocal", False)
        
        source_code = None
        source_type = ""
        
        if is_local and jar_path.endswith(".java"):
            source_type = "local_source"
        elif source_jar_path and source_jar_path != jar_path and os.path.exists(source_jar_path):
            try:
                with zipfile.ZipFile(source_jar_path, 'r') as zip_ref:
                    source_entry_name = class_name.replace('.', '/') + ".java"
                    found_source_entry = None
                    for entry in zip_ref.namelist():
                        if entry.endswith(source_entry_name):
                            found_source_entry = entry
                            break
                    
                    if found_source_entry:
                        with zip_ref.open(found_source_entry) as source_file:
                            source_code = source_file.read().decode('utf-8')
                        source_type = "source"
            except Exception as e:
                logger.warning(f"Error extracting source from {source_jar_path}: {e}")
        
        if source_code is None:
            source_type = "decompiled"
        
        final_results.append({
            "source_type": source_type,
            "jar_path": jar_path,
            "source_jar_path": source_jar_path,
            "dependency_coordinates": dependency_coordinates,
            "class_name": found_class_name
        })
    
    if not final_results:
        return {"status": "error", "message": f"Class '{class_name}' not found in any dependency.", "matches": []}
    
    return {"status": "success", "matches": final_results}

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
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
        types.Tool(
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
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool calls."""
    
    if name == "find_class":
        result = find_class_source(
            arguments["workspace_dir"],
            arguments["class_name"]
        )
        
        if result["status"] == "success":
            matches = result["matches"]
            content = f"Found {len(matches)} occurrence(s) of {arguments['class_name']}:\n\n"
            for match in matches:
                content += f"- Dependency: {match['dependency_coordinates']}\n"
                content += f"  JAR Path: {match['jar_path']}\n"
                if match.get('source_jar_path'):
                    content += f"  Source JAR: {match['source_jar_path']}\n"
                content += "\n"
        else:
            content = result["message"]
        
        return [types.TextContent(type="text", text=content)]
    
    elif name == "get_source_code":
        jar_path = arguments["jar_path"]
        class_name = arguments["class_name"]
        line_start = arguments.get("line_start")
        line_end = arguments.get("line_end")
        
        # Get source code
        java_exe = find_java_executable()
        source_code = None
        
        # Check if it's a local Java file
        if jar_path.endswith(".java") and os.path.exists(jar_path):
            try:
                with open(jar_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                    if line_start is not None and line_end is not None:
                        lines = source_code.split('\n')
                        source_code = '\n'.join(lines[line_start-1:line_end])
            except Exception as e:
                source_code = f"// Error reading local source: {e}"
        else:
            # Decompile using CFR
            decompile_cmd = [
                java_exe,
                "-jar", CFR_JAR_PATH,
                jar_path,
                class_name
            ]
            try:
                decompile_process = subprocess.run(decompile_cmd, capture_output=True, text=True, check=True)
                source_code = decompile_process.stdout
                
                if line_start is not None and line_end is not None:
                    lines = source_code.split('\n')
                    source_code = '\n'.join(lines[line_start-1:line_end])
            except subprocess.CalledProcessError as e:
                source_code = f"// Failed to decompile {class_name}: {e.stderr}"
        
        return [types.TextContent(type="text", text=source_code)]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

def run():
    """Entry point for uvx/pip install."""
    import asyncio
    import sys
    
    # Suppress event loop warnings
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")
    
    # Pre-check Java environment on startup
    try:
        java_exe = find_java_executable()
        logger.info(f"Java environment verified: {java_exe}")
    except Exception as e:
        logger.error(f"Java environment check failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run()