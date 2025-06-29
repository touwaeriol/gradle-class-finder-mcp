import argparse
import json
import os
import subprocess
import sys

# Determine the base directory of the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the helper JAR
HELPER_JAR = os.path.join(BASE_DIR, "build", "libs", "gradle-class-finder-helper.jar")

# Path to the JRE (if downloaded)
JRE_PATH = os.path.join(BASE_DIR, ".java_runtime", "bin", "java")

def run_java_helper(args):
    java_command = [get_java_executable()]
    java_command.extend(["-jar", HELPER_JAR])
    java_command.extend(args)

    process = subprocess.Popen(
        java_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )
    stdout, stderr = process.communicate()

    if stderr:
        print(f"Java helper stderr: {stderr}", file=sys.stderr)

    if process.returncode != 0:
        print(f"Error running Java helper: Process exited with code {process.returncode}", file=sys.stderr)
        sys.exit(1)
    return stdout

def get_java_executable():
    # Check if JRE is downloaded and available
    if os.path.exists(JRE_PATH):
        return JRE_PATH

    # Fallback to system Java
    system_java = "java"
    try:
        which_java_output = subprocess.check_output(["which", system_java], text=True).strip()
        print(f"Using system Java from: {which_java_output}", file=sys.stderr)
    except subprocess.CalledProcessError:
        print(f"Warning: 'which {system_java}' failed. Using default path.", file=sys.stderr)
    return system_java

def find_class(workspace_dir, class_name, submodule_path=None):
    args = [workspace_dir, class_name]
    if submodule_path:
        args.append(submodule_path)
    output = run_java_helper(args)
    return json.loads(output)

def get_source_code(jar_path, class_name, line_start=None, line_end=None):
    args = ["--decompile", jar_path, class_name]
    if line_start is not None:
        args.extend(["--line-start", str(line_start)])
    if line_end is not None:
        args.extend(["--line-end", str(line_end)])
    return run_java_helper(args)

def get_source_metadata(jar_path, class_name):
    args = ["--metadata", jar_path, class_name]
    output = run_java_helper(args)
    return json.loads(output)

def main():
    parser = argparse.ArgumentParser(description="Gradle Class Finder MCP Server")
    parser.add_argument("command", help="Command to execute (find_class, get_source_code, get_source_metadata)")
    parser.add_argument("--workspace_dir", help="Path to the Gradle project root")
    parser.add_argument("--class_name", help="Fully qualified class name (e.g., com.example.MyClass)")
    parser.add_argument("--submodule_path", help="Path to the submodule within the Gradle project")
    parser.add_argument("--jar_path", help="Full path to the JAR file")
    parser.add_argument("--line_start", type=int, help="Start line number for source code")
    parser.add_argument("--line_end", type=int, help="End line number for source code")

    args = parser.parse_args()

    if args.command == "find_class":
        if not args.workspace_dir or not args.class_name:
            parser.error("find_class requires --workspace_dir and --class_name")
        result = find_class(args.workspace_dir, args.class_name, args.submodule_path)
    elif args.command == "get_source_code":
        if not args.jar_path or not args.class_name:
            parser.error("get_source_code requires --jar_path and --class_name")
        result = get_source_code(args.jar_path, args.class_name, args.line_start, args.line_end)
    elif args.command == "get_source_metadata":
        if not args.jar_path or not args.class_name:
            parser.error("get_source_metadata requires --jar_path and --class_name")
        result = get_source_metadata(args.jar_path, args.class_name)
    else:
        parser.error(f"Unknown command: {args.command}")

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
