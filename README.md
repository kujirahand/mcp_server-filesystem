# filesystem-mcp

An MCP server (Python) that can only read and write files inside folders you explicitly allow.

[日本語版はこちら (README-ja.md)](README-ja.md)

- Uses the Python MCP SDK (`mcp` v2), following the latest MCP specification
- Communicates over stdio
- Every tool supports `outputSchema` / `structuredContent` (structured output)

## Tools

| Tool | Description | Arguments |
| --- | --- | --- |
| `list_allowed_directories` | Returns the list of allowed directories | none |
| `list_directory` | Lists files and folders inside a directory | `path` |
| `read_file` | Reads a text file | `path`, `encoding` (default utf-8) |
| `write_file` | Writes or appends to a file | `path`, `content`, `append`, `encoding` |

## Usage

Pass one or more allowed directories as startup arguments.

```sh
uvx filesystem-mcp ~/Documents/work ~/tmp
```

To run from source, `uv sync` first, then:

```sh
uv run filesystem-mcp ~/Documents/work ~/tmp
uv run python -m filesystem_mcp ~/Documents/work
```

Any access outside the specified directories (and their subdirectories) fails with an
error. Escaping via `..` or a symlink is blocked too, since paths are checked against
their resolved (real) location.

## Registering with clients

`uvx` lets you run the server without installing it up front (it's fetched automatically
on first use).

Run it from PyPI:

```sh
uvx filesystem-mcp ~/Documents/work
```

You can also install it with `pip`:

```sh
pip install filesystem-mcp
filesystem-mcp ~/Documents/work
```

Run it from a local checkout during development:

```sh
uvx --from /path/to/mcp_server-filesystem filesystem-mcp ~/Documents/work
```

Or run it directly from GitHub:

```sh
uvx --from git+https://github.com/kujirahand/mcp_server-filesystem filesystem-mcp ~/Documents/work
```

The trailing arguments (one or more) are the allowed directories.

### Claude Code

```sh
claude mcp add filesystem -- uvx filesystem-mcp ~/Documents/work
```

Check the registration with `claude mcp list`, remove it with `claude mcp remove filesystem`.

### Codex CLI

```sh
codex mcp add filesystem -- uvx filesystem-mcp ~/Documents/work
```

Or configure it directly in `~/.codex/config.toml`:

```toml
[mcp_servers.filesystem]
command = "uvx"
args = ["filesystem-mcp", "~/Documents/work"]
```

List servers with `codex mcp list`, remove with `codex mcp remove filesystem`.

### Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "uvx",
      "args": ["filesystem-mcp", "~/Documents/work"]
    }
  }
}
```

## Testing with MCP Inspector

[MCP Inspector](https://github.com/modelcontextprotocol/inspector) lets you try out the
tools without registering the server with a client (requires Node.js).

### Using the GUI

```sh
npx -y @modelcontextprotocol/inspector uv run filesystem-mcp ~/Documents/work
```

When the browser opens, click **Connect** on the left to connect, then go to the
**Tools** tab and click `List Tools` to see the available tools. Select a tool, fill in
its arguments, and click `Run Tool` to see the result (including structured output).

To test against the published PyPI version instead, swap out the `uv run` part:

```sh
npx -y @modelcontextprotocol/inspector uvx filesystem-mcp ~/Documents/work
```

### Using the CLI

Adding `--cli` returns the result as JSON without opening a browser, which is handy for
quick checks and automation.

List tools:

```sh
npx -y @modelcontextprotocol/inspector --cli uv run filesystem-mcp ~/Documents/work \
  --method tools/list
```

Check the allowed directories:

```sh
npx -y @modelcontextprotocol/inspector --cli uv run filesystem-mcp ~/Documents/work \
  --method tools/call --tool-name list_allowed_directories
```

List a directory:

```sh
npx -y @modelcontextprotocol/inspector --cli uv run filesystem-mcp ~/Documents/work \
  --method tools/call --tool-name list_directory --tool-arg path=$HOME/Documents/work
```

Write and read a file (add one `--tool-arg` per argument):

```sh
npx -y @modelcontextprotocol/inspector --cli uv run filesystem-mcp ~/Documents/work \
  --method tools/call --tool-name write_file \
  --tool-arg path=$HOME/Documents/work/memo.txt --tool-arg content=hello

npx -y @modelcontextprotocol/inspector --cli uv run filesystem-mcp ~/Documents/work \
  --method tools/call --tool-name read_file --tool-arg path=$HOME/Documents/work/memo.txt
```

Pointing at a path outside the allowed directories returns `"isError": true` with a
message like `Path not allowed`.

## Tests

```sh
uv run pytest
```

## Publishing to PyPI

See [docs/publish-ja.md](docs/publish-ja.md) (maintainer notes, in Japanese).

## License

MIT
