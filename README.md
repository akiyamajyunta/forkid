# なぞなぞゲーム開発プロジェクト (for Cursor)

## 概要
未就学児〜小学生を対象とした、PCでオフライン動作するデスクトップ形式の「なぞなぞゲーム」を作成します。

## 開発方針・ルール
- 各モジュールは `docs/` 配下の役割別READMEに従って設計・実装してください。
- オフラインで完結するスタンドアロン構成（Python/Pygame、Tauri/HTML, JS、Electron等）で構築します。
- コード生成や機能実装時は、対応するドキュメントを参照してください。

## 役割別ドキュメント
1. **システムロジック・ゲームループ**: `docs/README_SYSTEM.md`
2. **データ構造・なぞなぞ問題管理**: `docs/README_DATA.md`
3. **画面UI・レイアウト・操作設計**: `docs/README_UI.md`

## 開発の進め方プロンプト (Cursor指示用)
「`README.md` および `docs/` 内の各種READMEを読み込み、開発に必要な技術スタックの選定と基本フレームワークのセットアップを行ってください。」

## 起動方法

```bash
pip install -e ".[dev]"
kidgame
# または
python -m kidgame.main
```

Python 3.14 など新しい環境では `pygame-ce`（`import pygame` 互換）を利用しています。

問題データは [なぞなぞ問題いっぱい](https://nazonazo.nihonsimondai.com/) 由来（約300問）。再取得は `python scripts/build_questions_from_web.py`。

起動時に **ウィンドウモード選択** ダイアログが表示されます（4:3 の 640×480 / 960×720 / 1280×960、フルスクリーン可）。
「起動時に毎回聞く」のチェックを外すと、次回から前回の設定で直接起動します（`%USERPROFILE%\.kidgame\display.json`）。
