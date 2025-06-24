from unittest.mock import mock_open, patch

import pytest
from mcp.shared.exceptions import McpError


class TestAddTodo:
    @patch("mcp_tdo.tdo_client.TdoClient._read_file_contents")
    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_add_todo_to_existing_section(
        self, mock_open_file, mock_read_contents, tdo_server
    ):
        file_content = "# Todo List\n- [ ] Existing Task 1\n- [ ] Existing Task 2\n\n# Another Section\nSome content"
        mock_read_contents.return_value = file_content

        result = tdo_server.add_todo("/path/to/todo.md", "New Task")

        mock_read_contents.assert_called_with("/path/to/todo.md")

        expected_content = "# Todo List\n- [ ] Existing Task 1\n- [ ] Existing Task 2\n- [ ] New Task\n\n# Another Section\nSome content"
        mock_open_file.assert_called_once()
        mock_open_file.return_value.__enter__.return_value.write.assert_called_with(
            expected_content
        )
        assert result.file_path == "/path/to/todo.md"
        assert result.content == expected_content

    @patch("mcp_tdo.tdo_client.TdoClient._read_file_contents")
    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_add_todo_to_file_without_todos(
        self, mock_open_file, mock_read_contents, tdo_server
    ):
        file_content = "# Some Header\nSome content\n\n# Another Section\nMore content"
        mock_read_contents.return_value = file_content

        result = tdo_server.add_todo("/path/to/todo.md", "New Task")

        mock_read_contents.assert_called_with("/path/to/todo.md")

        expected_content = "# Some Header\nSome content\n- [ ] New Task\n\n# Another Section\nMore content"
        mock_open_file.assert_called_once()
        mock_open_file.return_value.__enter__.return_value.write.assert_called_with(
            expected_content
        )
        assert result.file_path == "/path/to/todo.md"
        assert result.content == expected_content

    @patch("mcp_tdo.tdo_client.TdoClient._read_file_contents")
    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_add_todo_to_empty_file(
        self, mock_open_file, mock_read_contents, tdo_server
    ):
        file_content = ""
        mock_read_contents.return_value = file_content

        result = tdo_server.add_todo("/path/to/todo.md", "New Task")

        mock_read_contents.assert_called_with("/path/to/todo.md")

        expected_content = "\n- [ ] New Task"
        mock_open_file.assert_called_once()
        mock_open_file.return_value.__enter__.return_value.write.assert_called_with(
            expected_content
        )
        assert result.file_path == "/path/to/todo.md"
        assert result.content == expected_content

    @patch("mcp_tdo.tdo_client.TdoClient._read_file_contents")
    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_add_todo_with_formatted_text(
        self, mock_open_file, mock_read_contents, tdo_server
    ):
        file_content = "# Todo List\n- [ ] Existing Task"
        mock_read_contents.return_value = file_content

        result = tdo_server.add_todo("/path/to/todo.md", "- [ ] New Formatted Task")

        expected_content = "# Todo List\n- [ ] Existing Task\n- [ ] New Formatted Task"
        mock_open_file.assert_called_once()
        mock_open_file.return_value.__enter__.return_value.write.assert_called_with(
            expected_content
        )
        assert result.file_path == "/path/to/todo.md"
        assert result.content == expected_content

    @patch("pathlib.Path.open")
    def test_add_todo_file_error(self, mock_file, tdo_server):
        mock_file.side_effect = Exception("File error")

        with pytest.raises(
            McpError, match="Failed to read file /path/to/todo.md: File error"
        ):
            tdo_server.add_todo("/path/to/todo.md", "New Task")
