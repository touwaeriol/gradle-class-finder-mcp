#!/usr/bin/env python3

"""
本地测试脚本，用于验证功能
"""

from server import GradleClassFinder
import sys

def test_find_class():
    if len(sys.argv) < 3:
        print("Usage: python test_local.py <gradle_project_dir> <class_name>")
        print("Example: python test_local.py /path/to/project org.springframework.stereotype.Component")
        return
    
    workspace_dir = sys.argv[1]
    class_name = sys.argv[2]
    
    finder = GradleClassFinder()
    
    print(f"Searching for class: {class_name}")
    print(f"In workspace: {workspace_dir}")
    print("-" * 50)
    
    # 查找类
    results = finder.find_class_in_dependencies(workspace_dir, class_name)
    
    if results:
        print(f"Found {len(results)} occurrence(s):")
        for i, result in enumerate(results):
            print(f"\n{i+1}. {result['dependency']}")
            print(f"   JAR: {result['jar_path']}")
            
            # 获取元信息
            metadata = finder.get_class_metadata(result['jar_path'], class_name)
            print(f"   Lines: {metadata['total_lines']}")
            print(f"   Methods: {metadata['methods_count']}")
            
            # 显示前几行源代码
            if i == 0:  # 只显示第一个结果的源代码
                print("\n   First 20 lines of decompiled source:")
                print("   " + "-" * 40)
                source = finder.decompile_class(result['jar_path'], class_name, 1, 20)
                for line in source.split('\n'):
                    print(f"   {line}")
    else:
        print("Class not found in dependencies")

if __name__ == "__main__":
    test_find_class()