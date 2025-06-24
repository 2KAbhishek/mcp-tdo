from unittest.mock import mock_open, patch

import pytest
from mcp.shared.exceptions import McpError


class TestMarkTodoDone:
    @patch("mcp_tdo.tdo_client.TdoClient._read_file_contents")
    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_mark_todo_done_success(
        self, mock_open_file, mock_read_contents, tdo_server
    ):
        file_content = (
            "# Todo List\n- [ ] Task 1\n- [ ] Task to mark\n- [ ] Task 3"
        )
        mock_read_contents.return_value = file_content

        result = tdo_server.mark_todo_done(
            "/path/to/todo.md", "- [ ] Task to mark"
        )

        mock_read_contents.assert_called_with("/path/to/todo.md")

        expected_content = (
            "# Todo List\n- [ ] Task 1\n- [x] Task to mark\n- [ ] Task 3"
        )
        mock_open_file.assert_called_once()
        mock_open_file.return_value.__enter__.return_value.write.assert_called_with(
            expected_content
        )
        assert result.file_path == "/path/to/todo.md"
        assert result.content == expected_content

    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_mark_todo_done_not_found(self, mock_file, tdo_server):
        mock_file.return_value.__enter__.return_value.read.return_value = (
            "# Todo List\n- [ ] Task 1\n- [ ] Task 3"
        )

        with pytest.raises(
            McpError, match="Todo not found in the specified file"
        ):
            tdo_server.mark_todo_done(
                "/path/to/todo.md", "- [ ] Nonexistent Task"
            )

    @patch("pathlib.Path.open")
    def test_mark_todo_done_file_error(self, mock_file, tdo_server):
        mock_file.return_value.__enter__.side_effect = Exception("File error")

        with pytest.raises(
            McpError, match="Failed to read file /path/to/todo.md: File error"
        ):
            tdo_server.mark_todo_done("/path/to/todo.md", "- [ ] Task")

    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_mark_todo_done_write_error(self, mock_file, tdo_server):
        mock_file.return_value.__enter__.return_value.read.return_value = (
            "# Todo List\n- [ ] Task 1\n- [ ] Task to mark\n- [ ] Task 3"
        )
        mock_file.return_value.__enter__.return_value.write.side_effect = (
            Exception("Write error")
        )

        with pytest.raises(
            McpError, match="Failed to mark todo as done: Write error"
        ):
            tdo_server.mark_todo_done("/path/to/todo.md", "- [ ] Task to mark")
