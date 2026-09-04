"""実際にサーバーをstdioで起動して、クライアントから動作を確認するテスト。"""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@asynccontextmanager
async def connect(allowed: Path):
    """許可フォルダを1つ指定してサーバーを起動し、接続済みセッションを返す。"""
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "filesystem_mcp", str(allowed)],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


@pytest.fixture
def workspace(tmp_path: Path) -> tuple[Path, Path]:
    """(許可フォルダ, 許可していないフォルダ) を作る。"""
    allowed = tmp_path / "allowed"
    denied = tmp_path / "denied"
    (allowed / "sub").mkdir(parents=True)
    denied.mkdir()
    (allowed / "hello.txt").write_text("こんにちは\n", encoding="utf-8")
    (denied / "secret.txt").write_text("ひみつ\n", encoding="utf-8")
    return allowed.resolve(), denied.resolve()


async def test_list_allowed_directories(workspace):
    allowed, _ = workspace
    async with connect(allowed) as session:
        result = await session.call_tool("list_allowed_directories", {})
        assert result.structured_content["directories"] == [str(allowed)]


async def test_list_directory(workspace):
    allowed, _ = workspace
    async with connect(allowed) as session:
        result = await session.call_tool("list_directory", {"path": str(allowed)})
        entries = result.structured_content["entries"]
        assert [(e["name"], e["type"]) for e in entries] == [
            ("hello.txt", "file"),
            ("sub", "directory"),
        ]


async def test_read_file(workspace):
    allowed, _ = workspace
    async with connect(allowed) as session:
        result = await session.call_tool(
            "read_file", {"path": str(allowed / "hello.txt")}
        )
        assert result.structured_content["content"] == "こんにちは\n"


async def test_write_file_and_append(workspace):
    allowed, _ = workspace
    target = allowed / "new.txt"
    async with connect(allowed) as session:
        result = await session.call_tool(
            "write_file", {"path": str(target), "content": "あ"}
        )
        assert result.structured_content["bytes_written"] == 3  # UTF-8で3バイト
        await session.call_tool(
            "write_file", {"path": str(target), "content": "い", "append": True}
        )
    assert target.read_text(encoding="utf-8") == "あい"


async def test_denied_directory_is_not_readable(workspace):
    allowed, denied = workspace
    async with connect(allowed) as session:
        result = await session.call_tool(
            "read_file", {"path": str(denied / "secret.txt")}
        )
        assert result.is_error
        assert "Path not allowed" in result.content[0].text


async def test_parent_traversal_is_blocked(workspace):
    allowed, denied = workspace
    async with connect(allowed) as session:
        result = await session.call_tool(
            "write_file",
            {"path": str(allowed / ".." / denied.name / "x.txt"), "content": "x"},
        )
        assert result.is_error


async def test_symlink_out_of_allowed_dir_is_blocked(workspace):
    allowed, denied = workspace
    link = allowed / "link.txt"
    link.symlink_to(denied / "secret.txt")
    async with connect(allowed) as session:
        result = await session.call_tool("read_file", {"path": str(link)})
        assert result.is_error
