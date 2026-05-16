"""
MCP Client for DevRamp AI Agents

Provides a client interface for communicating with MCP (Model Context Protocol) servers
via subprocess and JSON-RPC.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import subprocess
import sys


logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for communicating with MCP servers.
    
    Manages subprocess connections to MCP servers and handles JSON-RPC
    communication for tool calls.
    """
    
    def __init__(self, server_name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        """
        Initialize MCP client.
        
        Args:
            server_name: Name of the MCP server
            command: Command to start the server (e.g., 'node')
            args: Arguments for the command (e.g., ['path/to/server.js'])
            env: Optional environment variables for the server
        """
        self.server_name = server_name
        self.command = command
        self.args = args
        self.env = env or {}
        self.process: Optional[asyncio.subprocess.Process] = None
        self.request_id = 0
        self.logger = logging.getLogger(f"mcp.{server_name}")
        
    async def connect(self):
        """
        Start the MCP server subprocess and establish connection.
        
        Raises:
            Exception: If server fails to start
        """
        try:
            self.logger.info(f"Starting MCP server: {self.command} {' '.join(self.args)}")
            
            # Prepare environment
            import os
            env = os.environ.copy()
            env.update(self.env)
            
            # Start subprocess
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            self.logger.info(f"MCP server {self.server_name} started (PID: {self.process.pid})")
            
            # Wait a bit for server to initialize
            await asyncio.sleep(0.5)
            
            # Check if process is still running
            if self.process.returncode is not None:
                stderr = await self.process.stderr.read()
                raise Exception(f"Server failed to start: {stderr.decode()}")
                
        except Exception as e:
            self.logger.error(f"Failed to start MCP server: {e}")
            raise
    
    async def disconnect(self):
        """
        Disconnect from the MCP server and terminate subprocess.
        """
        if self.process:
            try:
                self.logger.info(f"Stopping MCP server {self.server_name}")
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.logger.warning(f"Server did not terminate gracefully, killing")
                self.process.kill()
                await self.process.wait()
            except Exception as e:
                self.logger.error(f"Error stopping server: {e}")
            finally:
                self.process = None
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a JSON-RPC request to the MCP server.
        
        Args:
            method: JSON-RPC method name
            params: Method parameters
            
        Returns:
            dict: Response from server
            
        Raises:
            Exception: If request fails or server is not connected
        """
        if not self.process or not self.process.stdin:
            raise Exception("Not connected to MCP server")
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        
        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            self.logger.debug(f"Sending request: {request_json.strip()}")
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()
            
            # Read response
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=30.0
            )
            
            if not response_line:
                raise Exception("Server closed connection")
            
            response = json.loads(response_line.decode())
            self.logger.debug(f"Received response: {json.dumps(response)[:200]}")
            
            # Check for errors
            if "error" in response:
                error = response["error"]
                raise Exception(f"Server error: {error.get('message', error)}")
            
            return response.get("result", {})
            
        except asyncio.TimeoutError:
            raise Exception("Request timed out")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}")
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            raise
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the MCP server.
        
        Returns:
            list: List of tool definitions
        """
        try:
            result = await self._send_request("tools/list", {})
            return result.get("tools", [])
        except Exception as e:
            self.logger.error(f"Failed to list tools: {e}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Optional arguments for the tool
            
        Returns:
            Tool execution result (parsed from JSON if possible)
            
        Raises:
            Exception: If tool call fails
        """
        try:
            params = {
                "name": tool_name,
                "arguments": arguments or {}
            }
            
            self.logger.info(f"Calling tool: {tool_name}")
            result = await self._send_request("tools/call", params)
            
            # Extract content from response
            content = result.get("content", [])
            if not content:
                return None
            
            # Get text from first content item
            text = content[0].get("text", "")
            
            # Try to parse as JSON
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
                
        except Exception as e:
            self.logger.error(f"Tool call failed: {e}")
            raise
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class MCPClientManager:
    """
    Manager for multiple MCP clients.
    
    Handles lifecycle of multiple MCP server connections.
    """
    
    def __init__(self):
        """Initialize the manager."""
        self.clients: Dict[str, MCPClient] = {}
        self.logger = logging.getLogger("mcp.manager")
    
    def add_client(
        self,
        name: str,
        command: str,
        args: List[str],
        env: Optional[Dict[str, str]] = None
    ) -> MCPClient:
        """
        Add a new MCP client.
        
        Args:
            name: Client name
            command: Command to start server
            args: Command arguments
            env: Optional environment variables
            
        Returns:
            MCPClient: The created client
        """
        client = MCPClient(name, command, args, env)
        self.clients[name] = client
        return client
    
    async def connect_all(self):
        """Connect to all registered MCP servers."""
        self.logger.info(f"Connecting to {len(self.clients)} MCP servers")
        
        tasks = [client.connect() for client in self.clients.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for failures
        for name, result in zip(self.clients.keys(), results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to connect to {name}: {result}")
                raise result
        
        self.logger.info("All MCP servers connected")
    
    async def disconnect_all(self):
        """Disconnect from all MCP servers."""
        self.logger.info("Disconnecting from all MCP servers")
        
        tasks = [client.disconnect() for client in self.clients.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info("All MCP servers disconnected")
    
    def get_client(self, name: str) -> MCPClient:
        """
        Get a client by name.
        
        Args:
            name: Client name
            
        Returns:
            MCPClient: The requested client
            
        Raises:
            KeyError: If client not found
        """
        if name not in self.clients:
            raise KeyError(f"MCP client '{name}' not found")
        return self.clients[name]
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect_all()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect_all()

# Made with Bob
