#!/usr/bin/env python3

import platform
import os
import subprocess
import json
import shutil
import requests
import zipfile
import tarfile
import asyncio
from typing import List, Dict, Optional
import logging

import mcp
import mcp.server.stdio
from mcp.server import Server
from mcp.types import TextContent, Tool, CallToolResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constants ---
JRE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".java_runtime")
HELPER_JAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "java_helper", "helper.jar")
CFR_JAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "decompilers", "cfr.jar")

# Adoptium Temurin 17 LTS (most compatible for Gradle Tooling API)
JRE_DOWNLOAD_URLS = {
    "linux": {
        "x86_64": "https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jre/hotspot/normal/eclipse?project=jdk",
        "aarch64": "https://api.adoptium.net/v3/binary/latest/17/ga/linux/aarch64/jre/hotspot/normal/eclipse?project=jdk"
    },
    "darwin": {
        "x86_64": "https://api.adoptium.net/v3/binary/latest/17/ga/mac/x64/jre/hotspot/normal/eclipse?project=jdk",
        "aarch64": "https://api.adoptium.net/v3/binary/latest/17/ga/mac/aarch64/jre/hotspot/normal/eclipse?project=jdk"
    },
    "windows": {
        "x86_64": "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jre/hotspot/normal/eclipse?project=jdk"
    }
}

# --- JRE Management ---
def ensure_jre_available():
    # Find the actual extracted JRE directory
    extracted_jre_path = None
    if os.path.exists(JRE_DIR):
        for item in os.listdir(JRE_DIR):
            full_path = os.path.join(JRE_DIR, item)
            if os.path.isdir(full_path) and ("jdk" in item.lower() or "jre" in item.lower()):
                extracted_jre_path = full_path
                break

    java_exe_path = None
    if extracted_jre_path:
        if platform.system() == "Windows":
            java_exe_path = os.path.join(extracted_jre_path, "bin", "java.exe")
        elif platform.system() == "Darwin":
            java_exe_path = os.path.join(extracted_jre_path, "Contents", "Home", "bin", "java")
        else: # Linux
            java_exe_path = os.path.join(extracted_jre_path, "bin", "java")

    if java_exe_path and os.path.exists(java_exe_path) and os.path.isfile(java_exe_path) and os.access(java_exe_path, os.X_OK):
        logger.info(f"JRE already available at {java_exe_path}")
        return java_exe_path

    logger.info(f"JRE not found or not executable. Attempting to download to {JRE_DIR}...")
    os.makedirs(JRE_DIR, exist_ok=True)

    system = platform.system().lower()
    arch = platform.machine().lower()

    download_url = None
    if system == "darwin":
        if arch == "x86_64":
            download_url = JRE_DOWNLOAD_URLS["darwin"]["x86_64"]
        elif arch == "arm64":
            download_url = JRE_DOWNLOAD_URLS["darwin"]["aarch64"]
        else:
            raise Exception(f"Unsupported macOS architecture: {arch}")
    elif system == "linux":
        if arch == "x86_64":
            download_url = JRE_DOWNLOAD_URLS["linux"]["x86_64"]
        elif arch == "aarch64":
            download_url = JRE_DOWNLOAD_URLS["linux"]["aarch64"]
        else:
            raise Exception(f"Unsupported Linux architecture: {arch}")
    elif system == "windows":
        if arch == "x86_64":
            download_url = JRE_DOWNLOAD_URLS["windows"]["x86_64"]
        else:
            raise Exception(f"Unsupported Windows architecture: {arch}")
    else:
        raise Exception(f"Unsupported operating system: {system}")

    logger.info(f"Downloading JRE from: {download_url}")
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status() # Raise an exception for HTTP errors

        temp_file_path = os.path.join(JRE_DIR, "jre_temp.zip" if system == "windows" else "jre_temp.tar.gz")
        with open(temp_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info("Download complete. Extracting...")

        if system == "windows":
            with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                zip_ref.extractall(JRE_DIR)
        else:
            with tarfile.open(temp_file_path, 'r:gz') as tar_ref:
                tar_ref.extractall(JRE_DIR)
        
        # Find the actual extracted directory name (e.g., jdk-17.0.x+x-jre)
        extracted_jre_path = None
        for item in os.listdir(JRE_DIR):
            full_path = os.path.join(JRE_DIR, item)
            if os.path.isdir(full_path) and ("jdk" in item.lower() or "jre" in item.lower()):
                extracted_jre_path = full_path
                break
        
        if not extracted_jre_path:
            raise Exception(f"Could not find extracted JRE directory in {JRE_DIR} after extraction.")

        os.remove(temp_file_path)
        logger.info("Extraction complete.")

        # Construct java_exe_path after extraction
        if platform.system() == "Windows":
            java_exe_path = os.path.join(extracted_jre_path, "bin", "java.exe")
        elif platform.system() == "Darwin":
            java_exe_path = os.path.join(extracted_jre_path, "Contents", "Home", "bin", "java")
        else: # Linux
            java_exe_path = os.path.join(extracted_jre_path, "bin", "java")

        # Make java executable on Unix-like systems
        if system != "windows":
            if os.path.exists(java_exe_path):
                os.chmod(java_exe_path, 0o755)
            else:
                raise Exception(f"Java executable not found at {java_exe_path} after extraction for chmod.")

        if not os.path.exists(java_exe_path) or not os.access(java_exe_path, os.X_OK):
            raise Exception(f"Failed to find or make Java executable at {java_exe_path} after extraction.")

        return java_exe_path

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to download JRE: {e}")
    except (zipfile.BadZipFile, tarfile.ReadError) as e:
        raise Exception(f"Failed to extract JRE: {e}. Downloaded file might be corrupted.")
    except Exception as e:
        raise Exception(f"An unexpected error occurred during JRE setup: {e}")

# --- Main Logic ---
def find_class_source(project_path, class_name, submodule_path=None):
    java_exe = ensure_jre_available()

    # Construct classpath for helper.jar
    lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "java_helper", "lib")
    build_classes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "java_helper", "build", "classes")
    classpath_elements = [build_classes_dir] + [os.path.join(lib_dir, f) for f in os.listdir(lib_dir) if f.endswith(".jar")]
    classpath = os.pathsep.join(classpath_elements)

    # Call helper.jar
    helper_cmd = [
        java_exe,
        "-cp", classpath,
        "com.example.ClassFinder", # Main class
        project_path,
        class_name
    ]
    if submodule_path:
        helper_cmd.append(submodule_path)

    logger.debug(f"Running helper.jar: {' '.join(helper_cmd)}")
    try:
        helper_process = subprocess.run(helper_cmd, capture_output=True, text=True, check=True)
        helper_output = helper_process.stdout
        matches = json.loads(helper_output)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running helper.jar: {e}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return {"status": "error", "message": "Failed to get dependency info from Gradle project.", "details": e.stderr}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding helper.jar output: {e}")
        logger.error(f"Helper output: {helper_output}")
        return {"status": "error", "message": "Invalid JSON output from helper.jar.", "details": str(e)}

    final_results = []
    for match in matches:
        jar_path = match["jarPath"]
        source_jar_path = match.get("sourceJarPath")
        dependency_coordinates = match["dependencyCoordinates"]
        found_class_name = match["className"]
        is_local = match.get("isLocal", False)

        source_code = None
        source_type = ""

        # Handle local source files
        if is_local and jar_path.endswith(".java"):
            try:
                with open(jar_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                source_type = "local_source"
                logger.debug(f"Read local source from {jar_path}")
            except Exception as e:
                logger.error(f"Error reading local source {jar_path}: {e}")
                source_code = f"// Error reading local source: {e}"
                source_type = "error"
        elif source_jar_path and os.path.exists(source_jar_path):
            try:
                # Extract source from source JAR
                with zipfile.ZipFile(source_jar_path, 'r') as zip_ref:
                    source_entry_name = found_class_name.replace('.', '/') + ".java"
                    # Some source JARs might have a top-level directory, try to find it
                    found_source_entry = None
                    for entry in zip_ref.namelist():
                        if entry.endswith(source_entry_name):
                            found_source_entry = entry
                            break
                    
                    if found_source_entry:
                        with zip_ref.open(found_source_entry) as source_file:
                            source_code = source_file.read().decode('utf-8')
                        source_type = "source"
                    else:
                        logger.warning(f"Source entry {source_entry_name} not found in {source_jar_path}. Falling back to decompilation.")

            except Exception as e:
                logger.warning(f"Error extracting source from {source_jar_path}: {e}. Falling back to decompilation.")

        if source_code is None:
            # Decompile using CFR
            logger.debug(f"Decompiling {found_class_name} from {jar_path} using CFR...")
            decompile_cmd = [
                java_exe,
                "-jar", CFR_JAR_PATH,
                jar_path,
                found_class_name  # CFR takes the class name as a direct argument
            ]
            try:
                decompile_process = subprocess.run(decompile_cmd, capture_output=True, text=True, check=True)
                source_code = decompile_process.stdout
                source_type = "decompiled"
            except subprocess.CalledProcessError as e:
                logger.error(f"Error decompiling {found_class_name}: {e}")
                logger.error(f"Stdout: {e.stdout}")
                logger.error(f"Stderr: {e.stderr}")
                source_code = f"// Failed to decompile {found_class_name}: {e.stderr}"
                source_type = "error_decompilation"

        final_results.append({
            "source_type": source_type,
            "source_code": source_code,
            "jar_path": jar_path,
            "source_jar_path": source_jar_path,
            "dependency_coordinates": dependency_coordinates,
            "class_name": found_class_name
        })
    
    if not final_results:
        return {"status": "error", "message": f"Class '{class_name}' not found in any dependency.", "matches": []}

    return {"status": "success", "matches": final_results}

# --- MCP Server Implementation ---

# Create MCP server instance
server = Server("gradle-class-finder")

# Create a wrapper class for better organization
class GradleClassFinder:
    def __init__(self):
        pass
    
    def find_class_in_dependencies(self, workspace_dir: str, class_name: str) -> List[Dict]:
        """Find class in Gradle dependencies using the helper.jar"""
        result = find_class_source(workspace_dir, class_name)
        if result["status"] == "success":
            return result["matches"]
        else:
            raise Exception(result.get("message", "Unknown error"))
    
    def get_source_code(self, jar_path: str, class_name: str, 
                       line_start: Optional[int] = None, 
                       line_end: Optional[int] = None) -> str:
        """Get source code from a specific JAR file or local source file"""
        # Handle local source files
        if jar_path.endswith(".java"):
            try:
                with open(jar_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                    if line_start is not None and line_end is not None:
                        lines = source_code.split('\n')
                        return '\n'.join(lines[line_start-1:line_end])
                    return source_code
            except Exception as e:
                return f"// Error reading local source: {e}"
        
        # Use the existing logic to extract or decompile
        java_exe = ensure_jre_available()
        
        # First try to find source JAR
        source_jar_path = jar_path.replace('.jar', '-sources.jar')
        source_code = None
        source_type = ""
        
        if os.path.exists(source_jar_path):
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
                logger.warning(f"Error extracting source: {e}")
        
        if source_code is None:
            # Decompile using CFR
            decompile_cmd = [
                java_exe,
                "-jar", CFR_JAR_PATH,
                jar_path,
                class_name  # CFR takes the class name as a direct argument
            ]
            try:
                decompile_process = subprocess.run(decompile_cmd, capture_output=True, text=True, check=True)
                source_code = decompile_process.stdout
                source_type = "decompiled"
            except subprocess.CalledProcessError as e:
                source_code = f"// Failed to decompile {class_name}: {e.stderr}"
                source_type = "error"
        
        # Handle line range extraction
        if source_code and line_start is not None and line_end is not None:
            lines = source_code.split('\n')
            return '\n'.join(lines[line_start-1:line_end])
        
        return source_code
    
    def get_class_metadata(self, jar_path: str, class_name: str) -> Dict:
        """Get metadata about a class"""
        source_code = self.get_source_code(jar_path, class_name)
        lines = source_code.split('\n')
        
        # Simple method extraction
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

# Create global finder instance
finder = GradleClassFinder()

# Define MCP tools
@server.list_tools()
async def list_tools() -> List[Tool]:
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
                    content += f"- Dependency: {result['dependency_coordinates']}\n"
                    content += f"  JAR Path: {result['jar_path']}\n"
                    if result.get('source_jar_path'):
                        content += f"  Source JAR: {result['source_jar_path']}\n"
                    content += "\n"
            else:
                content = f"Class {arguments['class_name']} not found in dependencies"
            
            return CallToolResult(content=[TextContent(type="text", text=content)])
        
        elif name == "get_source_code":
            source_code = finder.get_source_code(
                arguments["jar_path"],
                arguments["class_name"],
                arguments.get("line_start"),
                arguments.get("line_end")
            )
            
            return CallToolResult(content=[TextContent(type="text", text=source_code)])
        
        elif name == "get_source_metadata":
            metadata = finder.get_class_metadata(
                arguments["jar_path"],
                arguments["class_name"]
            )
            
            content = json.dumps(metadata, indent=2)
            return CallToolResult(content=[TextContent(type="text", text=content)])
        
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True
            )
    
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True
        )

# Main MCP server function
async def amain():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

def main():
    """Entry point for uvx/pip install"""
    asyncio.run(amain())

# --- CLI Entry Point ---
if __name__ == "__main__":
    import sys
    
    # Check if running as MCP server (no arguments)
    if len(sys.argv) == 1:
        # Run as MCP server
        main()
    else:
        # Run as CLI tool
        import argparse

        parser = argparse.ArgumentParser(description="Gradle Class Finder MCP: Find and retrieve source code for classes in Gradle project dependencies.")
        parser.add_argument("--project-path", required=True, help="Absolute path to the root of the Gradle project.")
        parser.add_argument("--class-name", required=True, help="Fully qualified class name (e.g., com.example.MyClass).")
        parser.add_argument("--submodule-path", help="Optional: Path to a specific Gradle submodule relative to project-path.")

        args = parser.parse_args()

        try:
            result = find_class_source(args.project_path, args.class_name, args.submodule_path)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}, indent=2))