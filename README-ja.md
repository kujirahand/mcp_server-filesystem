# filesystem-mcp

許可したフォルダの中だけを読み書きできる、Python製のMCPサーバーです。

- Python MCP SDK (`mcp` v2) を使用し、最新のMCP仕様に対応
- 通信方式は stdio
- 各ツールは `outputSchema` / `structuredContent`(構造化出力)に対応

## ツール

| ツール | 説明 | 引数 |
| --- | --- | --- |
| `list_allowed_directories` | 許可フォルダの一覧を返す | なし |
| `list_directory` | フォルダ内のファイル・フォルダ一覧を返す | `path` |
| `read_file` | テキストファイルを読む | `path`, `encoding`(既定 utf-8) |
| `write_file` | ファイルに書き込む/追記する | `path`, `content`, `append`, `encoding` |

## 使い方

起動時の引数に、許可するフォルダを1つ以上指定します。

```sh
uvx filesystem-mcp ~/Documents/work ~/tmp
```

ソースから動かす場合は `uv sync` してから次のようにします。

```sh
uv run filesystem-mcp ~/Documents/work ~/tmp
uv run python -m filesystem_mcp ~/Documents/work
```

引数に指定したフォルダ(とその中のフォルダ)以外へのアクセスはエラーになります。
`..` やシンボリックリンクで外へ抜けようとした場合も、実体パスで判定してブロックします。

## クライアントへの登録

`uvx` を使うと、事前のインストールなしで実行できます(初回に自動で取得されます)。

PyPIから実行する場合:

```sh
uvx filesystem-mcp ~/Documents/work
```

`pip` でインストールすることもできます。

```sh
pip install filesystem-mcp
filesystem-mcp ~/Documents/work
```

開発中のローカルのフォルダから実行する場合:

```sh
uvx --from /path/to/mcp_server-filesystem filesystem-mcp ~/Documents/work
```

GitHubから直接実行する場合:

```sh
uvx --from git+https://github.com/kujirahand/mcp_server-filesystem filesystem-mcp ~/Documents/work
```

最後の引数(1つ以上)が許可フォルダです。

### Claude Code

```sh
claude mcp add filesystem -- uvx filesystem-mcp ~/Documents/work
```

登録を確認するには `claude mcp list`、外すには `claude mcp remove filesystem` です。

### Codex CLI

```sh
codex mcp add filesystem -- uvx filesystem-mcp ~/Documents/work
```

`~/.codex/config.toml` に直接書く場合は次のようになります。

```toml
[mcp_servers.filesystem]
command = "uvx"
args = ["filesystem-mcp", "~/Documents/work"]
```

一覧は `codex mcp list`、削除は `codex mcp remove filesystem` です。

### Claude Desktop

設定ファイル `claude_desktop_config.json` に次のように書きます。

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

## MCP Inspector で動作確認する

[MCP Inspector](https://github.com/modelcontextprotocol/inspector) を使うと、
クライアントに登録しなくてもツールを手軽に試せます(Node.js が必要です)。

### GUIで確認する

```sh
npx -y @modelcontextprotocol/inspector uv run filesystem-mcp ~/Documents/work
```

ブラウザが開いたら、左側の **Connect** を押して接続し、**Tools** タブで
`List Tools` を押すとツール一覧が出ます。ツールを選んで引数を入れ、
`Run Tool` を押すと結果(構造化出力を含む)を確認できます。

PyPIの公開版で確認したいときは、`uv run` の部分を置き換えます。

```sh
npx -y @modelcontextprotocol/inspector uvx filesystem-mcp ~/Documents/work
```

### コマンドラインで確認する

`--cli` を付けるとブラウザを開かずに結果がJSONで返るので、動作確認や自動化に便利です。

ツールの一覧:

```sh
npx -y @modelcontextprotocol/inspector --cli uv run filesystem-mcp ~/Documents/work \
  --method tools/list
```

許可フォルダの確認:

```sh
npx -y @modelcontextprotocol/inspector --cli uv run filesystem-mcp ~/Documents/work \
  --method tools/call --tool-name list_allowed_directories
```

フォルダの一覧:

```sh
npx -y @modelcontextprotocol/inspector --cli uv run filesystem-mcp ~/Documents/work \
  --method tools/call --tool-name list_directory --tool-arg path=$HOME/Documents/work
```

ファイルの書き込みと読み込み(`--tool-arg` は引数の数だけ並べます):

```sh
npx -y @modelcontextprotocol/inspector --cli uv run filesystem-mcp ~/Documents/work \
  --method tools/call --tool-name write_file \
  --tool-arg path=$HOME/Documents/work/memo.txt --tool-arg content=こんにちは

npx -y @modelcontextprotocol/inspector --cli uv run filesystem-mcp ~/Documents/work \
  --method tools/call --tool-name read_file --tool-arg path=$HOME/Documents/work/memo.txt
```

許可フォルダの外を指定すると `"isError": true` と
`許可されていないパスです` というメッセージが返ります。

## テスト

```sh
uv run pytest
```

## ライセンス

MIT
