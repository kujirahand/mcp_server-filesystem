"""ファイルシステムMCPサーバー。

起動時の引数で指定したフォルダ(許可フォルダ)の中だけを読み書きできる。

使い方:
    python -m filesystem_mcp /path/to/dir1 /path/to/dir2
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

# --- 許可フォルダ ---------------------------------------------------------

# 実体パス(シンボリックリンク解決済み)の許可フォルダ一覧
ALLOWED_DIRS: list[Path] = []


def set_allowed_dirs(paths: list[str]) -> list[Path]:
    """引数のパスを検査して許可フォルダとして登録する。"""
    dirs: list[Path] = []
    for arg in paths:
        path = Path(arg).expanduser()
        if not path.is_dir():
            raise ValueError(f"フォルダではないか、開けません: {path}")
        dirs.append(path.resolve())
    ALLOWED_DIRS[:] = dirs
    return dirs


def _is_inside(parent: Path, child: Path) -> bool:
    """childがparentの中(またはparent自身)かどうか。"""
    return child == parent or parent in child.parents


def resolve_allowed_path(target: str) -> Path:
    """指定パスが許可フォルダ内かを検査して、実体の絶対パスを返す。

    シンボリックリンクや ``..`` で許可フォルダの外へ抜けるのを防ぐため、
    実体パスに変換してから比較する。まだ存在しないパス(新規作成するファイル)は
    親フォルダを基準に検査する。
    """
    path = Path(target).expanduser()
    if path.exists():
        real = path.resolve()
    else:
        parent = path.parent.expanduser()
        if not parent.is_dir():
            raise ToolError(f"親フォルダが見つかりません: {parent}")
        real = parent.resolve() / path.name
    if not any(_is_inside(allowed, real) for allowed in ALLOWED_DIRS):
        raise ToolError(f"許可されていないパスです: {path}")
    return real


# --- ツールの戻り値(構造化出力) -----------------------------------------


class AllowedDirectories(BaseModel):
    """許可フォルダの一覧。"""

    directories: list[str] = Field(description="許可フォルダの絶対パスの一覧")


class DirectoryEntry(BaseModel):
    """フォルダの中身1件分."""

    name: str = Field(description="ファイル名またはフォルダ名")
    type: Literal["file", "directory", "other"] = Field(description="種類")
    size: int | None = Field(default=None, description="ファイルのバイト数")


class DirectoryListing(BaseModel):
    """フォルダの一覧。"""

    path: str = Field(description="実際に読んだフォルダの絶対パス")
    entries: list[DirectoryEntry] = Field(description="フォルダの中身")


class FileContent(BaseModel):
    """読み込んだファイルの内容。"""

    path: str = Field(description="実際に読んだファイルの絶対パス")
    content: str = Field(description="ファイルの内容")
    size: int = Field(description="ファイルのバイト数")


class WriteResult(BaseModel):
    """書き込みの結果。"""

    path: str = Field(description="書き込んだファイルの絶対パス")
    bytes_written: int = Field(description="書き込んだバイト数")
    appended: bool = Field(description="追記した場合はTrue")


# --- MCPサーバー ----------------------------------------------------------

mcp = MCPServer(
    name="filesystem-mcp",
    title="ファイルシステム",
    version="1.0.0",
    instructions=(
        "許可されたフォルダの中だけでファイルの読み書き・一覧取得ができます。"
        "まず list_allowed_directories で操作できるフォルダを確認してください。"
    ),
)

READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False)


@mcp.tool(
    title="許可フォルダの一覧",
    description="このサーバーが読み書きを許可されているフォルダの一覧を返します。",
    annotations=READ_ONLY,
)
def list_allowed_directories() -> AllowedDirectories:
    return AllowedDirectories(directories=[str(d) for d in ALLOWED_DIRS])


@mcp.tool(
    title="フォルダのファイル一覧",
    description="許可フォルダ内にあるフォルダの、ファイル・フォルダの一覧を返します。",
    annotations=READ_ONLY,
)
def list_directory(
    path: Annotated[str, Field(description="一覧を取得するフォルダのパス")],
) -> DirectoryListing:
    target = resolve_allowed_path(path)
    if not target.is_dir():
        raise ToolError(f"フォルダではありません: {target}")
    entries: list[DirectoryEntry] = []
    for child in sorted(target.iterdir(), key=lambda p: p.name):
        if child.is_dir():
            entries.append(DirectoryEntry(name=child.name, type="directory"))
        elif child.is_file():
            try:
                size = child.stat().st_size
            except OSError:
                size = None  # 読めないファイルはサイズなしで返す
            entries.append(DirectoryEntry(name=child.name, type="file", size=size))
        else:
            entries.append(DirectoryEntry(name=child.name, type="other"))
    return DirectoryListing(path=str(target), entries=entries)


@mcp.tool(
    title="ファイルの読み込み",
    description="許可フォルダ内にあるテキストファイルの内容を読み込んで返します。",
    annotations=READ_ONLY,
)
def read_file(
    path: Annotated[str, Field(description="読み込むファイルのパス")],
    encoding: Annotated[str, Field(description="文字コード")] = "utf-8",
) -> FileContent:
    target = resolve_allowed_path(path)
    if target.is_dir():
        raise ToolError(f"フォルダは読み込めません: {target}")
    content = target.read_text(encoding=encoding)
    return FileContent(path=str(target), content=content, size=target.stat().st_size)


@mcp.tool(
    title="ファイルの書き込み",
    description=(
        "許可フォルダ内のファイルにテキストを書き込みます。"
        "既存のファイルは上書きされます(append を True にすると末尾に追記します)。"
    ),
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=False,
        open_world_hint=False,
    ),
)
def write_file(
    path: Annotated[str, Field(description="書き込むファイルのパス")],
    content: Annotated[str, Field(description="書き込む内容")],
    append: Annotated[bool, Field(description="Trueなら追記、Falseなら上書き")] = False,
    encoding: Annotated[str, Field(description="文字コード")] = "utf-8",
) -> WriteResult:
    target = resolve_allowed_path(path)
    with open(target, "a" if append else "w", encoding=encoding) as fp:
        fp.write(content)
    return WriteResult(
        path=str(target),
        bytes_written=len(content.encode(encoding)),
        appended=append,
    )


# --- 起動 -----------------------------------------------------------------


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(
            "使い方: filesystem-mcp <許可フォルダ> [<許可フォルダ> ...]",
            file=sys.stderr,
        )
        raise SystemExit(1)
    try:
        dirs = set_allowed_dirs(args)
    except ValueError as err:
        print(f"エラー: {err}", file=sys.stderr)
        raise SystemExit(1) from err
    print(
        "filesystem-mcp 起動: 許可フォルダ = "
        + ", ".join(str(d) for d in dirs),
        file=sys.stderr,
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
