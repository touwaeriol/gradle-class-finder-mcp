# Gradle Class Finder MCP

This project implements a self-contained, "black-box" tool (MCP) designed to locate and provide source code for classes found within the dependencies of a Gradle project. It supports both retrieving actual source code from source JARs and decompiling class files when sources are unavailable.

## Overview

Many times, when working with large Gradle projects, it's challenging to quickly find the source code for a specific class that resides within a project's dependencies, especially when dealing with multiple versions of the same library or complex dependency trees. This tool aims to solve that by providing a robust and self-contained solution.

The tool is designed to be a "black box," meaning it does not rely on any external tools pre-installed on the user's system (except for a Python interpreter). It automatically manages its own Java Runtime Environment (JRE) and bundles necessary components like a Gradle Tooling API helper and a Java decompiler.

## Features

*   **Class Location in Dependencies:** Given a Gradle project path (and an optional submodule path), it can find which JAR file contains a specified class.
*   **Source Code Retrieval (Preferred):** If a source JAR (`-sources.jar`) is available for the dependency, it will extract and return the original source code.
*   **Decompilation (Fallback):** If the source JAR is not found, it will decompile the `.class` file from the binary JAR and return the decompiled Java code.
*   **Submodule Support:** Accurately resolves dependencies within a specific Gradle submodule.
*   **Multi-Version Awareness:** If the same class name exists in multiple dependencies or different versions of the same dependency, the tool will identify and return information for *all* matching occurrences, including their full Maven/Gradle coordinates.
*   **Self-Contained JRE:** Automatically downloads and manages its own lightweight Java Runtime Environment (JRE) on first run, eliminating the need for a pre-installed Java environment on the host system.
*   **No `gradlew` Dependency:** Uses the Gradle Tooling API directly, avoiding common issues associated with `gradlew` command-line execution (e.g., `JAVA_HOME` conflicts, IDE integration problems).

## How It Works (High-Level)

1.  **Initialization:** On its first run, the tool checks for a bundled JRE. If not found, it automatically downloads a suitable JRE for the host operating system and architecture.
2.  **Request Handling:** The main Python server (`server.py`) receives requests specifying the Gradle project path, an optional submodule path, and the target class name.
3.  **Gradle Model Resolution:** The Python server invokes a small, self-contained Java helper (`helper.jar`). This helper uses the official Gradle Tooling API to connect to the specified Gradle project (or submodule) and programmatically resolve its dependency graph.
4.  **Class and Source Finding:** The `helper.jar` identifies all JARs in the project's compile classpath that contain the target class. For each identified JAR, it attempts to locate its corresponding source JAR. All findings, including dependency coordinates, are returned to the Python server.
5.  **Source Extraction/Decompilation:**
    *   If a source JAR is found, the Python server extracts the original `.java` file.
    *   If no source JAR is found, the Python server uses a bundled Java decompiler (e.g., CFR) to decompile the `.class` file from the binary JAR.
6.  **Result Delivery:** The extracted or decompiled source code, along with metadata (source type, JAR path, dependency coordinates), is returned to the client.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/gradle-class-finder-mcp.git
    cd gradle-class-finder-mcp
    ```
2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Initial JRE Download (Automatic):**
    The first time you run `server.py`, it will automatically download and set up its internal JRE. This might take a moment depending on your internet connection.

## Usage Example

(This section will be filled once the API is finalized and implemented.)

```bash
# Example command (conceptual, actual API might be HTTP or direct function call)
python server.py --project-path /path/to/your/gradle/project --class-name com.example.MyClass --submodule-path my-submodule

# Example output (conceptual)
# {
#   "status": "success",
#   "matches": [
#     {
#       "source_type": "source",
#       "source_code": "...",
#       "jar_path": "...",
#       "dependency_coordinates": "...",
#       "class_name": "..."
#     },
#     {
#       "source_type": "decompiled",
#       "source_code": "...",
#       "jar_path": "...",
#       "dependency_coordinates": "...",
#       "class_name": "..."
#     }
#   ]
# }
```
