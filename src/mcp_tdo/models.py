from enum import Enum, IntEnum

from pydantic import BaseModel


class TdoTools(str, Enum):
    GET_TODO_CONTENTS = "get_todo_contents"
    SEARCH_NOTES = "search_notes"
    GET_PENDING_TODOS = "get_pending_todos"
    GET_TODO_COUNT = "get_todo_count"
    CREATE_NOTE = "create_note"
    MARK_TODO_DONE = "mark_todo_done"
    ADD_TODO = "add_todo"


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
    notes: list[TodoNote]


class PendingTodos(BaseModel):
    todos: list[dict[str, str]]


class TodoCount(BaseModel):
    count: int
