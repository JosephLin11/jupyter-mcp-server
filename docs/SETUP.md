# 🚀 Setup Guide

This guide will help you set up the Jupyter MCP Server for use with Claude Desktop or other MCP-compatible clients.

## 📋 Prerequisites

- **Python 3.11+** - Required for async features and type hints
- **Jupyter Notebook** - For running the notebook server
- **Claude Desktop** - Or another MCP-compatible client

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/jupyter-mcp-server.git
cd jupyter-mcp-server
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n jupyter-mcp python=3.11
conda activate jupyter-mcp
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e ".[dev]"
```

## 🎯 Configuration

### 1. Start Jupyter Server

Use the provided script for easy setup:

```bash
./scripts/start_jupyter.sh
```

Or start manually with the correct parameters:

```bash
jupyter notebook \
    --port=8888 \
    --no-browser \
    --allow-root \
    --NotebookApp.token='' \
    --NotebookApp.password='' \
    --NotebookApp.disable_check_xsrf=True \
    --ip=127.0.0.1
```

### 2. Configure Claude Desktop

1. **Find your Claude Desktop config file:**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add the MCP server configuration:**

```json
{
  "mcpServers": {
    "jupyter": {
      "command": "python",
      "args": ["/Users/joseph/Documents/personal_projects/jupyter-mcp-server/src/jupyter_mcp_server.py"],
      "env": {
        "JUPYTER_URL": "http://localhost:8888",
        "JUPYTER_TOKEN": ""
      }
    }
  }
}
```

3. **Update the path** to match your installation directory

4. **Restart Claude Desktop** completely (File → Exit, then reopen)

💡 **Quick Setup Tip**: Run `python3 scripts/get_claude_config.py` from the project directory to generate the correct configuration with current paths!

## ✅ Verification

### 1. Test the Connection

Ask Claude to run this command:
```
get_notebook_info
```

You should see information about the current notebook.

### 2. Test Code Execution

Ask Claude to:
```
Execute this Python code:
print("Hello from Jupyter MCP Server!")
import numpy as np
print(f"NumPy version: {np.__version__}")
```

### 3. Test Image Generation

Ask Claude to:
```
Create a simple plot and extract the image:

import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y)
plt.title('Test Plot')
plt.show()

Then extract the image from the cell.
```

## 🔧 Troubleshooting

### Common Issues

#### 1. "Cannot connect to Jupyter server"
- Ensure Jupyter is running on port 8888
- Check that no firewall is blocking the connection
- Verify the Jupyter URL in your configuration

#### 2. "XSRF token error"
- Use the provided startup script which handles XSRF correctly
- Ensure `--NotebookApp.disable_check_xsrf=True` is set

#### 3. "Module not found" errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that you're using Python 3.11+

#### 4. Claude doesn't see the MCP server
- Verify the path in `claude_desktop_config.json` is absolute and correct
- Restart Claude Desktop completely
- Check Claude's developer console for error messages

### Debug Mode

Run the server with debug logging:

```bash
PYTHONPATH=src python src/jupyter_mcp_server.py --debug
```

### Test Without Claude

Run the test suite to verify functionality:

```bash
# Test image extraction
python tests/test_image_extraction.py

# Test notebook operations
python tests/test_notebook_save.py
```

## 🎯 Advanced Configuration

### Custom Jupyter Server

If you're using a different Jupyter setup:

```json
{
  "mcpServers": {
    "jupyter": {
      "command": "python",
      "args": ["/Users/joseph/Documents/personal_projects/jupyter-mcp-server/src/jupyter_mcp_server.py"],
      "env": {
        "JUPYTER_URL": "http://your-server:8888",
        "JUPYTER_TOKEN": "your-token-here"
      }
    }
  }
}
```

### Multiple Notebook Directories

The server works with the directory where it's started. To use a specific directory:

```bash
cd /path/to/your/notebooks
python /Users/joseph/Documents/personal_projects/jupyter-mcp-server/src/jupyter_mcp_server.py
```

## 🚀 Next Steps

Once everything is working:

1. **Explore the tools** - See [MCP_TOOLS_SUMMARY.md](MCP_TOOLS_SUMMARY.md) for all available commands
2. **Try image extraction** - See [IMAGE_EXTRACTION_README.md](IMAGE_EXTRACTION_README.md) for advanced features
3. **Create notebooks** - Use the file management tools to organize your work
4. **Build workflows** - Combine tools for complex data science tasks

## 📞 Getting Help

If you encounter issues:

1. Check this troubleshooting guide
2. Review the [main README](../README.md) for examples
3. Open an issue on GitHub with:
   - Your operating system
   - Python version
   - Error messages
   - Steps to reproduce

Happy coding! 🎉 