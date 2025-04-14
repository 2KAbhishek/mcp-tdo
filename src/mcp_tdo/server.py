from enum import Enum
import json
import subprocess
import re
from typing import Sequence, List, Dict, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError

from pydantic import BaseModel


class TdoTools(str, Enum):
    GET_TODO_CONTENTS = "get_todo_contents"
    SEARCH_NOTES = "search_notes"
    GET_PENDING_TODOS = "get_pending_todos"


class TodoNote(BaseModel):
    file_path: str
    content: str


class SearchResult(BaseModel):
    query: str
    notes: List[TodoNote]


class PendingTodos(BaseModel):
    todos: List[Dict[str, str]]


class TdoServer:
    def __init__(self, tdo_path: str = "tdo"):
        self.tdo_path = tdo_path

    def _run_command(self, args: List[str]) -> str:
        """Run a tdo command and return its output"""
        cmd = [self.tdo_path] + args
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise McpError(f"Command failed: {e.stderr}")
        except Exception as e:
            raise McpError(f"Failed to run tdo command: {str(e)}")

    def _read_file_contents(self, file_path: str) -> str:
        """Read the contents of a file"""
        try:
            with open(file_path, "r") as f:
                return f.read()
        except Exception as e:
            raise McpError(f"Failed to read file {file_path}: {str(e)}")

    def get_todo_contents(self, offset: Optional[str] = None) -> TodoNote:
        """Get contents of todo notes"""
        args = []
        if offset:
            args.append(offset)

        # Run tdo command in non-interactive mode to get the file path
        file_path = self._run_command(args)
        if not file_path:
            raise McpError("No todo note found for the specified offset")

        # Read the content of the file
        content = self._read_file_contents(file_path)

        return TodoNote(file_path=file_path, content=content)

    def search_notes(self, query: str) -> SearchResult:
        """Search for notes matching a query"""
        # Run tdo command in non-interactive mode to get the file paths
        file_paths = self._run_command(["f", query]).splitlines()

        notes = []
        for path in file_paths:
            if path:
                content = self._read_file_contents(path)
                notes.append(TodoNote(file_path=path, content=content))

        return SearchResult(query=query, notes=notes)

    def get_pending_todos(self) -> PendingTodos:
        """Get all pending todos"""
        # Run tdo command in non-interactive mode to get the file paths with todos
        file_paths = self._run_command(["t"]).splitlines()

        todos = []
        for path in file_paths:
            if path:
                content = self._read_file_contents(path)
                # Extract lines with unchecked boxes
                for line in content.splitlines():
                    if re.search(r"\[ \]", line):
                        todos.append({"file": path, "todo": line.strip()})

        return PendingTodos(todos=todos)


async def serve(tdo_path: str | None = None) -> None:
    server = Server("mcp-tdo")
    tdo_server = TdoServer(tdo_path if tdo_path else "tdo")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tdo tools."""
        return [
            Tool(
                name=TdoTools.GET_TODO_CONTENTS.value,
                description="Show contents of todo notes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "offset": {
                            "type": "string",
                            "description": "Optional offset like '1' for tomorrow, '-1' for yesterday, etc.",
                        }
                    },
                },
            ),
            Tool(
                name=TdoTools.SEARCH_NOTES.value,
                description="Search for notes matching a query",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query term",
                        }
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name=TdoTools.GET_PENDING_TODOS.value,
                description="Get all pending todos",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Handle tool calls for tdo commands."""
        try:
            match name:
                case TdoTools.GET_TODO_CONTENTS.value:
                    offset = arguments.get("offset")
                    result = tdo_server.get_todo_contents(offset)

                case TdoTools.SEARCH_NOTES.value:
                    query = arguments.get("query")
                    if not query:
                        raise ValueError("Missing required argument: query")
                    result = tdo_server.search_notes(query)

                case TdoTools.GET_PENDING_TODOS.value:
                    result = tdo_server.get_pending_todos()

                case _:
                    raise ValueError(f"Unknown tool: {name}")

            return [
                TextContent(type="text", text=json.dumps(result.model_dump(), indent=2))
            ]

        except Exception as e:
            raise ValueError(f"Error processing mcp-tdo query: {str(e)}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)
