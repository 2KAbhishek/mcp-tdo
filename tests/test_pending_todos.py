from unittest.mock import MagicMock, mock_open, patch

import pytest
from mcp.shared.exceptions import McpError


class TestGetPendingTodos:
    @patch("subprocess.run")
    @patch("mcp_tdo.tdo_client.TdoClient._read_file_contents")
    def test_get_pending_todos_with_results(
        self, mock_read_contents, mock_subprocess, tdo_server
    ):
        process_mock = MagicMock()
        process_mock.stdout = "/path/to/todo1.md\n/path/to/todo2.md\n"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        def mock_file_content(file_path):
            if file_path == "/path/to/todo1.md":
                return "# Todo 1\n- [ ] Task 1\n- [x] Completed task\n- [ ] Task 2"
            elif file_path == "/path/to/todo2.md":
                return "# Todo 2\n- [ ] Another task\n- [ ] Yet another task"
            return ""

        mock_read_contents.side_effect = mock_file_content

        result = tdo_server.get_pending_todos()

        mock_subprocess.assert_called_once_with(
            ["tdo", "t"], capture_output=True, text=True, check=True
        )
        assert len(result.todos) == 4
        assert result.todos[0] == {"file": "/path/to/todo1.md", "todo": "- [ ] Task 1"}
        assert result.todos[1] == {"file": "/path/to/todo1.md", "todo": "- [ ] Task 2"}
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
        process_mock = MagicMock()
        process_mock.stdout = ""
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        result = tdo_server.get_pending_todos()

        mock_subprocess.assert_called_once_with(
            ["tdo", "t"], capture_output=True, text=True, check=True
        )
        assert len(result.todos) == 0

    @patch("subprocess.run")
    @patch(
        "pathlib.Path.open",
        mock_open(read_data="# Todo\n- [x] Completed task 1\n- [x] Completed task 2"),
    )
    def test_get_pending_todos_only_completed(self, mock_subprocess, tdo_server):
        process_mock = MagicMock()
        process_mock.stdout = "/path/to/completed.md\n"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        result = tdo_server.get_pending_todos()

        mock_subprocess.assert_called_once_with(
            ["tdo", "t"], capture_output=True, text=True, check=True
        )
        assert len(result.todos) == 0

    @patch("subprocess.run")
    def test_get_pending_todos_command_error(self, mock_subprocess, tdo_server):
        mock_subprocess.side_effect = Exception("Command error")

        with pytest.raises(McpError, match="Failed to run tdo command: Command error"):
            tdo_server.get_pending_todos()
