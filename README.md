# getmycar

[![CI](https://github.com/drumsuko1113/GetMyCarforCLI/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/drumsuko1113/GetMyCarforCLI/actions/workflows/ci.yml)
[![Security](https://github.com/drumsuko1113/GetMyCarforCLI/actions/workflows/security.yml/badge.svg?branch=develop)](https://github.com/drumsuko1113/GetMyCarforCLI/actions/workflows/security.yml)

カーセンサー (https://www.carsensor.net) をスクレイピングし、Windows PowerShell ターミナル上で動作する中古車検索 CLI。

## 必要環境

- Python 3.10+
- Windows 10/11 (PowerShell 5.1+ / Windows Terminal 推奨)
- ※ Linux/macOS でも動作

## インストール

```powershell
git clone https://github.com/drumsuko1113/GetMyCarforCLI.git
cd GetMyCarforCLI
pip install -e .
```

開発時:

```powershell
pip install -e ".[dev]"
```

### PowerShell 文字化け対策

日本語表示で文字化けする場合は事前に UTF-8 を指定してください。

```powershell
$env:PYTHONIOENCODING = "utf-8"
chcp 65001
```

## 基本コマンド

```powershell
# 検索
getmycar search プリウス --price-max 200 --year-min 2018 --sort price_asc

# お気に入り (ID は直前の search 結果から参照される)
getmycar favorites add V001
getmycar favorites list
getmycar favorites compare V001 V002
getmycar favorites remove V001

# 検索条件のプリセット
getmycar preset save cheap-prius プリウス --price-max 200
getmycar preset list
getmycar preset load cheap-prius     # URL を表示

# キャッシュをクリア
getmycar cache clear
```

`-v` / `-vv` で INFO / DEBUG ログを有効にできます。

## 設定ファイル

任意で `config.toml` を以下に置くと既定値を上書きできます。

| OS | パス |
|----|------|
| Windows | `%APPDATA%\getmycar\config.toml` |
| Linux/macOS | `~/.config/getmycar/config.toml` |

```toml
[cache]
ttl_seconds = 1800

[scraper]
request_interval_seconds = 1.0
max_retries = 3
user_agent = "getmycar/0.0.1"

[search]
default_per_page = 20

[data]
dir = "./data"
```

## 倫理ガイド

- カーセンサーの `robots.txt` を遵守します（自動的に検査されます）。
- 個人利用かつ低頻度のアクセスを前提としています。連続実行や並列化は行わないでください。
- 取得したデータの再配布や商用利用はしないでください。

## 開発

- アーキテクチャは MVC、設計は SOLID と DRY を遵守しています。
- 開発フローは TDD (Red → Green → Refactor)。
- 各 Issue は `feature/issue-N-...` ブランチで作業し、PR で `develop` にマージ。CI 全 green が必須です。

```powershell
pytest tests/ -v --cov=src
mypy src/

# pre-commit hooks (Ruff + mypy + 標準フック)
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## ライセンス

MIT
