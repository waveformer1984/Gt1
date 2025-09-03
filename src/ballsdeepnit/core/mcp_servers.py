"""
Specialized MCP Server implementations for different agent functions.
Optimized per function type for maximum performance.
"""

import asyncio
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
import logging

try:
    import mcp
    from mcp import types
    from mcp.server import Server, stdio_server
    from mcp.server.session import ServerSession
    import httpx
    import numpy as np
    import sounddevice as sd
    import rtmidi
except ImportError as e:
    logging.warning(f"MCP server dependencies not available: {e}")

from ..utils.logging import get_logger
from .config import settings

logger = get_logger(__name__)


class AudioProcessingMCPServer:
    """MCP Server optimized for audio processing operations."""
    
    def __init__(self):
        self.server = Server("audio-processing")
        self.sample_rate = settings.AUDIO_SAMPLE_RATE
        self.buffer_size = settings.AUDIO_BUFFER_SIZE
        self.setup_tools()
    
    def setup_tools(self):
        """Setup audio processing tools."""
        
        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="record_audio",
                    description="Record audio from default input device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "duration": {"type": "number", "description": "Recording duration in seconds"},
                            "sample_rate": {"type": "integer", "default": self.sample_rate},
                            "channels": {"type": "integer", "default": 1}
                        },
                        "required": ["duration"]
                    }
                ),
                types.Tool(
                    name="play_audio",
                    description="Play audio data or file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "audio_data": {"type": "array", "description": "Audio data as array"},
                            "file_path": {"type": "string", "description": "Path to audio file"},
                            "sample_rate": {"type": "integer", "default": self.sample_rate}
                        }
                    }
                ),
                types.Tool(
                    name="analyze_audio_spectrum",
                    description="Analyze audio frequency spectrum",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "audio_data": {"type": "array", "description": "Audio data as array"},
                            "sample_rate": {"type": "integer", "default": self.sample_rate}
                        },
                        "required": ["audio_data"]
                    }
                ),
                types.Tool(
                    name="apply_audio_filter",
                    description="Apply filter to audio data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "audio_data": {"type": "array", "description": "Audio data as array"},
                            "filter_type": {"type": "string", "enum": ["lowpass", "highpass", "bandpass"]},
                            "cutoff_freq": {"type": "number", "description": "Cutoff frequency in Hz"},
                            "sample_rate": {"type": "integer", "default": self.sample_rate}
                        },
                        "required": ["audio_data", "filter_type", "cutoff_freq"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            try:
                if name == "record_audio":
                    return await self._record_audio(**arguments)
                elif name == "play_audio":
                    return await self._play_audio(**arguments)
                elif name == "analyze_audio_spectrum":
                    return await self._analyze_spectrum(**arguments)
                elif name == "apply_audio_filter":
                    return await self._apply_filter(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Audio processing tool error: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _record_audio(self, duration: float, sample_rate: int = None, channels: int = 1) -> List[types.TextContent]:
        """Record audio from input device."""
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        try:
            # Record audio
            recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels)
            sd.wait()  # Wait until recording is finished
            
            # Convert to list for JSON serialization
            audio_data = recording.flatten().tolist()
            
            result = {
                "audio_data": audio_data,
                "sample_rate": sample_rate,
                "duration": duration,
                "channels": channels,
                "samples": len(audio_data)
            }
            
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        except Exception as e:
            logger.error(f"Audio recording failed: {e}")
            raise
    
    async def _play_audio(self, audio_data: List[float] = None, file_path: str = None, sample_rate: int = None) -> List[types.TextContent]:
        """Play audio data or file."""
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        try:
            if audio_data:
                # Play audio data
                audio_array = np.array(audio_data, dtype=np.float32)
                sd.play(audio_array, samplerate=sample_rate)
                sd.wait()
                
                result = {
                    "status": "played",
                    "samples": len(audio_data),
                    "duration": len(audio_data) / sample_rate
                }
                
            elif file_path and os.path.exists(file_path):
                # Load and play audio file (simplified - would need librosa or similar)
                result = {
                    "status": "file_playback_not_implemented",
                    "message": "File playback requires additional audio libraries"
                }
            else:
                raise ValueError("Either audio_data or valid file_path must be provided")
            
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        except Exception as e:
            logger.error(f"Audio playback failed: {e}")
            raise
    
    async def _analyze_spectrum(self, audio_data: List[float], sample_rate: int = None) -> List[types.TextContent]:
        """Analyze audio frequency spectrum."""
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        try:
            # Convert to numpy array
            audio_array = np.array(audio_data, dtype=np.float32)
            
            # Perform FFT
            fft = np.fft.fft(audio_array)
            freqs = np.fft.fftfreq(len(fft), 1/sample_rate)
            
            # Get magnitude spectrum (first half, as it's symmetric)
            half_point = len(fft) // 2
            magnitudes = np.abs(fft[:half_point])
            frequencies = freqs[:half_point]
            
            # Find dominant frequencies
            peak_indices = np.argsort(magnitudes)[-10:]  # Top 10 peaks
            dominant_freqs = [
                {"frequency": float(frequencies[i]), "magnitude": float(magnitudes[i])}
                for i in peak_indices[::-1]  # Reverse to get highest first
            ]
            
            result = {
                "dominant_frequencies": dominant_freqs,
                "sample_rate": sample_rate,
                "fft_size": len(fft),
                "frequency_resolution": sample_rate / len(fft)
            }
            
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        except Exception as e:
            logger.error(f"Spectrum analysis failed: {e}")
            raise
    
    async def _apply_filter(self, audio_data: List[float], filter_type: str, cutoff_freq: float, sample_rate: int = None) -> List[types.TextContent]:
        """Apply audio filter."""
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        try:
            # Convert to numpy array
            audio_array = np.array(audio_data, dtype=np.float32)
            
            # Simple filtering using FFT (for demonstration - real implementation would use scipy.signal)
            fft = np.fft.fft(audio_array)
            freqs = np.fft.fftfreq(len(fft), 1/sample_rate)
            
            # Create filter mask
            if filter_type == "lowpass":
                mask = np.abs(freqs) <= cutoff_freq
            elif filter_type == "highpass":
                mask = np.abs(freqs) >= cutoff_freq
            elif filter_type == "bandpass":
                # Simple bandpass around cutoff (±20% bandwidth)
                bandwidth = cutoff_freq * 0.2
                mask = (np.abs(freqs) >= cutoff_freq - bandwidth) & (np.abs(freqs) <= cutoff_freq + bandwidth)
            else:
                raise ValueError(f"Unknown filter type: {filter_type}")
            
            # Apply filter
            filtered_fft = fft * mask
            filtered_audio = np.fft.ifft(filtered_fft).real
            
            result = {
                "filtered_audio": filtered_audio.tolist(),
                "filter_type": filter_type,
                "cutoff_frequency": cutoff_freq,
                "sample_rate": sample_rate,
                "original_samples": len(audio_data),
                "filtered_samples": len(filtered_audio)
            }
            
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        except Exception as e:
            logger.error(f"Audio filtering failed: {e}")
            raise


class FileOperationsMCPServer:
    """MCP Server optimized for file operations."""
    
    def __init__(self, base_path: str = "/workspace"):
        self.server = Server("file-operations")
        self.base_path = Path(base_path)
        self.setup_tools()
    
    def setup_tools(self):
        """Setup file operation tools."""
        
        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="read_file",
                    description="Read contents of a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to file"},
                            "encoding": {"type": "string", "default": "utf-8"}
                        },
                        "required": ["file_path"]
                    }
                ),
                types.Tool(
                    name="write_file",
                    description="Write content to a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to file"},
                            "content": {"type": "string", "description": "Content to write"},
                            "encoding": {"type": "string", "default": "utf-8"},
                            "append": {"type": "boolean", "default": False}
                        },
                        "required": ["file_path", "content"]
                    }
                ),
                types.Tool(
                    name="list_directory",
                    description="List contents of a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory_path": {"type": "string", "description": "Path to directory"},
                            "recursive": {"type": "boolean", "default": False},
                            "include_hidden": {"type": "boolean", "default": False}
                        },
                        "required": ["directory_path"]
                    }
                ),
                types.Tool(
                    name="create_directory",
                    description="Create a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory_path": {"type": "string", "description": "Path to directory"},
                            "parents": {"type": "boolean", "default": True}
                        },
                        "required": ["directory_path"]
                    }
                ),
                types.Tool(
                    name="delete_file",
                    description="Delete a file or directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to file or directory"},
                            "recursive": {"type": "boolean", "default": False}
                        },
                        "required": ["path"]
                    }
                ),
                types.Tool(
                    name="search_files",
                    description="Search for files by pattern",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string", "description": "Search pattern (glob)"},
                            "directory": {"type": "string", "default": "."},
                            "recursive": {"type": "boolean", "default": True}
                        },
                        "required": ["pattern"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            try:
                if name == "read_file":
                    return await self._read_file(**arguments)
                elif name == "write_file":
                    return await self._write_file(**arguments)
                elif name == "list_directory":
                    return await self._list_directory(**arguments)
                elif name == "create_directory":
                    return await self._create_directory(**arguments)
                elif name == "delete_file":
                    return await self._delete_file(**arguments)
                elif name == "search_files":
                    return await self._search_files(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"File operation tool error: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to base path for security."""
        resolved = self.base_path / path
        # Ensure path is within base directory for security
        try:
            resolved.resolve().relative_to(self.base_path.resolve())
            return resolved
        except ValueError:
            raise PermissionError(f"Access denied: {path} is outside allowed directory")
    
    async def _read_file(self, file_path: str, encoding: str = "utf-8") -> List[types.TextContent]:
        """Read file contents."""
        try:
            path = self._resolve_path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not path.is_file():
                raise ValueError(f"Path is not a file: {file_path}")
            
            content = path.read_text(encoding=encoding)
            
            result = {
                "content": content,
                "file_path": str(path),
                "size": len(content),
                "encoding": encoding
            }
            
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        except Exception as e:
            logger.error(f"File read failed: {e}")
            raise
    
    async def _write_file(self, file_path: str, content: str, encoding: str = "utf-8", append: bool = False) -> List[types.TextContent]:
        """Write content to file."""
        try:
            path = self._resolve_path(file_path)
            
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if append:
                with path.open('a', encoding=encoding) as f:
                    f.write(content)
            else:
                path.write_text(content, encoding=encoding)
            
            result = {
                "file_path": str(path),
                "bytes_written": len(content.encode(encoding)),
                "mode": "append" if append else "write",
                "encoding": encoding
            }
            
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        except Exception as e:
            logger.error(f"File write failed: {e}")
            raise
    
    async def _list_directory(self, directory_path: str, recursive: bool = False, include_hidden: bool = False) -> List[types.TextContent]:
        """List directory contents."""
        try:
            path = self._resolve_path(directory_path)
            
            if not path.exists():
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            if not path.is_dir():
                raise ValueError(f"Path is not a directory: {directory_path}")
            
            files = []
            directories = []
            
            if recursive:
                items = path.rglob("*")
            else:
                items = path.iterdir()
            
            for item in items:
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                item_info = {
                    "name": item.name,
                    "path": str(item.relative_to(self.base_path)),
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime,
                    "is_directory": item.is_dir()
                }
                
                if item.is_dir():
                    directories.append(item_info)
                else:
                    files.append(item_info)
            
            result = {
                "directory": str(path),
                "files": files,
                "directories": directories,
                "total_items": len(files) + len(directories)
            }
            
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        except Exception as e:
            logger.error(f"Directory listing failed: {e}")
            raise
    
    async def _create_directory(self, directory_path: str, parents: bool = True) -> List[types.TextContent]:
        """Create directory."""
        try:
            path = self._resolve_path(directory_path)
            path.mkdir(parents=parents, exist_ok=True)
            
            result = {
                "directory_path": str(path),
                "created": True,
                "parents": parents
            }
            
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        except Exception as e:
            logger.error(f"Directory creation failed: {e}")
            raise
    
    async def _delete_file(self, path: str, recursive: bool = False) -> List[types.TextContent]:
        """Delete file or directory."""
        try:
            target_path = self._resolve_path(path)
            
            if not target_path.exists():
                raise FileNotFoundError(f"Path not found: {path}")
            
            if target_path.is_dir():
                if recursive:
                    import shutil
                    shutil.rmtree(target_path)
                else:
                    target_path.rmdir()  # Only works if empty
            else:
                target_path.unlink()
            
            result = {
                "path": str(target_path),
                "deleted": True,
                "was_directory": target_path.is_dir(),
                "recursive": recursive
            }
            
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            raise
    
    async def _search_files(self, pattern: str, directory: str = ".", recursive: bool = True) -> List[types.TextContent]:
        """Search for files by pattern."""
        try:
            search_path = self._resolve_path(directory)
            
            if not search_path.exists():
                raise FileNotFoundError(f"Search directory not found: {directory}")
            
            if recursive:
                matches = list(search_path.rglob(pattern))
            else:
                matches = list(search_path.glob(pattern))
            
            results = []
            for match in matches:
                if match.is_file():
                    results.append({
                        "path": str(match.relative_to(self.base_path)),
                        "name": match.name,
                        "size": match.stat().st_size,
                        "modified": match.stat().st_mtime
                    })
            
            result = {
                "pattern": pattern,
                "search_directory": str(search_path),
                "matches": results,
                "total_matches": len(results)
            }
            
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        except Exception as e:
            logger.error(f"File search failed: {e}")
            raise


class DatabaseMCPServer:
    """MCP Server optimized for database operations."""
    
    def __init__(self, db_path: str = "data/app.db"):
        self.server = Server("database")
        self.db_path = db_path
        self.setup_tools()
    
    def setup_tools(self):
        """Setup database operation tools."""
        
        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            return [
                types.Tool(
                    name="execute_query",
                    description="Execute SQL query",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "SQL query to execute"},
                            "params": {"type": "array", "description": "Query parameters", "default": []}
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="create_table",
                    description="Create database table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {"type": "string", "description": "Name of table"},
                            "columns": {"type": "object", "description": "Column definitions"}
                        },
                        "required": ["table_name", "columns"]
                    }
                ),
                types.Tool(
                    name="insert_data",
                    description="Insert data into table",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {"type": "string", "description": "Name of table"},
                            "data": {"type": "object", "description": "Data to insert"}
                        },
                        "required": ["table_name", "data"]
                    }
                ),
                types.Tool(
                    name="get_table_schema",
                    description="Get table schema information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "table_name": {"type": "string", "description": "Name of table"}
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            try:
                if name == "execute_query":
                    return await self._execute_query(**arguments)
                elif name == "create_table":
                    return await self._create_table(**arguments)
                elif name == "insert_data":
                    return await self._insert_data(**arguments)
                elif name == "get_table_schema":
                    return await self._get_table_schema(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Database tool error: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _execute_query(self, query: str, params: List = None) -> List[types.TextContent]:
        """Execute SQL query."""
        if params is None:
            params = []
        
        try:
            # Ensure database directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Return rows as dictionaries
                cursor = conn.cursor()
                
                cursor.execute(query, params)
                
                if query.strip().upper().startswith(('SELECT', 'PRAGMA')):
                    # Query returns data
                    rows = cursor.fetchall()
                    results = [dict(row) for row in rows]
                    
                    result = {
                        "query": query,
                        "results": results,
                        "row_count": len(results)
                    }
                else:
                    # Query modifies data
                    conn.commit()
                    result = {
                        "query": query,
                        "rows_affected": cursor.rowcount,
                        "last_insert_id": cursor.lastrowid
                    }
            
            return [types.TextContent(type="text", text=json.dumps(result))]
            
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise
    
    async def _create_table(self, table_name: str, columns: Dict[str, str]) -> List[types.TextContent]:
        """Create database table."""
        try:
            # Build CREATE TABLE statement
            column_defs = []
            for col_name, col_type in columns.items():
                column_defs.append(f"{col_name} {col_type}")
            
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
            
            # Execute the query
            result = await self._execute_query(query)
            
            return result
            
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            raise
    
    async def _insert_data(self, table_name: str, data: Dict[str, Any]) -> List[types.TextContent]:
        """Insert data into table."""
        try:
            # Build INSERT statement
            columns = list(data.keys())
            placeholders = ['?' for _ in columns]
            values = list(data.values())
            
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            
            # Execute the query
            result = await self._execute_query(query, values)
            
            return result
            
        except Exception as e:
            logger.error(f"Data insertion failed: {e}")
            raise
    
    async def _get_table_schema(self, table_name: str = None) -> List[types.TextContent]:
        """Get table schema information."""
        try:
            if table_name:
                # Get schema for specific table
                query = f"PRAGMA table_info({table_name})"
                result = await self._execute_query(query)
            else:
                # Get list of all tables
                query = "SELECT name FROM sqlite_master WHERE type='table'"
                result = await self._execute_query(query)
            
            return result
            
        except Exception as e:
            logger.error(f"Schema query failed: {e}")
            raise


# Factory for creating MCP servers based on function type
class MCPServerFactory:
    """Factory for creating specialized MCP servers."""
    
    _servers = {
        "audio_processing": AudioProcessingMCPServer,
        "file_operations": FileOperationsMCPServer,
        "database_queries": DatabaseMCPServer,
    }
    
    @classmethod
    def create_server(cls, function_type: str, **kwargs) -> Any:
        """Create an MCP server for a specific function type."""
        if function_type not in cls._servers:
            raise ValueError(f"Unknown function type: {function_type}")
        
        server_class = cls._servers[function_type]
        return server_class(**kwargs)
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of available server types."""
        return list(cls._servers.keys())


async def start_mcp_server(function_type: str, **kwargs):
    """Start an MCP server for a specific function type."""
    server_instance = MCPServerFactory.create_server(function_type, **kwargs)
    
    # Start the server using stdio transport
    async with stdio_server() as streams:
        await server_instance.server.run(streams[0], streams[1], None)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mcp_servers.py <function_type>")
        print(f"Available types: {MCPServerFactory.get_available_types()}")
        sys.exit(1)
    
    function_type = sys.argv[1]
    asyncio.run(start_mcp_server(function_type))