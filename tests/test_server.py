from unittest.mock import patch, mock_open, MagicMock
import pytest

from mcp.shared.exceptions import McpError
from mcp_tdo.server import TdoServer


@pytest.fixture
def tdo_server():
    return TdoServer(tdo_path="tdo")


class TestGetTodoContents:
    @patch("subprocess.run")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="# Todo for today\n- [ ] Task 1\n- [ ] Task 2",
    )
    def test_get_todo_contents_no_offset(self, mock_file, mock_subprocess, tdo_server):
        """Test getting todo contents for current day"""
        # Mock the subprocess run to return a file path
        process_mock = MagicMock()
        process_mock.stdout = "/path/to/note.md\n"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        # Call the function
        result = tdo_server.get_todo_contents()

        # Verify the function called the correct commands
        mock_subprocess.assert_called_once_with(
            ["tdo"], capture_output=True, text=True, check=True
        )

        # Verify the result
        assert result.file_path == "/path/to/note.md"
        assert result.content == "# Todo for today\n- [ ] Task 1\n- [ ] Task 2"

    @patch("subprocess.run")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="# Todo for tomorrow\n- [ ] Future task",
    )
    def test_get_todo_contents_with_offset(
        self, mock_file, mock_subprocess, tdo_server
    ):
        """Test getting todo contents with a date offset"""
        # Mock the subprocess run to return a file path
        process_mock = MagicMock()
        process_mock.stdout = "/path/to/tomorrow.md\n"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        # Call the function with offset
        result = tdo_server.get_todo_contents("1")

        # Verify the function called the correct commands
        mock_subprocess.assert_called_once_with(
            ["tdo", "1"], capture_output=True, text=True, check=True
        )

        # Verify the result
        assert result.file_path == "/path/to/tomorrow.md"
        assert result.content == "# Todo for tomorrow\n- [ ] Future task"

    @patch("subprocess.run")
    def test_get_todo_contents_command_error(self, mock_subprocess, tdo_server):
        """Test handling of command errors"""
        # Mock the subprocess run to raise an error
        mock_subprocess.side_effect = Exception("Command failed")

        # Verify the function raises the expected error
        with pytest.raises(McpError, match="Failed to run tdo command: Command failed"):
            tdo_server.get_todo_contents()

    @patch("subprocess.run")
    def test_get_todo_contents_empty_result(self, mock_subprocess, tdo_server):
        """Test handling of empty result from tdo command"""
        # Mock the subprocess run to return empty output
        process_mock = MagicMock()
        process_mock.stdout = ""
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        # Verify the function raises the expected error
        with pytest.raises(
            McpError, match="No todo note found for the specified offset"
        ):
            tdo_server.get_todo_contents()


class TestSearchNotes:
    @patch("subprocess.run")
    @patch("builtins.open")
    def test_search_notes_with_results(self, mock_file, mock_subprocess, tdo_server):
        """Test searching notes with results"""
        # Mock the subprocess run to return multiple file paths
        process_mock = MagicMock()
        process_mock.stdout = "/path/to/note1.md\n/path/to/note2.md\n"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        # Set up the mock file reader to return different content for different files
        def mock_file_content(filename, *args, **kwargs):
            mock = mock_open(read_data="").return_value
            if filename == "/path/to/note1.md":
                mock.read.return_value = "# Note 1\nContent with search term"
            elif filename == "/path/to/note2.md":
                mock.read.return_value = "# Note 2\nAnother file with search term"
            return mock

        mock_file.side_effect = mock_file_content

        # Call the function
        result = tdo_server.search_notes("search term")

        # Verify the function called the correct command
        mock_subprocess.assert_called_once_with(
            ["tdo", "f", "search term"], capture_output=True, text=True, check=True
        )

        # Verify the result
        assert result.query == "search term"
        assert len(result.notes) == 2
        assert result.notes[0].file_path == "/path/to/note1.md"
        assert result.notes[0].content == "# Note 1\nContent with search term"
        assert result.notes[1].file_path == "/path/to/note2.md"
        assert result.notes[1].content == "# Note 2\nAnother file with search term"

    @patch("subprocess.run")
    def test_search_notes_no_results(self, mock_subprocess, tdo_server):
        """Test searching notes with no results"""
        # Mock the subprocess run to return no results
        process_mock = MagicMock()
        process_mock.stdout = ""
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        # Call the function
        result = tdo_server.search_notes("nonexistent term")

        # Verify the function called the correct command
        mock_subprocess.assert_called_once_with(
            ["tdo", "f", "nonexistent term"], capture_output=True, text=True, check=True
        )

        # Verify the result has no notes
        assert result.query == "nonexistent term"
        assert len(result.notes) == 0

    @patch("subprocess.run")
    def test_search_notes_command_error(self, mock_subprocess, tdo_server):
        """Test handling of command errors during search"""
        # Mock the subprocess run to raise an error
        mock_subprocess.side_effect = Exception("Search failed")

        # Verify the function raises the expected error
        with pytest.raises(McpError, match="Failed to run tdo command: Search failed"):
            tdo_server.search_notes("error term")


class TestGetPendingTodos:
    @patch("subprocess.run")
    @patch("builtins.open")
    def test_get_pending_todos_with_results(
        self, mock_file, mock_subprocess, tdo_server
    ):
        """Test getting pending todos with results"""
        # Mock the subprocess run to return file paths
        process_mock = MagicMock()
        process_mock.stdout = "/path/to/todo1.md\n/path/to/todo2.md\n"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        # Set up the mock file reader to return different content for different files
        def mock_file_content(filename, *args, **kwargs):
            mock = mock_open(read_data="").return_value
            if filename == "/path/to/todo1.md":
                mock.read.return_value = (
                    "# Todo 1\n- [ ] Task 1\n- [x] Completed task\n- [ ] Task 2"
                )
            elif filename == "/path/to/todo2.md":
                mock.read.return_value = (
                    "# Todo 2\n- [ ] Another task\n- [ ] Yet another task"
                )
            return mock

        mock_file.side_effect = mock_file_content

        # Call the function
        result = tdo_server.get_pending_todos()

        # Verify the function called the correct command
        mock_subprocess.assert_called_once_with(
            ["tdo", "t"], capture_output=True, text=True, check=True
        )

        # Verify the result
        assert len(result.todos) == 4
        assert result.todos[0] == {
            "file": "/path/to/todo1.md", "todo": "- [ ] Task 1"}
        assert result.todos[1] == {
            "file": "/path/to/todo1.md", "todo": "- [ ] Task 2"}
        assert result.todos[2] == {
            "file": "/path/to/todo2.md",
            "todo": "- [ ] Another task",
        }
        assert result.todos[3] == {
            "file": "/path/to/todo2.md",
            "todo": "- [ ] Yet another task",
        }

    @patch("subprocess.run")
    def test_get_pending_todos_no_results(self, mock_subprocess, tdo_server):
        """Test getting pending todos with no results"""
        # Mock the subprocess run to return no files
        process_mock = MagicMock()
        process_mock.stdout = ""
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        # Call the function
        result = tdo_server.get_pending_todos()

        # Verify the function called the correct command
        mock_subprocess.assert_called_once_with(
            ["tdo", "t"], capture_output=True, text=True, check=True
        )

        # Verify the result has no todos
        assert len(result.todos) == 0

    @patch("subprocess.run")
    @patch(
        "builtins.open",
        mock_open(
            read_data="# Todo\n- [x] Completed task 1\n- [x] Completed task 2"),
    )
    def test_get_pending_todos_only_completed(self, mock_subprocess, tdo_server):
        """Test getting pending todos when all tasks are completed"""
        # Mock the subprocess run to return a file path
        process_mock = MagicMock()
        process_mock.stdout = "/path/to/completed.md\n"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        # Call the function
        result = tdo_server.get_pending_todos()

        # Verify the function called the correct command
        mock_subprocess.assert_called_once_with(
            ["tdo", "t"], capture_output=True, text=True, check=True
        )

        # Verify the result has no todos since all tasks are completed
        assert len(result.todos) == 0

    @patch("subprocess.run")
    def test_get_pending_todos_command_error(self, mock_subprocess, tdo_server):
        """Test handling of command errors when getting pending todos"""
        # Mock the subprocess run to raise an error
        mock_subprocess.side_effect = Exception("Command error")

        # Verify the function raises the expected error
        with pytest.raises(McpError, match="Failed to run tdo command: Command error"):
            tdo_server.get_pending_todos()


class TestMarkTodoDone:
    @patch("mcp_tdo.server.TdoServer._read_file_contents")
    @patch("builtins.open", new_callable=mock_open)
    def test_mark_todo_done_success(
        self, mock_open_file, mock_read_contents, tdo_server
    ):
        """Test marking a todo as done successfully"""
        # Set up mock for _read_file_contents to return content with todo
        file_content = "# Todo List\n- [ ] Task 1\n- [ ] Task to mark\n- [ ] Task 3"
        mock_read_contents.return_value = file_content

        # Call the function
        result = tdo_server.mark_todo_done(
            "/path/to/todo.md", "- [ ] Task to mark")

        # Check the content was read
        mock_read_contents.assert_called_with("/path/to/todo.md")

        # Check that the file was written with updated content
        expected_content = "# Todo List\n- [ ] Task 1\n- [x] Task to mark\n- [ ] Task 3"
        mock_open_file.assert_called_with("/path/to/todo.md", "w")
        mock_open_file.return_value.__enter__.return_value.write.assert_called_with(
            expected_content
        )

        # Check the result
        assert result.file_path == "/path/to/todo.md"
        assert result.content == expected_content

    @patch("builtins.open", new_callable=mock_open)
    def test_mark_todo_done_not_found(self, mock_file, tdo_server):
        """Test marking a todo as done when the todo is not found"""
        # Set up mock to return content without the specified todo
        mock_file.return_value.__enter__.return_value.read.return_value = (
            "# Todo List\n- [ ] Task 1\n- [ ] Task 3"
        )

        # Check that the right error is raised
        with pytest.raises(McpError, match="Todo not found in the specified file"):
            tdo_server.mark_todo_done(
                "/path/to/todo.md", "- [ ] Nonexistent Task")

    @patch("builtins.open")
    def test_mark_todo_done_file_error(self, mock_file, tdo_server):
        """Test handling of file errors when marking a todo as done"""
        # Set up mock to raise an error on read
        mock_file.return_value.__enter__.side_effect = Exception("File error")

        # Check that the right error is raised
        with pytest.raises(
            McpError, match="Failed to read file /path/to/todo.md: File error"
        ):
            tdo_server.mark_todo_done("/path/to/todo.md", "- [ ] Task")

    @patch("builtins.open", new_callable=mock_open)
    def test_mark_todo_done_write_error(self, mock_file, tdo_server):
        """Test handling of write errors when marking a todo as done"""
        # Set up mock to return content on read but fail on write
        mock_file.return_value.__enter__.return_value.read.return_value = (
            "# Todo List\n- [ ] Task 1\n- [ ] Task to mark\n- [ ] Task 3"
        )
        mock_file.return_value.__enter__.return_value.write.side_effect = Exception(
            "Write error"
        )

        # Check that the right error is raised
        with pytest.raises(McpError, match="Failed to mark todo as done: Write error"):
            tdo_server.mark_todo_done("/path/to/todo.md", "- [ ] Task to mark")


class TestAddTodo:
    @patch("mcp_tdo.server.TdoServer._read_file_contents")
    @patch("builtins.open", new_callable=mock_open)
    def test_add_todo_to_existing_section(
        self, mock_open_file, mock_read_contents, tdo_server
    ):
        """Test adding a todo to a file with existing todo section"""
        # Set up mock for _read_file_contents to return content with existing todos
        file_content = "# Todo List\n- [ ] Existing Task 1\n- [ ] Existing Task 2\n\n# Another Section\nSome content"
        mock_read_contents.return_value = file_content

        # Call the function with properly formatted todo
        result = tdo_server.add_todo("/path/to/todo.md", "New Task")

        # Check the content was read
        mock_read_contents.assert_called_with("/path/to/todo.md")

        # Check that the file was written with updated content - new todo should be added after existing todos
        expected_content = "# Todo List\n- [ ] Existing Task 1\n- [ ] Existing Task 2\n- [ ] New Task\n\n# Another Section\nSome content"
        mock_open_file.assert_called_with("/path/to/todo.md", "w")
        mock_open_file.return_value.__enter__.return_value.write.assert_called_with(
            expected_content
        )

        # Check the result
        assert result.file_path == "/path/to/todo.md"
        assert result.content == expected_content

    @patch("mcp_tdo.server.TdoServer._read_file_contents")
    @patch("builtins.open", new_callable=mock_open)
    def test_add_todo_to_file_without_todos(
        self, mock_open_file, mock_read_contents, tdo_server
    ):
        """Test adding a todo to a file without existing todos but with sections"""
        # Set up mock for _read_file_contents to return content without todos
        file_content = "# Some Header\nSome content\n\n# Another Section\nMore content"
        mock_read_contents.return_value = file_content

        # Call the function
        result = tdo_server.add_todo("/path/to/todo.md", "New Task")

        # Check the content was read
        mock_read_contents.assert_called_with("/path/to/todo.md")

        # Check that the file was written with updated content - new todo should be added after first section
        expected_content = "# Some Header\nSome content\n- [ ] New Task\n\n# Another Section\nMore content"
        mock_open_file.assert_called_with("/path/to/todo.md", "w")
        mock_open_file.return_value.__enter__.return_value.write.assert_called_with(
            expected_content
        )

        # Check the result
        assert result.file_path == "/path/to/todo.md"
        assert result.content == expected_content

    @patch("mcp_tdo.server.TdoServer._read_file_contents")
    @patch("builtins.open", new_callable=mock_open)
    def test_add_todo_to_empty_file(
        self, mock_open_file, mock_read_contents, tdo_server
    ):
        """Test adding a todo to an empty file"""
        # Set up mock for _read_file_contents to return empty content
        file_content = ""
        mock_read_contents.return_value = file_content

        # Call the function
        result = tdo_server.add_todo("/path/to/todo.md", "New Task")

        # Check the content was read
        mock_read_contents.assert_called_with("/path/to/todo.md")

        # Check that the file was written with updated content - new todo should be added at the end
        expected_content = "\n- [ ] New Task"
        mock_open_file.assert_called_with("/path/to/todo.md", "w")
        mock_open_file.return_value.__enter__.return_value.write.assert_called_with(
            expected_content
        )

        # Check the result
        assert result.file_path == "/path/to/todo.md"
        assert result.content == expected_content

    @patch("mcp_tdo.server.TdoServer._read_file_contents")
    @patch("builtins.open", new_callable=mock_open)
    def test_add_todo_with_formatted_text(
        self, mock_open_file, mock_read_contents, tdo_server
    ):
        """Test adding a todo that's already formatted with checkbox"""
        # Set up mock for _read_file_contents to return content
        file_content = "# Todo List\n- [ ] Existing Task"
        mock_read_contents.return_value = file_content

        # Call the function with already formatted todo
        result = tdo_server.add_todo(
            "/path/to/todo.md", "- [ ] New Formatted Task")

        # Check that the file was written with updated content - formatting should be preserved
        expected_content = "# Todo List\n- [ ] Existing Task\n- [ ] New Formatted Task"
        mock_open_file.assert_called_with("/path/to/todo.md", "w")
        mock_open_file.return_value.__enter__.return_value.write.assert_called_with(
            expected_content
        )

        # Check the result
        assert result.file_path == "/path/to/todo.md"
        assert result.content == expected_content

    @patch("builtins.open")
    def test_add_todo_file_error(self, mock_file, tdo_server):
        """Test handling of file errors when adding a todo"""
        # Set up mock to raise an error on read
        mock_file.side_effect = Exception("File error")

        # Check that the right error is raised
        with pytest.raises(
            McpError, match="Failed to read file /path/to/todo.md: File error"
        ):
            tdo_server.add_todo("/path/to/todo.md", "New Task")
