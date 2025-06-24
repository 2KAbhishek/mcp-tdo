import json
from collections.abc import Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

from .models import TdoTools
from .tdo_client import TdoClient


def _handle_tool_call(
    tdo_client: TdoClient, name: str, arguments: dict
) -> object:
    """Handle individual tool calls and return results."""
    handlers = {
        TdoTools.GET_TODO_CONTENTS.value: _handle_get_todo_contents,
        TdoTools.SEARCH_NOTES.value: _handle_search_notes,
        TdoTools.GET_PENDING_TODOS.value: _handle_get_pending_todos,
        TdoTools.GET_TODO_COUNT.value: _handle_get_todo_count,
        TdoTools.CREATE_NOTE.value: _handle_create_note,
        TdoTools.MARK_TODO_DONE.value: _handle_mark_todo_done,
        TdoTools.ADD_TODO.value: _handle_add_todo,
    }

    handler = handlers.get(name)
    if handler:
        return handler(tdo_client, arguments)

    tdo_client.raise_unknown_tool_error(name)
    return None


def _handle_get_todo_contents(tdo_client: TdoClient, arguments: dict) -> object:
    offset = arguments.get("offset")
    return tdo_client.get_todo_contents(offset)


def _handle_search_notes(tdo_client: TdoClient, arguments: dict) -> object:
    query = arguments.get("query")
    if not query:
        tdo_client.raise_query_missing_error()
    return tdo_client.search_notes(query)


def _handle_get_pending_todos(
    tdo_client: TdoClient, _arguments: dict
) -> object:
    return tdo_client.get_pending_todos()


def _handle_get_todo_count(tdo_client: TdoClient, _arguments: dict) -> object:
    return tdo_client.get_todo_count()


def _handle_create_note(tdo_client: TdoClient, arguments: dict) -> object:
    note_path = arguments.get("note_path")
    if not note_path:
        tdo_client.raise_note_path_missing_error()
    return tdo_client.create_note(note_path)


def _handle_mark_todo_done(tdo_client: TdoClient, arguments: dict) -> object:
    file_path = arguments.get("file_path")
    todo_text = arguments.get("todo_text")
    return tdo_client.mark_todo_done(file_path, todo_text)


def _handle_add_todo(tdo_client: TdoClient, arguments: dict) -> object:
    file_path = arguments.get("file_path")
    todo_text = arguments.get("todo_text")
    return tdo_client.add_todo(file_path, todo_text)


def _create_tool_list() -> list[Tool]:
    return [
        Tool(
            name=TdoTools.GET_TODO_CONTENTS.value,
            description="Show contents of todo notes",
            inputSchema={
                "type": "object",
                "properties": {
                    "offset": {
                        "type": "string",
                        "description": (
                            "Optional offset like '1' for tomorrow, "
                            "'-1' for yesterday, etc."
                        ),
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
                        "description": (
                            "Path/name for the new note "
                            "(e.g., 'tech/vim' or 'ideas')"
                        ),
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
                        "description": "Path to file containing todo",
                    },
                    "todo_text": {
                        "type": "string",
                        "description": "Text of todo item to mark done",
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
                        "description": "Path to file to add todo to",
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


def _setup_server_handlers(server: Server, tdo_client: TdoClient) -> None:
    """Setup MCP server tool handlers."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return _create_tool_list()

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        try:
            result = _handle_tool_call(tdo_client, name, arguments)
            return [
                TextContent(
                    type="text", text=json.dumps(result.model_dump(), indent=2)
                )
            ]
        except Exception as e:
            msg = f"Error processing mcp-tdo query: {e!s}"
            raise ValueError(msg) from e


async def serve(tdo_path: str | None = None) -> None:
    server = Server("mcp-tdo")
    tdo_client = TdoClient(tdo_path if tdo_path else "tdo")

    _setup_server_handlers(server, tdo_client)

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)
