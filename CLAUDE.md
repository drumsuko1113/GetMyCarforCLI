# carsensor-cli — Claude Code 実装ガイド

## プロジェクト概要

カーセンサー（https://www.carsensor.net）をスクレイピングし、
Windows PowerShell ターミナル上で動作する中古車検索CLIツールを Python で実装する。

## ターゲット環境

- **OS**: Windows 10/11（PowerShell 5.1 以上 / Windows Terminal 推奨）
- **言語**: Python 3.10+
- **配布**: pip install 対応（`pyproject.toml` 構成）

---

## 機能要件

### 1. 検索機能
- メーカー・車種名によるキーワード検索
- 条件フィルター（価格・年式・走行距離・地域）
- ソート（価格順・新着順）& ページネーション（件数制限付き）
- 検索条件のプリセット保存・呼び出し（JSONファイル）

### 2. お気に入り機能
- 検索結果から車両を登録・削除
- お気に入り一覧表示・詳細確認
- 複数台のスペック比較表示
- `favorites.json` にローカル永続保存

### 3. スクレイピング基盤
- カーセンサー対応HTMLパーサー（`requests` + `BeautifulSoup4`）
- JS描画が必要な場合は `Playwright` にフォールバック
- リクエスト間隔制御（最低1秒以上）・リトライ処理
- 取得結果のローカルキャッシュ（TTL: 30分）

### 4. TUI表示
- `Rich` ライブラリによる表形式・カラー一覧表示
- 車両詳細画面・比較画面
- 矢印キーによるナビゲーション（`questionary` または `Rich` の `Live`）

---

## 非機能要件

| 項目 | 内容 |
|------|------|
| 対応OS | Windows 10/11（PowerShell） |
| Python | 3.10+ |
| 配布 | pip install（pyproject.toml） |
| 倫理 | robots.txt 遵守、個人利用目的のみ |

---

## ディレクトリ構成（推奨）

```
GetMyCarforCLI/
├── pyproject.toml
├── README.md
├── CLAUDE.md
├── src/
│   └── getmycar/
│       ├── __init__.py
│       ├── main.py         # Controller: CLIエントリーポイント
│       ├── scraper.py      # Model: スクレイピング基盤
│       ├── parser.py       # Model: HTML パーサー
│       ├── filters.py      # Model: 検索フィルター
│       ├── favorites.py    # Model: お気に入り管理
│       ├── display.py      # View:  Rich TUI 表示
│       ├── cache.py        # Model: キャッシュ管理
│       └── utils.py        # 共通ユーティリティ（DRY）
├── data/
│   ├── favorites.json      # お気に入りデータ（gitignore）
│   └── cache/              # キャッシュ（gitignore）
└── tests/
    ├── test_scraper.py
    ├── test_parser.py
    ├── test_filters.py
    ├── test_favorites.py
    ├── test_cache.py
    └── test_display.py
```

---

## 主要依存ライブラリ

```toml
[project.dependencies]
requests = ">=2.31"
beautifulsoup4 = ">=4.12"
rich = ">=13.0"
questionary = ">=2.0"
click = ">=8.1"
playwright = ">=1.40"   # オプション（JS描画用）
```

---

## 開発原則（必須）

### アーキテクチャ
- **MVC パターン**で実装すること
  - **Model** (`scraper.py`, `parser.py`, `cache.py`, `favorites.py`, `filters.py`) — データ取得・加工・永続化
  - **View** (`display.py`) — Rich による TUI 表示のみ。ロジックを含めないこと
  - **Controller** (`main.py`) — Click コマンド。Model と View を繋ぐのみ

### 設計原則
- **SOLID 原則**を遵守すること
  - **S** (単一責任): 1クラス・1関数は1つの責務のみ
  - **O** (開放閉鎖): 拡張に開き、修正に閉じた設計（例: フィルターは継承・追加で拡張）
  - **L** (リスコフ置換): サブクラスは親クラスと置換可能に
  - **I** (インターフェース分離): 不要なメソッドを実装させない小さなインターフェース
  - **D** (依存性逆転): 具体クラスでなく抽象（Protocol / ABC）に依存する
- **DRY 原則**を遵守すること
  - 同じロジックを2箇所以上に書かない
  - 共通処理は `utils.py` や基底クラスに切り出す

### テスト駆動開発（TDD）
- **Red → Green → Refactor** のサイクルで実装すること
  1. **Red**: まず失敗するテストを書く
  2. **Green**: テストが通る最小限の実装をする
  3. **Refactor**: コードを整理・改善する（テストは引き続きグリーンを維持）
- テストフレームワーク: `pytest`
- 外部HTTP通信は `responses` または `unittest.mock` でモック化すること
- カバレッジ目標: 各モジュール 80% 以上

---

## 各タスク完了条件（必須チェック）

各 Issue の実装完了前に、**以下をすべて満たすこと**を確認すること。

```
□ 1. テストがすべてグリーン
      pytest tests/ -v  →  全件 PASSED

□ 2. ビルド・インストールの成功
      pip install -e .  →  エラーなし
      getmycar --help   →  ヘルプが表示される

□ 3. 型チェックの通過
      mypy src/  →  エラーなし（または既知の警告のみ）

□ 4. リファクタリングの実施
      - 重複コードの除去（DRY）
      - 関数・クラスの責務が単一になっているか確認（SOLID-S）
      - 命名が意図を明確に表しているか確認
      - コメントが「なぜ」を説明しているか確認（「何を」はコードから読める）

□ 5. Issue のクローズ
      gh issue close <番号> -c "実装完了。テスト・ビルド確認済み。"
```

---

## 実装順序（推奨）

1. Issue #1 → #2 → #3 → #4（基盤）
2. Issue #5 → #6（ロジック）
3. Issue #7 → #8（UI/CLI）
4. Issue #9 → #10（品質）

---

## 注意事項

- スクレイピングはカーセンサーの `robots.txt` を必ず確認すること
- リクエストは**個人利用・低頻度**に限定すること
- `data/` ディレクトリは `.gitignore` に含め、個人データをコミットしないこと
- PowerShell での実行時は `$env:PYTHONIOENCODING="utf-8"` を設定すること
