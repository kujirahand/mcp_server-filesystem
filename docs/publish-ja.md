# PyPIへの公開(メンテナ向け)

1. `pyproject.toml` の `version` を上げる
2. ビルドして中身を確認する

   ```sh
   rm -rf dist
   uv build
   uv run --with twine twine check dist/*
   ```

3. TestPyPIで動作を確かめる(任意)

   ```sh
   uv publish --publish-url https://test.pypi.org/legacy/ --token <TestPyPIのトークン>
   uvx --index-url https://test.pypi.org/simple/ --index-strategy unsafe-best-match \
     filesystem-mcp ~/Documents/work
   ```

4. PyPIへ公開する

   ```sh
   uv publish --token <PyPIのトークン>
   ```

   トークンは https://pypi.org/manage/account/token/ で発行します
   (環境変数 `UV_PUBLISH_TOKEN` でも渡せます)。

5. 公開後の確認

   ```sh
   uvx filesystem-mcp ~/Documents/work
   ```

