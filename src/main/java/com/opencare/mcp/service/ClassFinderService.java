package com.opencare.mcp.service;

import org.gradle.tooling.GradleConnector;
import org.gradle.tooling.ProjectConnection;
import org.gradle.tooling.model.GradleProject;
import org.gradle.tooling.model.idea.IdeaProject;
import org.gradle.tooling.model.idea.IdeaModule;
import org.gradle.tooling.model.idea.IdeaDependency;
import org.gradle.tooling.model.idea.IdeaSingleEntryLibraryDependency;

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

/**
 * 类查找服务
 * 提供在Gradle项目依赖中查找Java类的功能
 */
public class ClassFinderService {
    
    public List<MatchResult> findClassInProject(String projectPath, String originalClassName, String submodulePath) {
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
                    throw new RuntimeException("子模块未找到: " + submodulePath);
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
                    System.err.println("[INFO] 找到本地类: " + localSource.getAbsolutePath());
                }
            }

            // Use IdeaProject model for more reliable dependency and source information
            // IMPORTANT: Only process dependencies for the CURRENT module/submodule, not parent modules
            IdeaProject ideaProject = connection.getModel(IdeaProject.class);
            String targetModulePath = targetProject.getPath();
            
            System.err.println("[INFO] 目标模块路径: " + targetModulePath);
            
            for (IdeaModule module : ideaProject.getModules()) {
                String modulePath = module.getGradleProject().getPath();
                System.err.println("[DEBUG] 检查模块: " + modulePath);
                
                // STRICT: Only process the exact target module, not parent or child modules
                if (modulePath.equals(targetModulePath)) {
                    System.err.println("[INFO] 处理目标模块的依赖: " + modulePath);
                    
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
                                    System.err.println("[INFO] 在依赖中找到: " + file.getName());
                                }
                            }
                        }
                    }
                    break; // Found and processed the target module
                } else {
                    System.err.println("[DEBUG] 跳过模块: " + modulePath + " (非目标模块)");
                }
            }
            
            // Check flatDir repositories
            checkFlatDirDependencies(projectDir, className, originalClassName, results);

        } catch (Exception e) {
            throw new RuntimeException("连接Gradle或处理项目时出错: " + e.getMessage(), e);
        } finally {
            if (connection != null) {
                connection.close();
            }
        }

        return results;
    }

    private boolean containsClass(File jarFile, String className) {
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
    
    private String extractDependencyCoordinates(File jarFile) {
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
    
    private void checkFlatDirDependencies(File projectDir, String className, String originalClassName, List<MatchResult> results) {
        try {
            System.err.println("[INFO] 检查当前模块的flatDir依赖: " + projectDir.getAbsolutePath());
            
            // STRICT: Only check build.gradle in the CURRENT module, NOT parent modules
            File buildGradle = new File(projectDir, "build.gradle");
            if (!buildGradle.exists()) {
                // Also try build.gradle.kts for Kotlin DSL
                buildGradle = new File(projectDir, "build.gradle.kts");
            }
            
            List<String> flatDirs = new ArrayList<>();
            
            if (buildGradle.exists()) {
                flatDirs.addAll(parseFlatDirs(buildGradle));
            }
            
            // Also check common directories, but ONLY relative to current module
            flatDirs.add("libs");
            flatDirs.add("lib");
            
            // IMPORTANT: Only check directories relative to CURRENT module, not parent
            for (String dir : flatDirs) {
                File flatDirPath;
                if (dir.startsWith("/")) {
                    // Absolute path
                    flatDirPath = new File(dir);
                } else {
                    // Relative path - ONLY relative to current module directory
                    flatDirPath = new File(projectDir, dir);
                }
                
                if (flatDirPath.exists() && flatDirPath.isDirectory()) {
                    System.err.println("[INFO] 检查flatDir: " + flatDirPath.getAbsolutePath());
                    checkDirectoryForJars(flatDirPath, className, originalClassName, results);
                } else {
                    System.err.println("[DEBUG] FlatDir未找到: " + flatDirPath.getAbsolutePath());
                }
            }
        } catch (Exception e) {
            System.err.println("检查flatDir依赖时出错: " + e.getMessage());
        }
    }

    private List<String> parseFlatDirs(File buildGradle) {
        List<String> dirs = new ArrayList<>();
        try (BufferedReader reader = new BufferedReader(new FileReader(buildGradle))) {
            String line;
            Pattern flatDirPattern = Pattern.compile("flatDir.*dirs:\\s*[\"']([^\"']*)[\"']");
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
            System.err.println("读取build.gradle时出错: " + e.getMessage());
        }
        return dirs;
    }

    private void checkDirectoryForJars(File directory, String className, String originalClassName, List<MatchResult> results) {
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
            System.err.println("检查目录时出错 " + directory + ": " + e.getMessage());
        }
    }
}