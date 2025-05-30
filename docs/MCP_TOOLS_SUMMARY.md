# Jupyter MCP Server - Complete Tool Reference

## 🎯 **Enhanced Jupyter MCP Server with Full Notebook Management**

The MCP server now provides **18 comprehensive tools** for complete Jupyter notebook management and manipulation.

---

## 📝 **Cell Content Tools**

### **add_execute_code_cell**
- **Description**: Add and execute a code cell in a Jupyter notebook
- **Parameters**: 
  - `cell_content` (required): Code content to execute
  - `position` (optional): Position to insert cell

### **add_markdown_cell**
- **Description**: Add a markdown cell in a Jupyter notebook  
- **Parameters**:
  - `cell_content` (required): Markdown content
  - `position` (optional): Position to insert cell

---

## ✏️ **Cell Editing Tools**

### **modify_cell**
- **Description**: Modify the content of an existing cell
- **Parameters**:
  - `cell_index` (required): Index of cell to modify (0-based)
  - `new_content` (required): New content for the cell

### **change_cell_type**
- **Description**: Change the type of a cell (markdown/code)
- **Parameters**:
  - `cell_index` (required): Index of cell to change (0-based)
  - `new_type` (required): New cell type ("markdown" or "code")

### **move_cell**
- **Description**: Move a cell to a different position
- **Parameters**:
  - `from_index` (required): Current index of cell to move (0-based)
  - `to_index` (required): Target index position (0-based)

---

## 🗑️ **Cell Deletion Tools**

### **delete_cell**
- **Description**: Delete a specific cell from the notebook by index
- **Parameters**:
  - `cell_index` (required): Index of cell to delete (0-based)

### **clear_notebook**
- **Description**: Clear all cells from the notebook except one and replace with custom content
- **Parameters**:
  - `content` (required): Content for the single remaining cell
  - `cell_type` (optional): Type of the remaining cell ("markdown" or "code")

---

## 📖 **Cell Reading Tools**

### **list_cells**
- **Description**: List all cells in the notebook with their types and content preview
- **Parameters**:
  - `preview_length` (optional): Length of content preview (default: 100)

### **read_cell**
- **Description**: Read the full content of a specific cell
- **Parameters**:
  - `cell_index` (required): Index of cell to read (0-based)

### **get_notebook_info**
- **Description**: Get comprehensive information about the current notebook
- **Parameters**: None

---

## 🖼️ **Cell Output Tools** *(NEW!)*

### **get_cell_image_output**
- **Description**: Get the image output of a specific cell
- **Parameters**:
  - `cell_index` (required): Index of cell to get image output from (0-based)
- **Returns**: Base64-encoded image data for PNG/JPEG images

### **get_cell_text_output**
- **Description**: Get the text output of a specific cell
- **Parameters**:
  - `cell_index` (required): Index of cell to get text output from (0-based)
- **Returns**: All text outputs including stdout, execution results, and error messages

---

## 🗂️ **Notebook File Management Tools**

### **create_notebook**
- **Description**: Create a new Jupyter notebook file
- **Parameters**:
  - `filename` (required): Name of the notebook file (with .ipynb extension)
  - `initial_content` (optional): Initial content for the first cell
  - `cell_type` (optional): Type of the initial cell ("markdown" or "code")

### **delete_notebook**
- **Description**: Delete a notebook file from the filesystem
- **Parameters**:
  - `filename` (required): Name of the notebook file to delete
- **Safety**: Cannot delete currently active notebook

### **list_notebooks**
- **Description**: List all notebook files in the current directory
- **Parameters**: None
- **Shows**: File sizes, modification dates, current active notebook

### **switch_notebook**
- **Description**: Switch to working with a different notebook file
- **Parameters**:
  - `filename` (required): Name of the notebook file to switch to

### **get_current_notebook**
- **Description**: Get the name of the currently active notebook
- **Parameters**: None

---

## 🔧 **System Requirements**

- **Jupyter Server**: Must be running on `http://localhost:8888`
- **Python**: 3.11+ with required packages
- **Dependencies**: `mcp`, `nbformat`, `websockets`, `httpx`

## 📋 **Usage Examples**

```python
# Create a new notebook with matplotlib visualization
create_notebook(filename="visualization.ipynb", initial_content="# Data Visualization", cell_type="markdown")
switch_notebook(filename="visualization.ipynb")

# Add code that generates a plot
add_execute_code_cell(cell_content="""
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y)
plt.title('Sine Wave')
plt.show()
""")

# Get the image output from the executed cell
get_cell_image_output(cell_index=1)

# Get text output if any
get_cell_text_output(cell_index=1)
```

---

## ✅ **Status: Fully Operational**

- ✅ **18 Tools Available**
- ✅ **Claude Desktop Compatible** 
- ✅ **Real-time Code Execution**
- ✅ **Image Output Extraction** *(NEW!)*
- ✅ **Text Output Extraction** *(NEW!)*
- ✅ **File System Management**
- ✅ **Safety Checks Implemented**
- ✅ **Comprehensive Error Handling**

**Your Jupyter MCP Server is now a complete notebook management solution with image extraction capabilities!** 🎉 🖼️ 