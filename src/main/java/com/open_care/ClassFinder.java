package com.open_care;

import org.gradle.tooling.GradleConnector;
import org.gradle.tooling.ProjectConnection;
import org.gradle.tooling.model.build.BuildEnvironment;
import org.gradle.tooling.model.GradleProject;
import org.gradle.tooling.model.idea.IdeaProject;
import org.gradle.tooling.model.idea.IdeaModule;
import org.gradle.tooling.model.idea.IdeaDependency;
import org.gradle.tooling.model.idea.IdeaSingleEntryLibraryDependency;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.io.File;
import java.io.IOException;
import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class ClassFinder {

    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private static final String CFR_JAR_PATH = "lib/cfr-0.152.jar";

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("Usage: java -jar helper.jar <projectPath> <className> [submodulePath]");
            System.exit(1);
        }

        String projectPath = args[0];
        String originalClassName = args[1];
        String submodulePath = args.length > 2 ? args[2] : null;

        try {
            List<MatchResult> results = findClassInProject(projectPath, originalClassName, submodulePath);
            System.out.println(GSON.toJson(results));
        } catch (Exception e) {
            System.err.println("Error finding class: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
    
    public static List<MatchResult> findClassInProject(String projectPath, String originalClassName, String submodulePath) {
        String className = originalClassName.replace('.', '/') + ".class"; // Convert to internal class name
        List<MatchResult> results = new ArrayList<>();

        ProjectConnection connection = null;
        try {
            GradleConnector connector = GradleConnector.newConnector();
            connector.forProjectDirectory(new File(projectPath));
            connection = connector.connect();

            GradleProject rootProject = connection.getModel(GradleProject.class);
            GradleProject targetProject = rootProject;

            if (submodulePath != null && !submodulePath.isEmpty()) {
                boolean foundSubmodule = false;
                for (GradleProject childProject : rootProject.getChildren()) {
                    if (childProject.getPath().equals(":" + submodulePath.replace('/', ':'))) {
                        targetProject = childProject;
                        foundSubmodule = true;
                        break;
                    }
                }
                if (!foundSubmodule) {
                    System.err.println("Submodule not found: " + submodulePath);
                    System.exit(1);
                }
            }

            // First check if the class exists locally in the module
            File projectDir = new File(projectPath);
            if (submodulePath != null && !submodulePath.isEmpty()) {
                projectDir = new File(projectPath, submodulePath);
            }
            
            // Check for local source file
            String localSourcePath = originalClassName.replace('.', File.separatorChar) + ".java";
            File[] possibleSourceDirs = {
                new File(projectDir, "src/main/java"),
                new File(projectDir, "src/main/kotlin"),
                new File(projectDir, "src/java"),
                new File(projectDir, "src")
            };
            
            for (File srcDir : possibleSourceDirs) {
                File localSource = new File(srcDir, localSourcePath);
                if (localSource.exists() && localSource.isFile()) {
                    MatchResult localMatch = new MatchResult();
                    localMatch.jarPath = localSource.getAbsolutePath();
                    localMatch.sourceJarPath = localSource.getAbsolutePath();
                    localMatch.className = originalClassName;
                    localMatch.dependencyCoordinates = "LOCAL::" + (submodulePath != null ? submodulePath : projectDir.getName());
                    localMatch.isLocal = true;
                    results.add(localMatch);
                    System.err.println("[INFO] Found local class: " + localSource.getAbsolutePath());
                }
            }

            // Use IdeaProject model for more reliable dependency and source information
            IdeaProject ideaProject = connection.getModel(IdeaProject.class);
            for (IdeaModule module : ideaProject.getModules()) {
                if (module.getGradleProject().getPath().equals(targetProject.getPath())) {
                    for (IdeaDependency dependency : module.getDependencies()) {
                        if (dependency instanceof IdeaSingleEntryLibraryDependency) {
                            IdeaSingleEntryLibraryDependency libDependency = (IdeaSingleEntryLibraryDependency) dependency;
                            File file = libDependency.getFile();
                            if (file != null && file.getName().endsWith(".jar")) {
                                if (containsClass(file, className)) {
                                    MatchResult match = new MatchResult();
                                    match.jarPath = file.getAbsolutePath();
                                    match.className = originalClassName;

                                    // Extract proper dependency coordinates from the file path
                                    String coordinates = extractDependencyCoordinates(file);
                                    match.dependencyCoordinates = coordinates;

                                    File sourceFile = libDependency.getSource();
                                    if (sourceFile != null && sourceFile.exists() && sourceFile.getName().endsWith("-sources.jar")) {
                                        match.sourceJarPath = sourceFile.getAbsolutePath();
                                    }
                                    results.add(match);
                                }
                            }
                        }
                    }
                    break; // Found the target module
                }
            }
            
            // Check flatDir repositories
            checkFlatDirDependencies(projectDir, className, originalClassName, results);

        } catch (Exception e) {
            throw new RuntimeException("Error connecting to Gradle or processing project: " + e.getMessage(), e);
        } finally {
            if (connection != null) {
                connection.close();
            }
        }

        return results;
    }

    private static boolean containsClass(File jarFile, String className) {
        try (JarFile jar = new JarFile(jarFile)) {
            Enumeration<JarEntry> entries = jar.entries();
            while (entries.hasMoreElements()) {
                JarEntry entry = entries.nextElement();
                if (entry.getName().equals(className)) {
                    return true;
                }
            }
        } catch (IOException e) {
            // System.err.println("Error reading JAR file " + jarFile.getAbsolutePath() + ": " + e.getMessage());
        }
        return false;
    }

    public static class MatchResult {
        public String jarPath;
        public String sourceJarPath;
        public String dependencyCoordinates;
        public String className;
        public boolean isLocal = false;
    }
    
    private static String extractDependencyCoordinates(File jarFile) {
        // Try to extract Maven coordinates from the file path
        // Example: /Users/xxx/.gradle/caches/modules-2/files-2.1/org.springframework.boot/spring-boot/3.3.6/xxx/spring-boot-3.3.6.jar
        String path = jarFile.getAbsolutePath();
        if (path.contains(".gradle/caches/modules-2/files-2.1/")) {
            String[] parts = path.split(".gradle/caches/modules-2/files-2.1/")[1].split("/");
            if (parts.length >= 4) {
                String group = parts[0];
                String artifact = parts[1];
                String version = parts[2];
                return group + ":" + artifact + ":" + version;
            }
        }
        // Fallback to just the filename
        return jarFile.getName();
    }
    
    private static void checkFlatDirDependencies(File projectDir, String className, String originalClassName, List<MatchResult> results) {
        try {
            // Check build.gradle for flatDir configurations
            File buildGradle = new File(projectDir, "build.gradle");
            if (!buildGradle.exists()) {
                buildGradle = new File(projectDir.getParentFile(), "build.gradle");
            }
            
            if (buildGradle.exists()) {
                List<String> flatDirs = parseFlatDirs(buildGradle);
                
                // Also check common directories
                flatDirs.add(".annotated-libs");
                flatDirs.add("libs");
                flatDirs.add("lib");
                
                for (String dir : flatDirs) {
                    File flatDirPath;
                    if (dir.startsWith("/") || dir.startsWith("${")) {
                        // Absolute path or variable
                        if (dir.contains("${rootProject.projectDir")) {
                            dir = dir.replace("${rootProject.projectDir.path}", projectDir.getParentFile().getAbsolutePath());
                            dir = dir.replace("${rootProject.projectDir}", projectDir.getParentFile().getAbsolutePath());
                        }
                        flatDirPath = new File(dir);
                    } else {
                        // Relative path
                        flatDirPath = new File(projectDir.getParentFile(), dir);
                    }
                    
                    if (flatDirPath.exists() && flatDirPath.isDirectory()) {
                        checkDirectoryForJars(flatDirPath, className, originalClassName, results);
                    }
                }
            }
        } catch (Exception e) {
            System.err.println("Error checking flatDir dependencies: " + e.getMessage());
        }
    }

    private static List<String> parseFlatDirs(File buildGradle) {
        List<String> dirs = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(buildGradle))) {
            String line;
            Pattern flatDirPattern = Pattern.compile("flatDir.*dirs:\\s*[\"']([^\"']+)[\"']");
            Pattern flatDirPattern2 = Pattern.compile("flatDir.*dirs:\\s*\\[([^\\]]+)\\]");
            
            while ((line = reader.readLine()) != null) {
                Matcher matcher = flatDirPattern.matcher(line);
                if (matcher.find()) {
                    dirs.add(matcher.group(1).trim());
                } else {
                    matcher = flatDirPattern2.matcher(line);
                    if (matcher.find()) {
                        String[] multipleDirs = matcher.group(1).split(",");
                        for (String dir : multipleDirs) {
                            dirs.add(dir.trim().replaceAll("[\"']", ""));
                        }
                    }
                }
            }
        } catch (IOException e) {
            System.err.println("Error reading build.gradle: " + e.getMessage());
        }
        return dirs;
    }

    private static void checkDirectoryForJars(File directory, String className, String originalClassName, List<MatchResult> results) {
        try {
            File[] jarFiles = directory.listFiles((dir, name) -> name.endsWith(".jar"));
            if (jarFiles != null) {
                for (File jarFile : jarFiles) {
                    if (containsClass(jarFile, className)) {
                        // Check if already found to avoid duplicates
                        boolean alreadyFound = results.stream()
                            .anyMatch(r -> r.jarPath.equals(jarFile.getAbsolutePath()));
                        
                        if (!alreadyFound) {
                            MatchResult match = new MatchResult();
                            match.jarPath = jarFile.getAbsolutePath();
                            match.className = originalClassName;
                            match.dependencyCoordinates = "FLATDIR::" + jarFile.getName();
                            results.add(match);
                        }
                    }
                }
            }
        } catch (Exception e) {
            System.err.println("Error checking directory " + directory + ": " + e.getMessage());
        }
    }
    
    public static String decompileClass(String jarPath, String className, Integer lineStart, Integer lineEnd) {
        try {
            // Use CFR to decompile the class
            ProcessBuilder pb = new ProcessBuilder(
                "java", "-jar", CFR_JAR_PATH, jarPath, className
            );
            
            Process process = pb.start();
            
            // Read the output
            StringBuilder output = new StringBuilder();
            try (BufferedReader reader = new BufferedReader(new java.io.InputStreamReader(process.getInputStream()))) {
                String line;
                int lineNumber = 0;
                while ((line = reader.readLine()) != null) {
                    lineNumber++;
                    if ((lineStart == null || lineNumber >= lineStart) && 
                        (lineEnd == null || lineNumber <= lineEnd)) {
                        output.append(line).append("\n");
                    }
                }
            }
            
            int exitCode = process.waitFor();
            if (exitCode != 0) {
                throw new RuntimeException("CFR decompilation failed with exit code: " + exitCode);
            }
            
            return output.toString();
        } catch (Exception e) {
            throw new RuntimeException("Failed to decompile class: " + e.getMessage(), e);
        }
    }
}
