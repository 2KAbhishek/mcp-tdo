from enum import Enum, IntEnum
import json
import subprocess
import re
from typing import Sequence, List, Dict, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.shared.exceptions import McpError, ErrorData

from pydantic import BaseModel


class TdoTools(str, Enum):
    GET_TODO_CONTENTS = "get_todo_contents"
    SEARCH_NOTES = "search_notes"
    GET_PENDING_TODOS = "get_pending_todos"
    MARK_TODO_DONE = "mark_todo_done"


class ErrorCodes(IntEnum):
    COMMAND_FAILED = 1001
    COMMAND_ERROR = 1002
    FILE_READ_ERROR = 1003
    NOT_FOUND = 1004


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
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_data = ErrorData(code=ErrorCodes.COMMAND_FAILED, message=f"Command failed: {e.stderr}")
            raise McpError(error_data)
        except Exception as e:
            error_data = ErrorData(code=ErrorCodes.COMMAND_ERROR, message=f"Failed to run tdo command: {str(e)}")
            raise McpError(error_data)

    def _read_file_contents(self, file_path: str) -> str:
        """Read the contents of a file"""
        try:
            with open(file_path, "r") as f:
                return f.read()
        except Exception as e:
            error_data = ErrorData(code=ErrorCodes.FILE_READ_ERROR, message=f"Failed to read file {file_path}: {str(e)}")
            raise McpError(error_data)

    def get_todo_contents(self, offset: Optional[str] = None) -> TodoNote:
        """Get contents of todo notes"""
        args = []
        if offset:
            args.append(offset)

        # Run tdo command in non-interactive mode to get the file path
        file_path = self._run_command(args)
        if not file_path:
            error_data = ErrorData(code=ErrorCodes.NOT_FOUND, message="No todo note found for the specified offset")
            raise McpError(error_data)

        # Read the content of the file
        content = self._read_file_contents(file_path)

        return TodoNote(
            file_path=file_path,
            content=content
        )

    def search_notes(self, query: str) -> SearchResult:
        """Search for notes matching a query"""
        # Run tdo command in non-interactive mode to get the file paths
        file_paths = self._run_command(["f", query]).splitlines()

        notes = []
        for path in file_paths:
            if path:
                content = self._read_file_contents(path)
                notes.append(TodoNote(file_path=path, content=content))

        return SearchResult(
            query=query,
            notes=notes
        )

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
                        todos.append({
                            "file": path,
                            "todo": line.strip()
                        })

        return PendingTodos(todos=todos)

    def mark_todo_done(self, file_path: str, todo_text: str) -> TodoNote:
        """Mark a todo as done by changing [ ] to [x]"""
        try:
            # Read the file content
            content = self._read_file_contents(file_path)

            # Find the exact todo line and replace [ ] with [x]
            lines = content.splitlines()
            todo_found = False

            for i, line in enumerate(lines):
                # Check if this line contains our todo (using strip to ignore whitespace differences)
                if line.strip() == todo_text.strip() and "[ ]" in line:
                    # Replace the first occurrence of [ ] with [x]
                    lines[i] = line.replace("[ ]", "[x]", 1)
                    todo_found = True
                    break

            if not todo_found:
                error_data = ErrorData(
                    code=ErrorCodes.NOT_FOUND,
                    message=f"Todo not found in the specified file"
                )
                raise McpError(error_data)

            # Write the updated content back to the file
            updated_content = "\n".join(lines)
            with open(file_path, "w") as f:
                f.write(updated_content)

            # Return the updated note
            return TodoNote(
                file_path=file_path,
                content=updated_content
            )
        except McpError:
            raise
        except Exception as e:
            error_data = ErrorData(
                code=ErrorCodes.COMMAND_ERROR,
                message=f"Failed to mark todo as done: {str(e)}"
            )
            raise McpError(error_data)


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
            Tool(
                name=TdoTools.MARK_TODO_DONE.value,
                description="Mark a todo item as done",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file containing the todo",
                        },
                        "todo_text": {
                            "type": "string",
                            "description": "Text of the todo item to mark as done",
                        }
                    },
                    "required": ["file_path", "todo_text"],
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

                case TdoTools.MARK_TODO_DONE.value:
                    file_path = arguments.get("file_path")
                    todo_text = arguments.get("todo_text")
                    result = tdo_server.mark_todo_done(file_path, todo_text)

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
