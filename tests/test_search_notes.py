from unittest.mock import MagicMock, patch

import pytest
from mcp.shared.exceptions import McpError


class TestSearchNotes:
    @patch("subprocess.run")
    @patch("mcp_tdo.tdo_client.TdoClient._read_file_contents")
    def test_search_notes_with_results(self, mock_read_contents, mock_subprocess, tdo_server):
        process_mock = MagicMock()
        process_mock.stdout = "/path/to/note1.md\n/path/to/note2.md\n"
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        def mock_file_content(file_path):
            if file_path == "/path/to/note1.md":
                return "# Note 1\nContent with search term"
            elif file_path == "/path/to/note2.md":
                return "# Note 2\nAnother file with search term"
            return ""

        mock_read_contents.side_effect = mock_file_content

        result = tdo_server.search_notes("search term")

        mock_subprocess.assert_called_once_with(
            ["tdo", "f", "search term"], capture_output=True, text=True, check=True
        )
        assert result.query == "search term"
        assert len(result.notes) == 2
        assert result.notes[0].file_path == "/path/to/note1.md"
        assert result.notes[0].content == "# Note 1\nContent with search term"
        assert result.notes[1].file_path == "/path/to/note2.md"
        assert result.notes[1].content == "# Note 2\nAnother file with search term"

    @patch("subprocess.run")
    def test_search_notes_no_results(self, mock_subprocess, tdo_server):
        process_mock = MagicMock()
        process_mock.stdout = ""
        process_mock.returncode = 0
        mock_subprocess.return_value = process_mock

        result = tdo_server.search_notes("nonexistent term")

        mock_subprocess.assert_called_once_with(
            ["tdo", "f", "nonexistent term"], capture_output=True, text=True, check=True
        )
        assert result.query == "nonexistent term"
        assert len(result.notes) == 0

    @patch("subprocess.run")
    def test_search_notes_command_error(self, mock_subprocess, tdo_server):
        mock_subprocess.side_effect = Exception("Search failed")

        with pytest.raises(McpError, match="Failed to run tdo command: Search failed"):
            tdo_server.search_notes("error term")
