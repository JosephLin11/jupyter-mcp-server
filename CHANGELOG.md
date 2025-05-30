<!--
  ~ Copyright (c) 2023-2024 Datalayer, Inc.
  ~
  ~ BSD 3-Clause License
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-XX

### 🚀 **Major Features Added**
- **Image Extraction System**: Extract base64-encoded images (PNG/JPEG) from notebook cells
- **Enhanced Output Processing**: Comprehensive capture of all Jupyter output types
- **Advanced WebSocket Implementation**: Real-time bidirectional communication with kernels
- **Smart XSRF Handling**: Automatic token detection and management

### ✨ **New Tools**
- `get_cell_image_output` - Extract images from executed cells
- `get_cell_text_output` - Get comprehensive text outputs including errors

### 🔧 **Technical Improvements**
- Structured output capture preserving metadata
- Multi-format image support (PNG, JPEG)
- Enhanced error handling with full traceback support
- Automatic reconnection and fallback mechanisms

### 📚 **Documentation**
- Complete project restructure with professional organization
- Comprehensive README with usage examples
- Detailed tool documentation
- Image extraction guide

### 🛡️ **Security**
- Improved XSRF token handling
- Multiple authentication endpoint support
- Graceful degradation for different Jupyter configurations

## [1.0.0] - 2024-11-XX

### 🎉 **Initial Release**
- Basic MCP server implementation
- Core Jupyter integration via HTTP API
- WebSocket support for real-time execution
- 16 fundamental tools for notebook management

### 📝 **Cell Operations**
- `add_execute_code_cell` - Execute Python code in notebooks
- `add_markdown_cell` - Add markdown content
- `modify_cell` - Edit existing cells
- `change_cell_type` - Convert between cell types
- `move_cell` - Reorder cells
- `delete_cell` - Remove cells

### 🗂️ **File Management**
- `create_notebook` - Create new notebook files
- `delete_notebook` - Remove notebook files
- `switch_notebook` - Change active notebook
- `list_notebooks` - Browse available notebooks

### 🔍 **Content Discovery**
- `list_cells` - Overview of notebook structure
- `read_cell` - Read specific cell content
- `get_notebook_info` - Notebook metadata
- `clear_notebook` - Reset notebook content

### 🏗️ **Infrastructure**
- Kernel lifecycle management
- Session persistence
- HTTP client with timeout handling
- Basic error recovery
