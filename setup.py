#!/usr/bin/env python3

import os
import urllib.request
from pathlib import Path

def download_cfr():
    """下载CFR反编译器"""
    cache_dir = Path.home() / ".gradle-class-finder-mcp"
    cache_dir.mkdir(exist_ok=True)
    
    cfr_path = cache_dir / "cfr.jar"
    
    if not cfr_path.exists():
        print("Downloading CFR decompiler...")
        # CFR最新版本
        cfr_url = "https://github.com/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar"
        
        try:
            urllib.request.urlretrieve(cfr_url, cfr_path)
            print(f"CFR downloaded to: {cfr_path}")
        except Exception as e:
            print(f"Failed to download CFR: {e}")
            print("You can manually download it from: https://www.benf.org/other/cfr/")
    else:
        print(f"CFR already exists at: {cfr_path}")

if __name__ == "__main__":
    download_cfr()
    print("\nSetup complete!")
    print("\nTo use the MCP service:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run with nvx: nvx gradle-class-finder")