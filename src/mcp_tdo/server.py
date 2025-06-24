import json
from collections.abc import Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

from .models import TdoTools
from .tdo_client import TdoClient


async def serve(tdo_path: str | None = None) -> None:
    server = Server("mcp-tdo")
    tdo_client = TdoClient(tdo_path if tdo_path else "tdo")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
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
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name=TdoTools.GET_TODO_COUNT.value,
                description="Get count of pending todos",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name=TdoTools.CREATE_NOTE.value,
                description="Create a new todo note",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "note_path": {
                            "type": "string",
                            "description": "Path/name for the new note (e.g., 'tech/vim' or 'ideas')",
                        }
                    },
                    "required": ["note_path"],
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
                        },
                    },
                    "required": ["file_path", "todo_text"],
                },
            ),
            Tool(
                name=TdoTools.ADD_TODO.value,
                description="Add a new todo item to a file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to add the todo to",
                        },
                        "todo_text": {
                            "type": "string",
                            "description": "Text of the todo item to add",
                        },
                    },
                    "required": ["file_path", "todo_text"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        try:
            match name:
                case TdoTools.GET_TODO_CONTENTS.value:
                    offset = arguments.get("offset")
                    result = tdo_client.get_todo_contents(offset)

                case TdoTools.SEARCH_NOTES.value:
                    query = arguments.get("query")
                    if not query:
                        raise ValueError("Missing required argument: query")
                    result = tdo_client.search_notes(query)

                case TdoTools.GET_PENDING_TODOS.value:
                    result = tdo_client.get_pending_todos()

                case TdoTools.GET_TODO_COUNT.value:
                    result = tdo_client.get_todo_count()

                case TdoTools.CREATE_NOTE.value:
                    note_path = arguments.get("note_path")
                    if not note_path:
                        raise ValueError("Missing required argument: note_path")
                    result = tdo_client.create_note(note_path)

                case TdoTools.MARK_TODO_DONE.value:
                    file_path = arguments.get("file_path")
                    todo_text = arguments.get("todo_text")
                    result = tdo_client.mark_todo_done(file_path, todo_text)

                case TdoTools.ADD_TODO.value:
                    file_path = arguments.get("file_path")
                    todo_text = arguments.get("todo_text")
                    result = tdo_client.add_todo(file_path, todo_text)

                case _:
                    raise ValueError(f"Unknown tool: {name}")

            return [
                TextContent(
                    type="text", text=json.dumps(result.model_dump(), indent=2)
                )
            ]

        except Exception as e:
            raise ValueError(f"Error processing mcp-tdo query: {e!s}") from e

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)
