from unittest.mock import MagicMock, patch

import pytest
from mcp.shared.exceptions import McpError


class TestGetTodoCount:
    @patch("subprocess.run")
    def test_get_todo_count_success(self, mock_subprocess, tdo_server):
        process_mock = MagicMock()
        process_mock.stdout = "42"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        result = tdo_server.get_todo_count()

        mock_subprocess.assert_called_once_with(
            ["tdo", "p"], capture_output=True, text=True, check=True
        )
        assert result.count == 42

    @patch("subprocess.run")
    def test_get_todo_count_zero(self, mock_subprocess, tdo_server):
        process_mock = MagicMock()
        process_mock.stdout = "0"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        result = tdo_server.get_todo_count()

        assert result.count == 0

    @patch("subprocess.run")
    def test_get_todo_count_invalid_output(self, mock_subprocess, tdo_server):
        process_mock = MagicMock()
        process_mock.stdout = "invalid"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        result = tdo_server.get_todo_count()

        assert result.count == 0

    @patch("subprocess.run")
    def test_get_todo_count_command_error(self, mock_subprocess, tdo_server):
        mock_subprocess.side_effect = Exception("Command failed")

        with pytest.raises(
            McpError, match="Failed to run tdo command: Command failed"
        ):
            tdo_server.get_todo_count()
