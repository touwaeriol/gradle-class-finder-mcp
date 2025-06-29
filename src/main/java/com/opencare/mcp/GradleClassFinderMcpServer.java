package com.opencare.mcp;

import io.modelcontextprotocol.server.McpServer;
import io.modelcontextprotocol.server.transport.StdioServerTransportProvider;
import io.modelcontextprotocol.spec.McpSchema.*;
import com.opencare.mcp.service.ClassFinderService;
import com.opencare.mcp.service.SourceCodeService;

import java.time.Duration;
import java.util.List;
import java.util.Map;

/**
 * Gradle Class Finder MCP Server
 * 基于MCP协议的Gradle类查找服务器，支持在Gradle项目依赖中查找和反编译Java类
 */
public class GradleClassFinderMcpServer {
    
    private final ClassFinderService classFinderService;
    private final SourceCodeService sourceCodeService;
    
    public GradleClassFinderMcpServer() {
        this.classFinderService = new ClassFinderService();
        this.sourceCodeService = new SourceCodeService();
    }
    
    public static void main(String[] args) {
        new GradleClassFinderMcpServer().start();
    }
    
    public void start() {
        StdioServerTransportProvider transportProvider = new StdioServerTransportProvider();
        
        // 定义find_class工具
        Tool findClassTool = new Tool(
            "find_class",
            "在Gradle项目依赖中查找指定的类",
            """
            {
                "type": "object",
                "properties": {
                    "workspace_dir": {
                        "type": "string",
                        "description": "Gradle项目根目录路径"
                    },
                    "class_name": {
                        "type": "string",
                        "description": "要查找的类的全限定名 (例如: com.example.MyClass)"
                    },
                    "submodule_path": {
                        "type": "string",
                        "description": "子模块路径 (可选)",
                        "default": null
                    }
                },
                "required": ["workspace_dir", "class_name"]
            }
            """
        );
        
        // 定义get_source_code工具
        Tool getSourceCodeTool = new Tool(
            "get_source_code",
            "获取指定类的源代码或反编译代码",
            """
            {
                "type": "object",
                "properties": {
                    "jar_path": {
                        "type": "string",
                        "description": "JAR文件的完整路径"
                    },
                    "class_name": {
                        "type": "string",
                        "description": "类的全限定名"
                    },
                    "line_start": {
                        "type": "integer",
                        "description": "起始行号 (可选)",
                        "minimum": 1
                    },
                    "line_end": {
                        "type": "integer",
                        "description": "结束行号 (可选)",
                        "minimum": 1
                    }
                },
                "required": ["jar_path", "class_name"]
            }
            """
        );
        
        // 创建MCP服务器
        var mcpServer = McpServer.sync(transportProvider)
            .serverInfo("gradle-class-finder", "1.0.0")
            .capabilities(ServerCapabilities.builder()
                .tools(true)
                .logging()
                .build())
            .requestTimeout(Duration.ofSeconds(120))
            
            // 注册find_class工具
            .tool(findClassTool, (exchange, args) -> {
                try {
                    String workspaceDir = (String) args.get("workspace_dir");
                    String className = (String) args.get("class_name");
                    String submodulePath = (String) args.get("submodule_path");
                    
                    System.err.println("[INFO] 查找类: " + className + " 在项目: " + workspaceDir);
                    
                    List<ClassFinderService.MatchResult> results = 
                        classFinderService.findClassInProject(workspaceDir, className, submodulePath);
                    
                    if (results.isEmpty()) {
                        return new CallToolResult(
                            List.of(new TextContent("未找到类: " + className)), 
                            false
                        );
                    }
                    
                    StringBuilder response = new StringBuilder();
                    response.append("找到 ").append(results.size()).append(" 个匹配项:\n\n");
                    
                    for (int i = 0; i < results.size(); i++) {
                        ClassFinderService.MatchResult result = results.get(i);
                        response.append(String.format("%d. %s\n", i + 1, result.className));
                        response.append(String.format("   JAR路径: %s\n", result.jarPath));
                        response.append(String.format("   依赖坐标: %s\n", result.dependencyCoordinates));
                        if (result.sourceJarPath != null) {
                            response.append(String.format("   源码JAR: %s\n", result.sourceJarPath));
                        }
                        if (result.isLocal) {
                            response.append("   类型: 本地源码\n");
                        }
                        response.append("\n");
                    }
                    
                    return new CallToolResult(
                        List.of(new TextContent(response.toString())), 
                        false
                    );
                    
                } catch (Exception e) {
                    System.err.println("[ERROR] 查找类失败: " + e.getMessage());
                    e.printStackTrace();
                    return new CallToolResult(
                        List.of(new TextContent("查找失败: " + e.getMessage())), 
                        true
                    );
                }
            })
            
            // 注册get_source_code工具
            .tool(getSourceCodeTool, (exchange, args) -> {
                try {
                    String jarPath = (String) args.get("jar_path");
                    String className = (String) args.get("class_name");
                    Integer lineStart = (Integer) args.get("line_start");
                    Integer lineEnd = (Integer) args.get("line_end");
                    
                    System.err.println("[INFO] 获取源码: " + className + " 来自: " + jarPath);
                    
                    String sourceCode = sourceCodeService.getSourceCode(jarPath, className, lineStart, lineEnd);
                    
                    return new CallToolResult(
                        List.of(new TextContent("```java\n" + sourceCode + "\n```")), 
                        false
                    );
                    
                } catch (Exception e) {
                    System.err.println("[ERROR] 获取源码失败: " + e.getMessage());
                    e.printStackTrace();
                    return new CallToolResult(
                        List.of(new TextContent("获取源码失败: " + e.getMessage())), 
                        true
                    );
                }
            })
            
            .build();
        
        System.err.println("Gradle Class Finder MCP Server 启动完成，正在监听stdin/stdout");
        System.err.println("服务器信息: gradle-class-finder v1.0.0");
        System.err.println("支持的工具: find_class, get_source_code");
        
        // 优雅关闭处理
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            System.err.println("正在关闭 MCP Server...");
            mcpServer.closeGracefully();
        }));
        
        // 保持程序运行
        try {
            Thread.currentThread().join();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}