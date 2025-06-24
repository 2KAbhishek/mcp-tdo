from unittest.mock import MagicMock, mock_open, patch

import pytest
from mcp.shared.exceptions import ErrorData, McpError

from mcp_tdo.models import ErrorCodes


class TestCreateNote:
    @patch("subprocess.run")
    @patch(
        "pathlib.Path.open",
        new_callable=mock_open,
        read_data="# New Note\nContent",
    )
    def test_create_note_success(self, mock_file, mock_subprocess, tdo_server):
        assert mock_file is not None
        process_mock = MagicMock()
        process_mock.stdout = "/path/to/new_note.md"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        result = tdo_server.create_note("tech/vim")

        mock_subprocess.assert_called_once_with(
            ["tdo", "tech/vim"], capture_output=True, text=True, check=True
        )
        assert result.file_path == "/path/to/new_note.md"
        assert result.content == "# New Note\nContent"

    @patch("subprocess.run")
    @patch("pathlib.Path.open", new_callable=mock_open)
    @patch("mcp_tdo.tdo_client.TdoClient._read_file_contents")
    def test_create_note_empty_file(
        self, mock_read_contents, mock_file, mock_subprocess, tdo_server
    ):
        process_mock = MagicMock()
        process_mock.stdout = "/path/to/empty_note.md"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        error_data = ErrorData(
            code=ErrorCodes.NOT_FOUND, message="File not found"
        )
        mock_read_contents.side_effect = McpError(error_data)

        result = tdo_server.create_note("ideas")

        assert result.file_path == "/path/to/empty_note.md"
        assert result.content == ""
        mock_file.assert_called_once()

    @patch("subprocess.run")
    def test_create_note_empty_result(self, mock_subprocess, tdo_server):
        process_mock = MagicMock()
        process_mock.stdout = ""
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        with pytest.raises(
            McpError, match="Failed to create note at the specified path"
        ):
            tdo_server.create_note("invalid/path")

    @patch("subprocess.run")
    def test_create_note_command_error(self, mock_subprocess, tdo_server):
        mock_subprocess.side_effect = Exception("Command failed")

        with pytest.raises(
            McpError, match="Failed to run tdo command: Command failed"
        ):
            tdo_server.create_note("tech/vim")
