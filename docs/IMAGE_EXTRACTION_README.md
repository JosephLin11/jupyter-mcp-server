# 🖼️ Image Extraction Features

Your Jupyter MCP Server now includes powerful image extraction capabilities inspired by the jjsantos01 implementation! This allows Claude to not only execute code that generates visualizations but also extract and work with the resulting images.

## ✨ New Features

### 🎯 **get_cell_image_output**
Extract base64-encoded images (PNG/JPEG) from executed cells.

```python
# Example: Get image from a matplotlib plot
get_cell_image_output(cell_index=2)
```

### 📝 **get_cell_text_output** 
Extract all text outputs from executed cells including stdout, results, and errors.

```python
# Example: Get text output from a data analysis cell
get_cell_text_output(cell_index=1)
```

## 🚀 Quick Start

### 1. Start Jupyter Server
```bash
./start_jupyter.sh
```

Or manually:
```bash
jupyter notebook --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.disable_check_xsrf=True
```

### 2. Test Image Generation
Ask Claude to:
```
Execute this code and then extract the image:

import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x) * np.exp(-x/10)

plt.figure(figsize=(10, 6))
plt.plot(x, y, 'b-', linewidth=2)
plt.title('Damped Sine Wave')
plt.xlabel('x')
plt.ylabel('y')
plt.grid(True, alpha=0.3)
plt.show()
```

### 3. Extract the Image
Claude can then run:
```
get_cell_image_output(cell_index=1)  # or whatever cell index contains the plot
```

## 🔧 Technical Details

### Image Format Support
- **PNG**: Primary format for matplotlib plots
- **JPEG**: Secondary format support
- **Base64 Encoding**: Images are returned as base64-encoded strings

### Output Types Captured
- **execute_result**: Direct return values with images
- **display_data**: Display outputs (plots, widgets, etc.)
- **stream**: Text output (stdout/stderr)
- **error**: Exception information with tracebacks

### Enhanced WebSocket Handling
The image extraction works by:
1. **Capturing All Output Types**: During code execution via WebSocket
2. **Storing Raw Data**: Preserving original base64 image data
3. **Organizing by Type**: Separating text, images, and errors
4. **Providing Extraction Tools**: Dedicated functions for accessing specific output types

## 📊 Example Use Cases

### Data Visualization Analysis
```python
# 1. Generate multiple plots
add_execute_code_cell(cell_content="""
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

# Load sample data
tips = sns.load_dataset('tips')

fig, axes = plt.subplots(2, 2, figsize=(12, 10))
sns.scatterplot(data=tips, x='total_bill', y='tip', ax=axes[0,0])
sns.boxplot(data=tips, x='day', y='total_bill', ax=axes[0,1])
sns.histplot(data=tips, x='tip', ax=axes[1,0])
sns.barplot(data=tips, x='day', y='tip', ax=axes[1,1])
plt.tight_layout()
plt.show()
""")

# 2. Extract the complex visualization
get_cell_image_output(cell_index=0)
```

### Scientific Computing
```python
# 1. Create scientific visualization
add_execute_code_cell(cell_content="""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 3D surface plot
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

x = np.linspace(-5, 5, 50)
y = np.linspace(-5, 5, 50)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2))

surface = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.9)
ax.set_title('3D Sine Function')
plt.colorbar(surface)
plt.show()
""")

# 2. Extract 3D visualization
get_cell_image_output(cell_index=0)
```

## 🔍 Debugging & Troubleshooting

### No Images Found?
```python
# Check what outputs exist
list_cells()  # See all cells
get_cell_text_output(cell_index=X)  # Check for errors
```

### Image Not Displaying?
- Ensure `plt.show()` is called
- Check if running in headless environment
- Verify matplotlib backend: `matplotlib.use('Agg')`

### Testing the Feature
```bash
# Run the test script
python test_image_extraction.py
```

## 🎯 Comparison with Other Implementations

| Feature | Your Enhanced MCP | jjsantos01 MCP | Cursor MCP |
|---------|-------------------|----------------|------------|
| **Image Extraction** | ✅ Base64 PNG/JPEG | ✅ Base64 PNG | ❌ File-only |
| **Text Output** | ✅ All output types | ✅ Limited to 1500 chars | ❌ File-only |
| **Real-time Execution** | ✅ WebSocket + HTTP | ✅ WebSocket bridge | ❌ No execution |
| **Multiple Image Formats** | ✅ PNG + JPEG | ❌ PNG only | ❌ No images |
| **Error Handling** | ✅ Full traceback | ✅ Basic errors | ❌ No execution errors |

## 🚀 Future Enhancements

Possible additions inspired by other implementations:
- **SVG Support**: Vector graphics extraction
- **Interactive Widget Outputs**: Plotly, Bokeh support
- **Output Size Limits**: Configurable limits like Cursor MCP
- **Image Metadata**: Dimensions, format info
- **Batch Extraction**: Get all images from notebook

---

**Your Jupyter MCP Server now provides the best of all worlds: comprehensive management + real-time execution + image extraction!** 🎉🖼️ 