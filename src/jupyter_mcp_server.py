#!/usr/bin/env python3.11
"""
Jupyter MCP Server - A Model Context Protocol server for Jupyter integration
Uses official MCP SDK and proper Jupyter Server API endpoints
"""

import asyncio
import json
import logging
import os
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
import base64

import httpx
import websockets
from mcp.server import Server
from mcp.server.models import InitializationOptions, ServerCapabilities
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    EmbeddedResource,
    ImageContent,
    ListResourcesRequest,
    ListToolsRequest,
    ReadResourceRequest,
    TextContent,
    Tool,
    PromptsCapability,
    ResourcesCapability,
    ToolsCapability
)
from pydantic import AnyUrl
import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("jupyter-mcp")

class JupyterMCPServer:
    """Jupyter MCP Server with proper API endpoint usage"""
    
    def __init__(self, jupyter_url: str = "http://localhost:8888", token: str = ""):
        self.jupyter_url = jupyter_url.rstrip('/')
        self.token = token
        self.session_id = None
        self.kernel_id = None
        self._xsrf_token: Optional[str] = None
        
        # Set up notebooks directory - go up one level from src and use notebooks folder
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)  # Go up from src/ to project root
        self.base_dir = os.path.join(project_root, "notebooks")
        
        # Create notebooks directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Change to notebooks directory for all operations
        os.chdir(self.base_dir)
        logger.info(f"Working directory set to: {self.base_dir}")
        
        # Current notebook will be in the notebooks directory
        self.current_notebook_path: str = os.path.join(self.base_dir, "mcp_notebook.ipynb")
        self.current_notebook: Optional[nbformat.NotebookNode] = None
        
        # HTTP client for API requests
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True
        )
        
        # Initialize MCP server
        self.server = Server("jupyter-mcp")
        
        # Register handlers
        self._register_handlers()
        
        # Initialize notebook
        self._init_notebook()
        
        # Log initialization info
        logger.info(f"Base directory: {self.base_dir}")
        logger.info(f"Current notebook: {self.current_notebook_path}")
    
    def _register_handlers(self):
        """Register MCP handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="add_execute_code_cell",
                    description="Add and execute a code cell in a Jupyter notebook",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cell_content": {
                                "type": "string",
                                "description": "Code content to execute",
                                "title": "Cell Content"
                            },
                            "position": {
                                "type": "integer",
                                "description": "Position to insert cell (optional, defaults to end)",
                                "title": "Position"
                            }
                        },
                        "required": ["cell_content"],
                        "title": "add_execute_code_cellArguments"
                    }
                ),
                Tool(
                    name="add_markdown_cell", 
                    description="Add a markdown cell in a Jupyter notebook",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cell_content": {
                                "type": "string",
                                "description": "Markdown content",
                                "title": "Cell Content"
                            },
                            "position": {
                                "type": "integer",
                                "description": "Position to insert cell (optional, defaults to end)",
                                "title": "Position"
                            }
                        },
                        "required": ["cell_content"],
                        "title": "add_markdown_cellArguments"
                    }
                ),
                Tool(
                    name="delete_cell",
                    description="Delete a specific cell from the notebook by index",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cell_index": {
                                "type": "integer",
                                "description": "Index of cell to delete (0-based)",
                                "title": "Cell Index"
                            }
                        },
                        "required": ["cell_index"],
                        "title": "delete_cellArguments"
                    }
                ),
                Tool(
                    name="modify_cell",
                    description="Modify the content of an existing cell",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cell_index": {
                                "type": "integer",
                                "description": "Index of cell to modify (0-based)",
                                "title": "Cell Index"
                            },
                            "new_content": {
                                "type": "string",
                                "description": "New content for the cell",
                                "title": "New Content"
                            }
                        },
                        "required": ["cell_index", "new_content"],
                        "title": "modify_cellArguments"
                    }
                ),
                Tool(
                    name="change_cell_type",
                    description="Change the type of a cell (markdown/code)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cell_index": {
                                "type": "integer",
                                "description": "Index of cell to change (0-based)",
                                "title": "Cell Index"
                            },
                            "new_type": {
                                "type": "string",
                                "enum": ["markdown", "code"],
                                "description": "New cell type",
                                "title": "New Type"
                            }
                        },
                        "required": ["cell_index", "new_type"],
                        "title": "change_cell_typeArguments"
                    }
                ),
                Tool(
                    name="move_cell",
                    description="Move a cell to a different position",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "from_index": {
                                "type": "integer",
                                "description": "Current index of cell to move (0-based)",
                                "title": "From Index"
                            },
                            "to_index": {
                                "type": "integer",
                                "description": "Target index position (0-based)",
                                "title": "To Index"
                            }
                        },
                        "required": ["from_index", "to_index"],
                        "title": "move_cellArguments"
                    }
                ),
                Tool(
                    name="clear_notebook",
                    description="Clear all cells from the notebook except one and replace with custom content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Content for the single remaining cell",
                                "title": "Content"
                            },
                            "cell_type": {
                                "type": "string",
                                "enum": ["markdown", "code"],
                                "description": "Type of the remaining cell (default: markdown)",
                                "title": "Cell Type"
                            }
                        },
                        "required": ["content"],
                        "title": "clear_notebookArguments"
                    }
                ),
                Tool(
                    name="get_notebook_info",
                    description="Get comprehensive information about the current notebook",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "title": "get_notebook_infoArguments"
                    }
                ),
                Tool(
                    name="list_cells",
                    description="List all cells in the notebook with their types and content preview",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "preview_length": {
                                "type": "integer",
                                "description": "Length of content preview (default: 100)",
                                "title": "Preview Length"
                            }
                        },
                        "title": "list_cellsArguments"
                    }
                ),
                Tool(
                    name="read_cell",
                    description="Read the full content of a specific cell",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cell_index": {
                                "type": "integer",
                                "description": "Index of cell to read (0-based)",
                                "title": "Cell Index"
                            }
                        },
                        "required": ["cell_index"],
                        "title": "read_cellArguments"
                    }
                ),
                Tool(
                    name="create_notebook",
                    description="Create a new Jupyter notebook file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Name of the notebook file (with .ipynb extension)",
                                "title": "Filename"
                            },
                            "initial_content": {
                                "type": "string",
                                "description": "Initial content for the first cell (optional)",
                                "title": "Initial Content"
                            },
                            "cell_type": {
                                "type": "string",
                                "enum": ["markdown", "code"],
                                "description": "Type of the initial cell (default: markdown)",
                                "title": "Cell Type"
                            }
                        },
                        "required": ["filename"],
                        "title": "create_notebookArguments"
                    }
                ),
                Tool(
                    name="delete_notebook",
                    description="Delete a notebook file from the filesystem",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Name of the notebook file to delete",
                                "title": "Filename"
                            }
                        },
                        "required": ["filename"],
                        "title": "delete_notebookArguments"
                    }
                ),
                Tool(
                    name="list_notebooks",
                    description="List all notebook files in the current directory",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "title": "list_notebooksArguments"
                    }
                ),
                Tool(
                    name="switch_notebook",
                    description="Switch to working with a different notebook file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Name of the notebook file to switch to",
                                "title": "Filename"
                            }
                        },
                        "required": ["filename"],
                        "title": "switch_notebookArguments"
                    }
                ),
                Tool(
                    name="get_current_notebook",
                    description="Get the name of the currently active notebook",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "title": "get_current_notebookArguments"
                    }
                ),
                Tool(
                    name="get_cell_image_output",
                    description="Get the image output of a specific cell",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cell_index": {
                                "type": "integer",
                                "description": "Index of cell to get image output from (0-based)",
                                "title": "Cell Index"
                            }
                        },
                        "required": ["cell_index"],
                        "title": "get_cell_image_outputArguments"
                    }
                ),
                Tool(
                    name="get_cell_text_output",
                    description="Get the text output of a specific cell",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "cell_index": {
                                "type": "integer",
                                "description": "Index of cell to get text output from (0-based)",
                                "title": "Cell Index"
                            }
                        },
                        "required": ["cell_index"],
                        "title": "get_cell_text_outputArguments"
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                logger.info(f"Calling tool: {name} with arguments: {arguments}")
                
                # Ensure Jupyter connection before executing tools
                if not await self._ensure_jupyter_connection():
                    return [TextContent(type="text", text="Error: Cannot connect to Jupyter server. Please ensure Jupyter is running on http://localhost:8888")]
                
                if name == "add_execute_code_cell":
                    result = await self._execute_code(
                        arguments.get("cell_content", ""),
                        "python3",
                        position=arguments.get("position")
                    )
                elif name == "add_markdown_cell":
                    result = await self._add_markdown_cell(
                        arguments.get("cell_content", ""),
                        position=arguments.get("position")
                    )
                elif name == "delete_cell":
                    result = await self._delete_cell(
                        arguments.get("cell_index")
                    )
                elif name == "modify_cell":
                    result = await self._modify_cell(
                        arguments.get("cell_index"),
                        arguments.get("new_content", "")
                    )
                elif name == "change_cell_type":
                    result = await self._change_cell_type(
                        arguments.get("cell_index"),
                        arguments.get("new_type", "markdown")
                    )
                elif name == "move_cell":
                    result = await self._move_cell(
                        arguments.get("from_index"),
                        arguments.get("to_index")
                    )
                elif name == "clear_notebook":
                    result = await self._clear_notebook(
                        arguments.get("content", ""),
                        cell_type=arguments.get("cell_type", "markdown")
                    )
                elif name == "get_notebook_info":
                    result = await self._get_notebook_info()
                elif name == "list_cells":
                    result = await self._list_cells(
                        preview_length=arguments.get("preview_length", 100)
                    )
                elif name == "read_cell":
                    result = await self._read_cell(
                        arguments.get("cell_index")
                    )
                elif name == "create_notebook":
                    result = await self._create_notebook(
                        arguments.get("filename"),
                        arguments.get("initial_content"),
                        arguments.get("cell_type", "markdown")
                    )
                elif name == "delete_notebook":
                    result = await self._delete_notebook(
                        arguments.get("filename")
                    )
                elif name == "list_notebooks":
                    result = await self._list_notebooks()
                elif name == "switch_notebook":
                    result = await self._switch_notebook(
                        arguments.get("filename")
                    )
                elif name == "get_current_notebook":
                    result = await self._get_current_notebook()
                elif name == "get_cell_image_output":
                    result = await self._get_cell_image_output(
                        arguments.get("cell_index")
                    )
                elif name == "get_cell_text_output":
                    result = await self._get_cell_text_output(
                        arguments.get("cell_index")
                    )
                else:
                    result = f"Unknown tool: {name}"
                
                logger.info(f"Tool {name} completed successfully")
                return [TextContent(type="text", text=str(result))]
                
            except Exception as e:
                error_msg = f"Error executing tool {name}: {str(e)}"
                logger.error(error_msg)
                return [TextContent(type="text", text=error_msg)]
        
        @self.server.list_resources()
        async def handle_list_resources():
            """List available resources"""
            from mcp.types import Resource
            return [
                Resource(
                    uri=AnyUrl(f"notebook://{self.current_notebook_path}"),
                    name="Current Notebook",
                    description="The current Jupyter notebook being managed",
                    mimeType="application/x-ipynb+json"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: AnyUrl) -> str:
            """Read a resource"""
            try:
                if str(uri).startswith("notebook://"):
                    notebook_path = str(uri).replace("notebook://", "")
                    if self.current_notebook:
                        return json.dumps(nbformat.to_dict(self.current_notebook), indent=2)
                    else:
                        return "No notebook loaded"
                else:
                    return f"Unsupported resource URI: {uri}"
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return f"Error reading resource: {str(e)}"
        
        @self.server.list_prompts()
        async def handle_list_prompts():
            """List available prompts"""
            from mcp.types import Prompt
            return [
                Prompt(
                    name="notebook_status",
                    description="Get the current status of the Jupyter notebook",
                ),
                Prompt(
                    name="create_notebook",
                    description="Create a new Jupyter notebook with initial cells",
                )
            ]
    
    def _get_auth_params(self) -> Dict[str, str]:
        """Get authentication parameters for API requests"""
        return {"token": self.token} if self.token else {}
    
    async def _get_xsrf_token(self) -> str:
        """Get CSRF token from Jupyter server"""
        if self._xsrf_token:
            return self._xsrf_token
        
        # List of endpoints to try for getting CSRF token
        endpoints = ["/", "/tree", "/api/kernels", "/api/sessions", "/lab", "/api/me"]
        
        for endpoint in endpoints:
            try:
                response = await self.client.get(
                    urljoin(self.jupyter_url, endpoint), 
                    params=self._get_auth_params(),
                    follow_redirects=True
                )
                # Don't require 200 status - even errors can return CSRF tokens
                
                # Extract CSRF token from cookies first
                for cookie in response.cookies.jar:
                    if cookie.name == '_xsrf':
                        self._xsrf_token = cookie.value
                        logger.info(f"Found CSRF token from {endpoint} cookies: {self._xsrf_token[:10]}...")
                        return self._xsrf_token
                
                # Try to extract from Set-Cookie header
                set_cookie = response.headers.get('Set-Cookie', '')
                if '_xsrf=' in set_cookie:
                    import re
                    xsrf_match = re.search(r'_xsrf=([^;]+)', set_cookie)
                    if xsrf_match:
                        self._xsrf_token = xsrf_match.group(1)
                        logger.info(f"Extracted CSRF token from {endpoint} header: {self._xsrf_token[:10]}...")
                        return self._xsrf_token
                        
            except Exception as e:
                logger.debug(f"Failed to get CSRF token from {endpoint}: {e}")
                continue
        
        # If we can't get a token, try without one but log it
        logger.warning("Could not obtain CSRF token - trying requests without CSRF protection")
        return ""
    
    async def _list_kernels(self) -> str:
        """List available kernels"""
        try:
            url = urljoin(self.jupyter_url, "/api/kernels")
            response = await self.client.get(url, params=self._get_auth_params())
            response.raise_for_status()
            
            kernels = response.json()
            if not kernels:
                return "No active kernels found"
            
            result = "Active kernels:\n"
            for kernel in kernels:
                result += f"- ID: {kernel['id']}, Name: {kernel['name']}, State: {kernel.get('execution_state', 'unknown')}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing kernels: {e}")
            return f"Error listing kernels: {str(e)}"
    
    async def _create_kernel(self, kernel_name: str = "python3") -> str:
        """Create a new kernel"""
        try:
            url = urljoin(self.jupyter_url, "/api/kernels")
            payload = {"name": kernel_name}
            
            # Get CSRF token for POST request
            xsrf_token = await self._get_xsrf_token()
            
            # Prepare headers and data for POST
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add CSRF token to headers and payload if available
            if xsrf_token:
                headers["X-XSRFToken"] = xsrf_token
                headers["X-Requested-With"] = "XMLHttpRequest"
                # Some setups need the token in the payload too
                payload["_xsrf"] = xsrf_token
            
            # Add authentication parameters
            auth_params = self._get_auth_params()
            
            logger.info(f"Creating kernel with payload: {payload}")
            logger.info(f"Using headers: {list(headers.keys())}")
            
            response = await self.client.post(
                url, 
                json=payload, 
                params=auth_params,
                headers=headers
            )
            
            # Log response details for debugging
            logger.info(f"Kernel creation response status: {response.status_code}")
            
            response.raise_for_status()
            
            kernel_info = response.json()
            self.kernel_id = kernel_info["id"]
            
            logger.info(f"Created kernel {self.kernel_id}")
            return f"Created kernel: {kernel_info['id']} (name: {kernel_info['name']})"
            
        except Exception as e:
            logger.error(f"Error creating kernel: {e}")
            # Try to provide more detailed error information
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            return f"Error creating kernel: {str(e)}"
    
    async def _shutdown_kernel(self, kernel_id: Optional[str] = None) -> str:
        """Shutdown a kernel"""
        try:
            target_kernel = kernel_id or self.kernel_id
            if not target_kernel:
                return "No kernel specified and no active kernel"
            
            url = urljoin(self.jupyter_url, f"/api/kernels/{target_kernel}")
            response = await self.client.delete(url, params=self._get_auth_params())
            response.raise_for_status()
            
            if target_kernel == self.kernel_id:
                self.kernel_id = None
            
            logger.info(f"Shutdown kernel {target_kernel}")
            return f"Kernel {target_kernel} shutdown successfully"
            
        except Exception as e:
            logger.error(f"Error shutting down kernel: {e}")
            return f"Error shutting down kernel: {str(e)}"
    
    async def _execute_code(self, code: str, kernel_name: str = "python3", position: Optional[int] = None) -> str:
        """Execute code in Jupyter kernel"""
        try:
            # Ensure we have an active kernel
            if not self.kernel_id:
                await self._create_kernel(kernel_name)
            
            if not self.kernel_id:
                return "Failed to create or find active kernel"
            
            # Use WebSocket for real-time execution
            return await self._execute_code_websocket(code, position)
            
        except Exception as e:
            logger.error(f"Error executing code: {e}")
            return f"Error executing code: {str(e)}"
    
    async def _execute_code_websocket(self, code: str, position: Optional[int] = None) -> str:
        """Execute code using WebSocket connection"""
        try:
            # Build WebSocket URL
            ws_url = self.jupyter_url.replace("http://", "ws://").replace("https://", "wss://")
            ws_url = urljoin(ws_url, f"/api/kernels/{self.kernel_id}/channels")
            
            # Add token to WebSocket URL if needed
            if self.token:
                ws_url += f"?token={self.token}"
            
            logger.info(f"Connecting to WebSocket: {ws_url}")
            
            async with websockets.connect(ws_url) as websocket:
                # Create execution message
                msg_id = f"execute_{asyncio.get_event_loop().time()}"
                message = {
                    "header": {
                        "msg_id": msg_id,
                        "msg_type": "execute_request",
                        "session": self.session_id or "default_session",
                        "username": "mcp",
                        "version": "5.3"
                    },
                    "metadata": {},
                    "content": {
                        "code": code,
                        "silent": False,
                        "store_history": True,
                        "user_expressions": {},
                        "allow_stdin": False,
                        "stop_on_error": True
                    },
                    "parent_header": {},
                    "channel": "shell"
                }
                
                # Send execution request
                await websocket.send(json.dumps(message))
                logger.info("Sent execution request")
                
                # Collect response
                outputs = []
                execution_count = None
                cell_outputs = []  # Store all output data for notebook saving
                
                while True:
                    try:
                        # Wait for message with timeout
                        response = await asyncio.wait_for(
                            websocket.recv(), 
                            timeout=30.0
                        )
                        msg = json.loads(response)
                        
                        msg_type = msg.get("msg_type", "")
                        content = msg.get("content", {})
                        
                        logger.debug(f"Received message type: {msg_type}")
                        
                        if msg_type == "execute_reply":
                            execution_count = content.get("execution_count")
                            status = content.get("status")
                            if status == "error":
                                error_output = {
                                    "output_type": "error",
                                    "ename": content.get("ename", "Unknown error"),
                                    "evalue": content.get("evalue", ""),
                                    "traceback": content.get("traceback", [])
                                }
                                cell_outputs.append(error_output)
                                outputs.append(f"Error: {content.get('ename', 'Unknown error')}")
                                outputs.append(f"Message: {content.get('evalue', '')}")
                            break
                            
                        elif msg_type == "stream":
                            stream_content = content.get("text", "")
                            stream_output = {
                                "output_type": "stream",
                                "name": content.get("name", "stdout"),
                                "text": stream_content
                            }
                            cell_outputs.append(stream_output)
                            outputs.append(stream_content)
                            
                        elif msg_type == "execute_result":
                            execution_count = content.get("execution_count")
                            data = content.get("data", {})
                            metadata = content.get("metadata", {})
                            
                            # Create execute_result output for notebook
                            execute_result_output = {
                                "output_type": "execute_result",
                                "execution_count": execution_count,
                                "data": data,
                                "metadata": metadata
                            }
                            cell_outputs.append(execute_result_output)
                            
                            # Add text representation to display outputs
                            if "text/plain" in data:
                                outputs.append(data["text/plain"])
                            if "image/png" in data:
                                outputs.append("[Image Output (PNG)]")
                            if "image/jpeg" in data:
                                outputs.append("[Image Output (JPEG)]")
                                
                        elif msg_type == "display_data":
                            data = content.get("data", {})
                            metadata = content.get("metadata", {})
                            
                            # Create display_data output for notebook
                            display_data_output = {
                                "output_type": "display_data",
                                "data": data,
                                "metadata": metadata
                            }
                            cell_outputs.append(display_data_output)
                            
                            # Add text representation to display outputs
                            if "text/plain" in data:
                                outputs.append(data["text/plain"])
                            if "image/png" in data:
                                outputs.append("[Image Output (PNG)]")
                            if "image/jpeg" in data:
                                outputs.append("[Image Output (JPEG)]")
                                
                        elif msg_type == "error":
                            error_output = {
                                "output_type": "error",
                                "ename": content.get("ename", "Unknown error"),
                                "evalue": content.get("evalue", ""),
                                "traceback": content.get("traceback", [])
                            }
                            cell_outputs.append(error_output)
                            outputs.append(f"Error: {content.get('ename', 'Unknown error')}")
                            outputs.append(f"Message: {content.get('evalue', '')}")
                            
                    except asyncio.TimeoutError:
                        logger.warning("WebSocket response timeout")
                        break
                    except Exception as e:
                        logger.error(f"WebSocket error: {e}")
                        break
                
                # Format result
                result = ""
                if execution_count is not None:
                    result += f"In [{execution_count}]: {code}\n\n"
                
                if outputs:
                    result += "Output:\n" + "\n".join(str(output) for output in outputs)
                else:
                    result += "Code executed successfully (no output)"
                
                # Save code cell to notebook
                code_cell = new_code_cell(source=code)
                # Add execution count if available
                if execution_count is not None:
                    code_cell.execution_count = execution_count
                
                # Add all captured outputs to cell
                code_cell.outputs = cell_outputs
                
                # Add cell to notebook and save
                if position is not None and position >= 0 and position < len(self.current_notebook.cells):
                    self.current_notebook.cells.insert(position, code_cell)
                else:
                    self.current_notebook.cells.append(code_cell)
                self._save_notebook()
                
                return result
                
        except Exception as e:
            logger.error(f"WebSocket execution error: {e}")
            # Fallback to HTTP execution
            return await self._execute_code_http_fallback(code)
    
    async def _execute_code_http_fallback(self, code: str) -> str:
        """Fallback HTTP-based code execution"""
        try:
            logger.info("Using HTTP fallback for code execution")
            
            # Get kernel info first
            url = urljoin(self.jupyter_url, f"/api/kernels/{self.kernel_id}")
            response = await self.client.get(url, params=self._get_auth_params())
            response.raise_for_status()
            
            kernel_info = response.json()
            
            # Note: Direct HTTP execution is limited in Jupyter Server
            # This is a simplified approach that mainly validates the kernel is running
            result = f"Code submitted to kernel {self.kernel_id} (HTTP fallback mode)\n"
            result += f"Kernel state: {kernel_info.get('execution_state', 'unknown')}\n"
            result += f"Code:\n{code}\n\n"
            result += "Note: Use WebSocket connection for full execution results"
            
            return result
            
        except Exception as e:
            logger.error(f"HTTP fallback error: {e}")
            return f"Execution failed: {str(e)}"
    
    async def _add_markdown_cell(self, content: str, position: Optional[int] = None) -> str:
        """Add a markdown cell to the notebook and save it"""
        try:
            # Create markdown cell
            markdown_cell = new_markdown_cell(source=content)
            
            # Add to notebook
            if position is not None and position >= 0 and position < len(self.current_notebook.cells):
                self.current_notebook.cells.insert(position, markdown_cell)
            else:
                self.current_notebook.cells.append(markdown_cell)
            
            # Save notebook
            self._save_notebook()
            
            logger.info(f"Added markdown cell with content: {content[:50]}...")
            return f"Markdown cell added and saved to {self.current_notebook_path}"
            
        except Exception as e:
            logger.error(f"Error adding markdown cell: {e}")
            return f"Error adding markdown cell: {str(e)}"
    
    async def _delete_cell(self, cell_index: int) -> str:
        """Delete a specific cell from the notebook by index"""
        try:
            if cell_index < 0 or cell_index >= len(self.current_notebook.cells):
                return "Invalid cell index"
            
            # Delete the cell
            del self.current_notebook.cells[cell_index]
            
            # Save notebook
            self._save_notebook()
            
            logger.info(f"Deleted cell at index {cell_index}")
            return f"Cell at index {cell_index} deleted successfully"
            
        except Exception as e:
            logger.error(f"Error deleting cell: {e}")
            return f"Error deleting cell: {str(e)}"
    
    async def _modify_cell(self, cell_index: int, new_content: str) -> str:
        """Modify the content of an existing cell"""
        try:
            if cell_index < 0 or cell_index >= len(self.current_notebook.cells):
                return "Invalid cell index"
            
            # Modify the cell content
            self.current_notebook.cells[cell_index].source = new_content
            
            # Save notebook
            self._save_notebook()
            
            logger.info(f"Modified cell at index {cell_index}")
            return f"Cell at index {cell_index} modified successfully"
            
        except Exception as e:
            logger.error(f"Error modifying cell: {e}")
            return f"Error modifying cell: {str(e)}"
    
    async def _change_cell_type(self, cell_index: int, new_type: str) -> str:
        """Change the type of a cell (markdown/code)"""
        try:
            if cell_index < 0 or cell_index >= len(self.current_notebook.cells):
                return "Invalid cell index"
            
            # Change the cell type
            self.current_notebook.cells[cell_index].cell_type = new_type
            
            # Save notebook
            self._save_notebook()
            
            logger.info(f"Changed cell type at index {cell_index} to {new_type}")
            return f"Cell at index {cell_index} type changed to {new_type}"
            
        except Exception as e:
            logger.error(f"Error changing cell type: {e}")
            return f"Error changing cell type: {str(e)}"
    
    async def _move_cell(self, from_index: int, to_index: int) -> str:
        """Move a cell to a different position"""
        try:
            if from_index < 0 or from_index >= len(self.current_notebook.cells) or to_index < 0 or to_index >= len(self.current_notebook.cells):
                return "Invalid cell index"
            
            # Move the cell
            cell = self.current_notebook.cells.pop(from_index)
            self.current_notebook.cells.insert(to_index, cell)
            
            # Save notebook
            self._save_notebook()
            
            logger.info(f"Moved cell from index {from_index} to index {to_index}")
            return f"Cell moved from index {from_index} to index {to_index}"
            
        except Exception as e:
            logger.error(f"Error moving cell: {e}")
            return f"Error moving cell: {str(e)}"
    
    async def _clear_notebook(self, content: str, cell_type: str = "markdown") -> str:
        """Clear all cells from notebook and replace with single cell containing the content"""
        try:
            # Clear all existing cells
            self.current_notebook.cells.clear()
            
            # Add single cell with the provided content
            if cell_type == "code":
                new_cell = new_code_cell(source=content)
            else:
                new_cell = new_markdown_cell(source=content)
            
            self.current_notebook.cells.append(new_cell)
            
            # Save notebook
            self._save_notebook()
            
            logger.info(f"Cleared notebook and added single {cell_type} cell with content: {content[:50]}...")
            return f"Notebook cleared and updated with single {cell_type} cell containing: '{content}'"
            
        except Exception as e:
            logger.error(f"Error clearing notebook: {e}")
            return f"Error clearing notebook: {str(e)}"
    
    async def _get_notebook_info(self) -> str:
        """Get comprehensive information about the current notebook"""
        try:
            if not self.current_notebook:
                return "No notebook loaded"
            
            info = f"Notebook Information:\n"
            info += f"- Path: {self.current_notebook_path}\n"
            info += f"- Total cells: {len(self.current_notebook.cells)}\n"
            
            # Count cell types
            markdown_count = sum(1 for cell in self.current_notebook.cells if cell.cell_type == "markdown")
            code_count = sum(1 for cell in self.current_notebook.cells if cell.cell_type == "code")
            
            info += f"- Markdown cells: {markdown_count}\n"
            info += f"- Code cells: {code_count}\n"
            
            # Notebook metadata
            if hasattr(self.current_notebook, 'metadata'):
                info += f"- Kernel: {self.current_notebook.metadata.get('kernelspec', {}).get('name', 'unknown')}\n"
                info += f"- Language: {self.current_notebook.metadata.get('language_info', {}).get('name', 'unknown')}\n"
            
            # Active kernel info
            info += f"- Active kernel ID: {self.kernel_id or 'None'}\n"
            info += f"- Session ID: {self.session_id or 'None'}\n"
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting notebook info: {e}")
            return f"Error getting notebook info: {str(e)}"
    
    async def _list_cells(self, preview_length: int = 100) -> str:
        """List all cells in the notebook with their types and content preview"""
        try:
            if not self.current_notebook or not self.current_notebook.cells:
                return "No cells in notebook"
            
            result = f"Notebook cells ({len(self.current_notebook.cells)} total):\n\n"
            
            for i, cell in enumerate(self.current_notebook.cells):
                content_preview = cell.source[:preview_length]
                if len(cell.source) > preview_length:
                    content_preview += "..."
                
                result += f"[{i}] Type: {cell.cell_type}\n"
                result += f"    Content: {repr(content_preview)}\n"
                
                # Add execution count for code cells
                if cell.cell_type == "code" and hasattr(cell, 'execution_count') and cell.execution_count:
                    result += f"    Execution count: {cell.execution_count}\n"
                
                result += "\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing cells: {e}")
            return f"Error listing cells: {str(e)}"
    
    async def _read_cell(self, cell_index: int) -> str:
        """Read the full content of a specific cell"""
        try:
            if cell_index < 0 or cell_index >= len(self.current_notebook.cells):
                return "Invalid cell index"
            
            cell = self.current_notebook.cells[cell_index]
            return f"Type: {cell.cell_type}, Content: {cell.source}"
        except Exception as e:
            logger.error(f"Error reading cell: {e}")
            return f"Error reading cell: {str(e)}"
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.kernel_id:
                await self._shutdown_kernel(self.kernel_id)
            await self.client.aclose()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def _init_notebook(self):
        """Initialize or load the current notebook"""
        if os.path.exists(self.current_notebook_path):
            # Load existing notebook
            try:
                with open(self.current_notebook_path, 'r') as f:
                    self.current_notebook = nbformat.read(f, as_version=4)
                logger.info(f"Loaded existing notebook: {self.current_notebook_path}")
            except Exception as e:
                logger.error(f"Error loading notebook: {e}")
                self.current_notebook = new_notebook()
        else:
            # Create new notebook
            self.current_notebook = new_notebook()
            # Add initial cell
            intro_cell = new_markdown_cell(
                source="# MCP Jupyter Notebook\n\nThis notebook is being created and managed by the Jupyter MCP Server."
            )
            self.current_notebook.cells.append(intro_cell)
            self._save_notebook()
            logger.info(f"Created new notebook: {self.current_notebook_path}")
    
    def _save_notebook(self):
        """Save the current notebook to disk"""
        try:
            with open(self.current_notebook_path, 'w') as f:
                nbformat.write(self.current_notebook, f)
            logger.info(f"Saved notebook: {self.current_notebook_path}")
        except Exception as e:
            logger.error(f"Error saving notebook: {e}")

    async def _ensure_jupyter_connection(self):
        """Ensure Jupyter connection is established"""
        try:
            response = await self.client.get(
                urljoin(self.jupyter_url, "/api"), 
                params=self._get_auth_params()
            )
            response.raise_for_status()
            logger.info("Jupyter connection verified")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Jupyter: {e}")
            return False

    async def _create_notebook(self, filename: str, initial_content: str, cell_type: str = "markdown") -> str:
        """Create a new Jupyter notebook file"""
        try:
            # Ensure filename has .ipynb extension
            if not filename.endswith('.ipynb'):
                filename += '.ipynb'
            
            # Use absolute path in the base directory
            full_path = os.path.join(self.base_dir, filename)
            
            # Check if file already exists
            if os.path.exists(full_path):
                return f"Notebook already exists: {filename}"
            
            # Create new notebook
            new_notebook = nbformat.v4.new_notebook()
            
            # Add initial cell with content (or empty if not provided)
            content = initial_content or ""
            if cell_type == "code":
                new_cell = nbformat.v4.new_code_cell(source=content)
            else:
                new_cell = nbformat.v4.new_markdown_cell(source=content)
            
            new_notebook.cells.append(new_cell)
            
            # Save notebook
            with open(full_path, 'w') as f:
                nbformat.write(new_notebook, f)
            
            logger.info(f"Created new notebook: {full_path}")
            return f"Notebook created successfully: {filename}"
            
        except Exception as e:
            logger.error(f"Error creating notebook: {e}")
            return f"Error creating notebook: {str(e)}"

    async def _delete_notebook(self, filename: str) -> str:
        """Delete a notebook file from the filesystem"""
        try:
            # Ensure filename has .ipynb extension
            if not filename.endswith('.ipynb'):
                filename += '.ipynb'
            
            # Use absolute path in the base directory
            full_path = os.path.join(self.base_dir, filename)
            
            # Check if file exists
            if not os.path.exists(full_path):
                return f"Notebook not found: {filename}"
            
            # Prevent deletion of currently active notebook
            if full_path == self.current_notebook_path:
                return f"Cannot delete currently active notebook: {filename}. Switch to another notebook first."
            
            # Delete the file
            os.remove(full_path)
            logger.info(f"Deleted notebook: {full_path}")
            return f"Notebook deleted successfully: {filename}"
            
        except Exception as e:
            logger.error(f"Error deleting notebook: {e}")
            return f"Error deleting notebook: {str(e)}"

    async def _list_notebooks(self) -> str:
        """List all notebook files in the current directory"""
        try:
            notebooks = [f for f in os.listdir(self.base_dir) if f.endswith('.ipynb')]
            if not notebooks:
                return "No notebooks found in the current directory"
            
            current_notebook_name = os.path.basename(self.current_notebook_path)
            result = f"Available notebooks (current: {current_notebook_name}):\n\n"
            
            for notebook in sorted(notebooks):
                full_path = os.path.join(self.base_dir, notebook)
                stat = os.stat(full_path)
                size = stat.st_size
                modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                # Mark current notebook
                marker = " *CURRENT*" if notebook == current_notebook_name else ""
                
                result += f"- {notebook}{marker}\n"
                result += f"  Size: {size:,} bytes\n"
                result += f"  Modified: {modified}\n\n"
            
            return result
        except Exception as e:
            logger.error(f"Error listing notebooks: {e}")
            return f"Error listing notebooks: {str(e)}"

    async def _switch_notebook(self, filename: str) -> str:
        """Switch to working with a different notebook file"""
        try:
            # Ensure filename has .ipynb extension
            if not filename.endswith('.ipynb'):
                filename += '.ipynb'
            
            # Use absolute path in the base directory
            full_path = os.path.join(self.base_dir, filename)
            
            self.current_notebook_path = full_path
            self._init_notebook()
            logger.info(f"Switched to notebook: {full_path}")
            return f"Switched to notebook: {filename}"
        except Exception as e:
            logger.error(f"Error switching notebook: {e}")
            return f"Error switching notebook: {str(e)}"

    async def _get_current_notebook(self) -> str:
        """Get the name of the currently active notebook"""
        try:
            return os.path.basename(self.current_notebook_path)
        except Exception as e:
            logger.error(f"Error getting current notebook: {e}")
            return f"Error getting current notebook: {str(e)}"

    async def _get_cell_image_output(self, cell_index: int) -> str:
        """Get the image output of a specific cell"""
        try:
            if cell_index < 0 or cell_index >= len(self.current_notebook.cells):
                return "Invalid cell index"
            
            cell = self.current_notebook.cells[cell_index]
            if cell.cell_type != "code" or not hasattr(cell, 'outputs') or not cell.outputs:
                return "No outputs found for this cell"
            
            images_found = []
            for output in cell.outputs:
                if output.get("output_type") in ["execute_result", "display_data"]:
                    data = output.get("data", {})
                    # Check for PNG images
                    if "image/png" in data:
                        images_found.append({
                            "format": "PNG",
                            "data": data["image/png"]
                        })
                    # Check for JPEG images
                    if "image/jpeg" in data:
                        images_found.append({
                            "format": "JPEG", 
                            "data": data["image/jpeg"]
                        })
            
            if not images_found:
                return f"No image outputs found in cell {cell_index}"
            
            result = f"Found {len(images_found)} image(s) in cell {cell_index}:\n"
            for i, img in enumerate(images_found):
                result += f"\nImage {i+1} ({img['format']}):\n"
                # Image data is already base64 encoded in Jupyter notebooks
                result += img["data"]
                result += "\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting cell image output: {e}")
            return f"Error getting cell image output: {str(e)}"

    async def _get_cell_text_output(self, cell_index: int) -> str:
        """Get the text output of a specific cell"""
        try:
            if cell_index < 0 or cell_index >= len(self.current_notebook.cells):
                return "Invalid cell index"
            
            cell = self.current_notebook.cells[cell_index]
            if cell.cell_type != "code" or not hasattr(cell, 'outputs') or not cell.outputs:
                return "No outputs found for this cell"
            
            text_outputs = []
            for output in cell.outputs:
                output_type = output.get("output_type")
                
                if output_type == "stream":
                    text_outputs.append(output.get("text", ""))
                elif output_type in ["execute_result", "display_data"]:
                    data = output.get("data", {})
                    if "text/plain" in data:
                        text_outputs.append(data["text/plain"])
                elif output_type == "error":
                    error_msg = f"Error: {output.get('ename', 'Unknown')}\n"
                    error_msg += f"Message: {output.get('evalue', '')}\n"
                    if output.get('traceback'):
                        error_msg += "Traceback:\n" + "\n".join(output['traceback'])
                    text_outputs.append(error_msg)
            
            if not text_outputs:
                return f"No text outputs found in cell {cell_index}"
            
            result = f"Text outputs for cell {cell_index}:\n"
            for i, text in enumerate(text_outputs):
                if len(text_outputs) > 1:
                    result += f"\nOutput {i+1}:\n"
                result += str(text)
                if i < len(text_outputs) - 1:
                    result += "\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting cell text output: {e}")
            return f"Error getting cell text output: {str(e)}"


async def main():
    """Main entry point"""
    import sys
    
    # Configuration - use the correct Jupyter server settings with no authentication
    jupyter_url = "http://localhost:8888"
    token = ""  # No token needed - Jupyter is running without authentication
    
    # Parse command line arguments if provided (but don't fail if none)
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        jupyter_url = sys.argv[1]
    if len(sys.argv) > 2:
        token = sys.argv[2]
    
    logger.info(f"Starting Jupyter MCP Server")
    logger.info(f"Jupyter URL: {jupyter_url}")
    logger.info(f"Token provided: {'Yes' if token else 'No'}")
    
    # Create server instance
    jupyter_server = JupyterMCPServer(jupyter_url=jupyter_url, token=token)
    
    try:
        # Don't test connection immediately for Claude Desktop compatibility
        # Connection will be tested when first tool is called
        logger.info("MCP Server ready (connection will be tested on first use)")
        
        # Run the MCP server
        async with stdio_server() as (read_stream, write_stream):
            await jupyter_server.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="jupyter-mcp",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities(
                        prompts=PromptsCapability(listChanged=False),
                        resources=ResourcesCapability(listChanged=False, subscribe=False),
                        tools=ToolsCapability(listChanged=False),
                        experimental={}
                    ),
                ),
            )
    
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await jupyter_server.cleanup()
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    asyncio.run(main()) 