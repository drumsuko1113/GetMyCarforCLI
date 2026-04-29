# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.1] - 2026-04-29

### Added
- 初期版。カーセンサーのスクレイピング基盤、検索 / お気に入り / プリセット / キャッシュ管理コマンド。
- Rich ベースの TUI 表示と Click ベースの CLI コントローラー。
- TOML 設定ファイル、ロギング、共通例外階層。
- GitHub Actions による CI（pytest / mypy / build / pre-commit）とセキュリティ（pip-audit / gitleaks / CodeQL）。
- カバレッジ 80% を CI ゲートで強制。

[Unreleased]: https://github.com/drumsuko1113/GetMyCarforCLI/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/drumsuko1113/GetMyCarforCLI/releases/tag/v0.0.1
