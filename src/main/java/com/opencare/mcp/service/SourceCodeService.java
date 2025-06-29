package com.opencare.mcp.service;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Enumeration;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;

/**
 * 源码服务
 * 提供获取Java类源码或反编译代码的功能
 */
public class SourceCodeService {
    
    /**
     * 获取指定类的源码
     * 
     * @param jarPath JAR文件路径或Java源文件路径
     * @param className 类的全限定名
     * @param lineStart 起始行号 (可选)
     * @param lineEnd 结束行号 (可选)
     * @return 源码内容
     */
    public String getSourceCode(String jarPath, String className, Integer lineStart, Integer lineEnd) {
        File file = new File(jarPath);
        
        // 如果是Java源文件，直接读取
        if (jarPath.endsWith(".java")) {
            return readJavaSourceFile(jarPath, lineStart, lineEnd);
        }
        
        // 如果是JAR文件，尝试提取源码或反编译
        if (jarPath.endsWith(".jar")) {
            // 首先尝试从sources.jar中提取源码
            String sourceCode = extractSourceFromJar(jarPath, className);
            if (sourceCode != null) {
                return filterLines(sourceCode, lineStart, lineEnd);
            }
            
            // 如果没有源码，使用CFR反编译
            return decompileClass(jarPath, className, lineStart, lineEnd);
        }
        
        throw new RuntimeException("不支持的文件类型: " + jarPath);
    }
    
    /**
     * 读取Java源文件
     */
    private String readJavaSourceFile(String filePath, Integer lineStart, Integer lineEnd) {
        try {
            String content = Files.readString(Paths.get(filePath));
            return filterLines(content, lineStart, lineEnd);
        } catch (IOException e) {
            throw new RuntimeException("读取Java源文件失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 从JAR文件中提取源码
     */
    private String extractSourceFromJar(String jarPath, String className) {
        String sourceFileName = className.replace('.', '/') + ".java";
        
        try (JarFile jarFile = new JarFile(jarPath)) {
            Enumeration<JarEntry> entries = jarFile.entries();
            while (entries.hasMoreElements()) {
                JarEntry entry = entries.nextElement();
                if (entry.getName().equals(sourceFileName)) {
                    try (InputStream inputStream = jarFile.getInputStream(entry);
                         BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
                        
                        StringBuilder content = new StringBuilder();
                        String line;
                        while ((line = reader.readLine()) != null) {
                            content.append(line).append("\n");
                        }
                        return content.toString();
                    }
                }
            }
        } catch (IOException e) {
            System.err.println("从JAR提取源码失败: " + e.getMessage());
        }
        
        return null; // 源码不存在
    }
    
    /**
     * 使用CFR反编译Java类
     */
    private String decompileClass(String jarPath, String className, Integer lineStart, Integer lineEnd) {
        try {
            // 使用CFR API直接反编译，而不是命令行
            return decompileWithCfrApi(jarPath, className, lineStart, lineEnd);
        } catch (Exception e) {
            throw new RuntimeException("反编译类失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 使用CFR API进行反编译
     */
    private String decompileWithCfrApi(String jarPath, String className, Integer lineStart, Integer lineEnd) {
        try {
            // 简化CFR的使用方式，使用默认设置
            java.util.Map<String, String> options = new java.util.HashMap<>();
            options.put("outputpath", "/tmp/cfr-output");
            options.put("silent", "true");
            
            // 创建CFR输出目录
            File outputDir = new File("/tmp/cfr-output");
            if (!outputDir.exists()) {
                outputDir.mkdirs();
            }
            
            // 使用CFR main方法进行反编译
            String[] args = {
                jarPath,
                "--outputpath", "/tmp/cfr-output",
                "--silent"
            };
            
            // 调用CFR的main方法
            org.benf.cfr.reader.Main.main(args);
            
            // 读取反编译后的文件
            String outputFileName = "/tmp/cfr-output/" + className.replace('.', '/') + ".java";
            File outputFile = new File(outputFileName);
            
            if (!outputFile.exists()) {
                throw new RuntimeException("反编译输出文件不存在: " + outputFileName);
            }
            
            String content = Files.readString(outputFile.toPath());
            return filterLines(content, lineStart, lineEnd);
            
        } catch (Exception e) {
            throw new RuntimeException("CFR API反编译失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 根据行号范围过滤内容
     */
    private String filterLines(String content, Integer lineStart, Integer lineEnd) {
        if (lineStart == null && lineEnd == null) {
            return content;
        }
        
        String[] lines = content.split("\n");
        StringBuilder result = new StringBuilder();
        
        int start = (lineStart != null) ? Math.max(1, lineStart) : 1;
        int end = (lineEnd != null) ? Math.min(lines.length, lineEnd) : lines.length;
        
        for (int i = start - 1; i < end && i < lines.length; i++) {
            result.append(lines[i]).append("\n");
        }
        
        return result.toString();
    }
}