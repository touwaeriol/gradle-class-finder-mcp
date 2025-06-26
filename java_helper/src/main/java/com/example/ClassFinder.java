package com.example;

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
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;

public class ClassFinder {

    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    public static void main(String[] args) {
        if (args.length < 2) {
            System.err.println("Usage: java -jar helper.jar <projectPath> <className> [submodulePath]");
            System.exit(1);
        }

        String projectPath = args[0];
        String className = args[1].replace('.', '/') + ".class"; // Convert to internal class name
        String originalClassName = args[1];
        String submodulePath = args.length > 2 ? args[2] : null;

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

        } catch (Exception e) {
            System.err.println("Error connecting to Gradle or processing project: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        } finally {
            if (connection != null) {
                connection.close();
            }
        }

        System.out.println(GSON.toJson(results));
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

    static class MatchResult {
        String jarPath;
        String sourceJarPath;
        String dependencyCoordinates;
        String className;
        boolean isLocal = false;
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
}
