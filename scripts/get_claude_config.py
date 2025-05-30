#!/usr/bin/env python3
"""
Helper script to generate the correct Claude Desktop configuration
"""

import os
import json

def main():
    # Get the current directory
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server_path = os.path.join(current_dir, "src", "jupyter_mcp_server.py")
    
    config = {
        "mcpServers": {
            "jupyter": {
                "command": "python",
                "args": [server_path],
                "env": {
                    "JUPYTER_URL": "http://localhost:8888",
                    "JUPYTER_TOKEN": ""
                }
            }
        }
    }
    
    print("🔧 Claude Desktop Configuration")
    print("=" * 50)
    print("Add this to your claude_desktop_config.json file:")
    print("(Located at ~/Library/Application Support/Claude/claude_desktop_config.json on macOS)")
    print()
    print(json.dumps(config, indent=2))
    print()
    print("📍 Server path:", server_path)
    print("✅ Path exists:", os.path.exists(server_path))

if __name__ == "__main__":
    main() 