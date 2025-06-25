#!/usr/bin/env python3

import sys
import asyncio
from server import server, finder, list_tools

async def test_mcp():
    print("Testing MCP Server...")
    
    # Test 1: List tools
    tools = await list_tools()
    print(f"\n✓ Found {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Test 2: Test imports
    print("\n✓ All imports successful")
    
    # Test 3: Test finder initialization
    print(f"\n✓ GradleClassFinder initialized")
    print(f"  CFR path will be: {finder.cfr_path}")
    
    print("\n✅ MCP server is ready to start!")
    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_mcp())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)