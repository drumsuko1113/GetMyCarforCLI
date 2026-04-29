# Contributing

## ブランチ運用

- 既定ブランチ: `develop` (作業統合先)
- リリース時に `develop` → `main` へマージ
- 各タスクは GitHub Issue を起票し、`feature/issue-<番号>-<short-desc>` ブランチを切る
- PR は `develop` を base にする

## 開発サイクル (TDD 必須)

1. **Red**: まず失敗するテストを書く (`tests/test_xxx.py`)
2. **Green**: テストが通る最小限のコードを書く
3. **Refactor**: 重複削除・命名整理・SOLID 原則の確認

## マージ前チェックリスト

CLAUDE.md の「各タスク完了条件」と同じです。

- [ ] `pytest tests/ -v` 全件 PASS
- [ ] `mypy src/` エラーなし
- [ ] `pip install -e .` + `getmycar --help` 動作確認
- [ ] 重複コードや責務違反のリファクタ済み
- [ ] CI 全ジョブ green
- [ ] Issue を `gh issue close` で閉じる

## コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) 準拠を推奨。

- `feat(scope): summary (#issue)`
- `fix(scope): summary (#issue)`
- `refactor(scope): ...`
- `docs: ...`
- `ci: ...`

## PR テンプレート

`.github/PULL_REQUEST_TEMPLATE.md` を参照。
