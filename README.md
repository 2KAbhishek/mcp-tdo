<div align = "center">

<h1><a href="https://github.com/2kabhishek/mcp-tdo">mcp-tdo</a></h1>

<a href="https://github.com/2KAbhishek/mcp-tdo/blob/main/LICENSE">
<img alt="License" src="https://img.shields.io/github/license/2kabhishek/mcp-tdo?style=flat&color=eee&label="> </a>

<a href="https://github.com/2KAbhishek/mcp-tdo/graphs/contributors">
<img alt="People" src="https://img.shields.io/github/contributors/2kabhishek/mcp-tdo?style=flat&color=ffaaf2&label=People"> </a>

<a href="https://github.com/2KAbhishek/mcp-tdo/stargazers">
<img alt="Stars" src="https://img.shields.io/github/stars/2kabhishek/mcp-tdo?style=flat&color=98c379&label=Stars"></a>

<a href="https://github.com/2KAbhishek/mcp-tdo/network/members">
<img alt="Forks" src="https://img.shields.io/github/forks/2kabhishek/mcp-tdo?style=flat&color=66a8e0&label=Forks"> </a>

<a href="https://github.com/2KAbhishek/mcp-tdo/watchers">
<img alt="Watches" src="https://img.shields.io/github/watchers/2kabhishek/mcp-tdo?style=flat&color=f5d08b&label=Watches"> </a>

<a href="https://github.com/2KAbhishek/mcp-tdo/pulse">
<img alt="Last Updated" src="https://img.shields.io/github/last-commit/2kabhishek/mcp-tdo?style=flat&color=e06c75&label="> </a>

<a href="https://pypi.org/project/mcp-tdo/">
<img alt="PyPI" src="https://img.shields.io/pypi/v/mcp-tdo?style=flat&color=blue&label=PyPI"> </a>

<h3>MCP for your Tdos 🤖✅</h3>

</div>

mcp-tdo is a Model Context Protocol (MCP) server that allows AI models to access and manage your todo notes and tasks through the [tdo](https://github.com/2kabhishek/tdo) CLI tool.

## ✨ Features

- Retrieve todo note contents for today, tomorrow, or any date offset
- Search across all notes for specific content
- List all pending todos across all your notes
- Get count of pending todos across all your notes
- Create new todo notes
- Mark specific todos as complete
- Add new todo items to existing note files
- Fully compatible with the MCP specification

## ⚡ Setup

### ⚙️ Requirements

- Python 3.10+
- tdo CLI tool installed and accessible in your PATH
- uv for local development

### 💻 Installation

#### From PyPI (Recommended)

Install mcp-tdo from PyPI using pip or uv:

```bash
# Using pip
pip install mcp-tdo

# Using uv (recommended)
uv add mcp-tdo

# Using pipx (for CLI tools)
pipx install mcp-tdo
```

#### From Source

For development or to get the latest changes:

```bash
git clone https://github.com/2kabhishek/mcp-tdo
cd mcp-tdo
uv sync --dev
```

## 🚀 Usage

### Running the Server

If installed from PyPI:

```bash
mcp-tdo
```

Or specify a custom path to the tdo executable:

```bash
mcp-tdo --tdo-path /path/to/tdo.sh
```

If running from source:

```bash
uv run mcp-tdo
```

### MCP Server Configuration

To use this MCP server, add it to your MCP client configuration:

**Option 1: Using direct command (PyPI install)**

```json
{
  "mcpServers": {
    "mcp-tdo": {
      "command": "mcp-tdo"
    }
  }
}
```

If your tdo executable is not in PATH:

```json
{
  "mcpServers": {
    "mcp-tdo": {
      "command": "mcp-tdo",
      "args": ["--tdo-path", "/path/to/your/tdo"]
    }
  }
}
```

**Option 2: Using uv for development**

```json
{
  "mcpServers": {
    "mcp-tdo": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-tdo", "mcp-tdo"]
    }
  }
}
```

**Option 3: Using python directly**

```json
{
  "mcpServers": {
    "mcp-tdo": {
      "command": "python",
      "args": ["-m", "mcp_tdo"]
    }
  }
}
```

## 🧩 Available Tools

### get_todo_contents

Shows contents of todo notes for today or a specific date offset.

Parameters:

- `offset`: (optional) Offset like "1" for tomorrow, "-1" for yesterday, etc.

### search_notes

Searches for notes matching a query term.

Parameters:

- `query`: Search query term

### get_pending_todos

Shows all pending todos (unchecked checkboxes) from all your notes.

No parameters required.

### get_todo_count

Shows the count of pending todos across all your notes.

No parameters required.

### create_note

Creates a new todo note at the specified path.

Parameters:

- `note_path`: Path/name for the new note (e.g., 'tech/vim' or 'ideas')

### mark_todo_done

Marks a specific todo item as done.

Parameters:

- `file_path`: Path to the file containing the todo
- `todo_text`: Text of the todo item to mark as done

### add_todo

Adds a new todo item to a specified file.

Parameters:

- `file_path`: Path to the file to add the todo to
- `todo_text`: Text of the todo item to add

## 🔧 Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

### Setup

```bash
# Clone the repository
git clone https://github.com/2kabhishek/mcp-tdo
cd mcp-tdo

# Install dependencies (including dev dependencies)
uv sync --dev
```

### Common Development Commands

```bash
# Run tests
uv run pytest tests/ -v

# Run linter
uv run ruff check src/ tests/

# Format code
uv run ruff format src/ tests/

# Fix linting issues automatically
uv run ruff check --fix src/ tests/

# Run the MCP server locally
uv run mcp-tdo

# Install the package in development mode
uv sync
```

### Project Structure

```
├── src/mcp_tdo/          # Main package
│   ├── models.py         # Data models
│   ├── tdo_client.py     # TDO CLI integration
│   └── server.py         # MCP server implementation
├── tests/                # Test suite
├── pyproject.toml        # Project configuration
└── uv.lock              # Dependency lockfile
```

## 🏗️ What's Next

### ✅ To-Do

You tell me!

## 🧑‍💻 Behind The Code

### 🌈 Inspiration

mcp-tdo was inspired by the need to give AI assistants access to personal task management tools, allowing for more productive interactions with AI models.

### 💡 Challenges/Learnings

- Implementing proper error handling and command execution
- Working with the MCP protocol specification
- Managing file path and content operations safely

### 🧰 Tooling

- [dots2k](https://github.com/2kabhishek/dots2k) — Dev Environment
- [nvim2k](https://github.com/2kabhishek/nvim2k) — Personalized Editor
- [sway2k](https://github.com/2kabhishek/sway2k) — Desktop Environment
- [qute2k](https://github.com/2kabhishek/qute2k) — Personalized Browser

### 🔍 More Info

- [shelly](https://github.com/2kabhishek/shelly) — Command line template
- [tiny-web](https://github.com/2kabhishek/tiny-web) — Web app template

<hr>

<div align="center">

<strong>⭐ hit the star button if you found this useful ⭐</strong><br>

<a href="https://github.com/2KAbhishek/mcp-tdo">Source</a>
| <a href="https://2kabhishek.github.io/blog" target="_blank">Blog </a>
| <a href="https://twitter.com/2kabhishek" target="_blank">Twitter </a>
| <a href="https://linkedin.com/in/2kabhishek" target="_blank">LinkedIn </a>
| <a href="https://2kabhishek.github.io/links" target="_blank">More Links </a>
| <a href="https://2kabhishek.github.io/projects" target="_blank">Other Projects </a>

</div>
