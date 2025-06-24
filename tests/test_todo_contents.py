from unittest.mock import MagicMock, mock_open, patch

import pytest
from mcp.shared.exceptions import McpError


class TestGetTodoContents:
    @patch("subprocess.run")
    @patch("pathlib.Path.open", new_callable=mock_open, read_data="# Todo for today\n- [ ] Task 1\n- [ ] Task 2")
    def test_get_todo_contents_no_offset(self, _mock_file, mock_subprocess, tdo_server):
        process_mock = MagicMock()
        process_mock.stdout = "/path/to/note.md\n"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        result = tdo_server.get_todo_contents()

        mock_subprocess.assert_called_once_with(
            ["tdo"], capture_output=True, text=True, check=True
        )
        assert result.file_path == "/path/to/note.md"
        assert result.content == "# Todo for today\n- [ ] Task 1\n- [ ] Task 2"

    @patch("subprocess.run")
    @patch("pathlib.Path.open", new_callable=mock_open, read_data="# Todo for tomorrow\n- [ ] Future task")
    def test_get_todo_contents_with_offset(
        self, _mock_file, mock_subprocess, tdo_server
    ):
        process_mock = MagicMock()
        process_mock.stdout = "/path/to/tomorrow.md\n"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        result = tdo_server.get_todo_contents("1")

        mock_subprocess.assert_called_once_with(
            ["tdo", "1"], capture_output=True, text=True, check=True
        )
        assert result.file_path == "/path/to/tomorrow.md"
        assert result.content == "# Todo for tomorrow\n- [ ] Future task"

    @patch("subprocess.run")
    def test_get_todo_contents_command_error(self, mock_subprocess, tdo_server):
        mock_subprocess.side_effect = Exception("Command failed")

        with pytest.raises(McpError, match="Failed to run tdo command: Command failed"):
            tdo_server.get_todo_contents()

    @patch("subprocess.run")
    def test_get_todo_contents_empty_result(self, mock_subprocess, tdo_server):
        process_mock = MagicMock()
        process_mock.stdout = ""
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        with pytest.raises(
            McpError, match="No todo note found for the specified offset"
        ):
            tdo_server.get_todo_contents()
