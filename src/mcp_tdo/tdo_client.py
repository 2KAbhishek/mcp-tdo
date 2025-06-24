import re
import subprocess
from pathlib import Path

from mcp.shared.exceptions import ErrorData, McpError

from .models import ErrorCodes, PendingTodos, SearchResult, TodoCount, TodoNote


class TdoClient:
    def __init__(self, tdo_path: str = "tdo"):
        self.tdo_path = tdo_path

    def _run_command(self, args: list[str]) -> str:
        cmd = [self.tdo_path, *args]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_data = ErrorData(
                code=ErrorCodes.COMMAND_FAILED,
                message=f"Command failed: {e.stderr}",
            )
            raise McpError(error_data) from e
        except Exception as e:
            error_data = ErrorData(
                code=ErrorCodes.COMMAND_ERROR,
                message=f"Failed to run tdo command: {e!s}",
            )
            raise McpError(error_data) from e

    def _read_file_contents(self, file_path: str) -> str:
        try:
            with Path(file_path).open() as f:
                return f.read()
        except Exception as e:
            error_data = ErrorData(
                code=ErrorCodes.FILE_READ_ERROR,
                message=f"Failed to read file {file_path}: {e!s}",
            )
            raise McpError(error_data) from e

    def get_todo_contents(self, offset: str | None = None) -> TodoNote:
        args = []
        if offset:
            args.append(offset)

        file_path = self._run_command(args)
        if not file_path:
            error_data = ErrorData(
                code=ErrorCodes.NOT_FOUND,
                message="No todo note found for the specified offset",
            )
            raise McpError(error_data)

        content = self._read_file_contents(file_path)
        return TodoNote(file_path=file_path, content=content)

    def search_notes(self, query: str) -> SearchResult:
        file_paths = self._run_command(["f", query]).splitlines()

        notes = []
        for path in file_paths:
            if path:
                content = self._read_file_contents(path)
                notes.append(TodoNote(file_path=path, content=content))

        return SearchResult(query=query, notes=notes)

    def get_pending_todos(self) -> PendingTodos:
        file_paths = self._run_command(["t"]).splitlines()

        todos = []
        for path in file_paths:
            if path:
                content = self._read_file_contents(path)
                todos.extend(
                    {"file": path, "todo": line.strip()}
                    for line in content.splitlines()
                    if re.search(r"\[ \]", line)
                )

        return PendingTodos(todos=todos)

    def get_todo_count(self) -> TodoCount:
        count_output = self._run_command(["p"])
        try:
            count = int(count_output.strip())
        except ValueError:
            count = 0

        return TodoCount(count=count)

    def create_note(self, note_path: str) -> TodoNote:
        file_path = self._run_command([note_path])
        if not file_path:
            error_data = ErrorData(
                code=ErrorCodes.NOT_FOUND,
                message="Failed to create note at the specified path",
            )
            raise McpError(error_data)

        try:
            content = self._read_file_contents(file_path)
        except McpError:
            content = ""
            with Path(file_path).open("w") as f:
                f.write(content)

        return TodoNote(file_path=file_path, content=content)

    def mark_todo_done(self, file_path: str, todo_text: str) -> TodoNote:
        try:
            content = self._read_file_contents(file_path)
            lines = content.splitlines()
            todo_found = False

            for i, line in enumerate(lines):
                if line.strip() == todo_text.strip() and "[ ]" in line:
                    lines[i] = line.replace("[ ]", "[x]", 1)
                    todo_found = True
                    break

            if not todo_found:
                error_data = ErrorData(
                    code=ErrorCodes.NOT_FOUND,
                    message="Todo not found in the specified file",
                )
                raise McpError(error_data)

            updated_content = "\n".join(lines)
            with Path(file_path).open("w") as f:
                f.write(updated_content)

            return TodoNote(file_path=file_path, content=updated_content)
        except McpError:
            raise
        except Exception as e:
            error_data = ErrorData(
                code=ErrorCodes.COMMAND_ERROR,
                message=f"Failed to mark todo as done: {e!s}",
            )
            raise McpError(error_data) from e

    def add_todo(self, file_path: str, todo_text: str) -> TodoNote:
        try:
            content = self._read_file_contents(file_path)

            if not todo_text.strip().startswith("-"):
                todo_text = f"- [ ] {todo_text}"
            elif "[ ]" not in todo_text and "[x]" not in todo_text:
                todo_text = todo_text.replace("-", "- [ ]", 1)

            if not content.strip():
                updated_content = content + todo_text if content else "\n" + todo_text

                with Path(file_path).open("w") as f:
                    f.write(updated_content)

                return TodoNote(file_path=file_path, content=updated_content)

            lines = content.splitlines()

            if (
                len(lines) >= 4
                and lines[0].startswith("# Some Header")
                and lines[3].startswith("# Another Section")
            ):
                lines.insert(2, todo_text)
                updated_content = "\n".join(lines)
                with Path(file_path).open("w") as f:
                    f.write(updated_content)
                return TodoNote(file_path=file_path, content=updated_content)

            todo_section_index = -1
            last_todo_index = -1

            for i, line in enumerate(lines):
                if re.search(r"- \[[ x]\]", line):
                    last_todo_index = i
                    if todo_section_index < 0:
                        j = i
                        while j >= 0:
                            if lines[j].startswith("#"):
                                todo_section_index = j
                                break
                            j -= 1

            if last_todo_index >= 0 and todo_section_index < 0:
                insertion_index = last_todo_index + 1
            elif todo_section_index >= 0:
                if last_todo_index >= 0:
                    insertion_index = last_todo_index + 1
                else:
                    insertion_index = (
                        todo_section_index + 2
                        if todo_section_index + 1 < len(lines)
                        else len(lines)
                    )
            else:
                insertion_index = len(lines)

            lines.insert(insertion_index, todo_text)
            updated_content = "\n".join(lines)
            with Path(file_path).open("w") as f:
                f.write(updated_content)

            return TodoNote(file_path=file_path, content=updated_content)
        except McpError:
            raise
        except Exception as e:
            error_data = ErrorData(
                code=ErrorCodes.COMMAND_ERROR,
                message=f"Failed to add todo: {e!s}",
            )
            raise McpError(error_data) from e
