# なぞなぞデータ管理仕様 (README_DATA.md)



## 担当範囲

問題データ（JSON）のフォーマット定義、データの読み込み・シャッフル・管理処理。



## 出典

- **推奨出典**: [なぞQ（nazoq.com）](https://nazoq.com/) — 問題・ヒント・答えをサイトから取得（`scripts/build_questions_from_nazoq.py`）。誤答は問題の型（例: 「サイはサイでも」→「サイ」系、食べ物の話→食べ物）に合わせて生成（`kidgame/data/distractors.py`）。既存 CSV の選択肢だけ直すときは `scripts/regenerate_review_options.py`。
- 旧出典: [なぞなぞ問題いっぱい](https://nazonazo.nihonsimondai.com/)（`scripts/build_questions_from_web.py`）。

- 選択肢（誤答）は正答プールから自動生成（各問6択を保持）。



## JSONフォーマット仕様

- ローカルの `.json` ファイルから問題を取得・管理する。

- **難易度別の確認用 CSV**（`questions_review_easy.csv` など）で出題リストを管理。同一 ID が複数ファイルにあれば、ゲーム内では `levels` を統合した1問として扱う。
- **ランタイム読み込み**: 3つの review CSV が揃っている場合は CSV を優先。なければ `questions.json`。
- **JSON の `levels`**: `import_review_csv.py` で CSV から再生成する際に付与される（スクリプト互換用）。

- **選択肢数はゲームモード側**（イージー3 / ノーマル4 / ハード6）。データは **6択まで** 保持し、プレイ時に正解＋ランダムな誤答で抽選。



### JSON構造定義例

```json

{

  "meta": { "source": "nazonazo.nihonsimondai.com", "count": 300 },

  "questions": [

    {

      "id": "web_001",

      "levels": ["easy", "normal"],

      "question": "どんなに走っても…着かないのは何?",

      "options": ["地平線", "影", "…（計6件）"],

      "answer_index": 0,

      "hint": "答えの 最初は「地」だよ",

      "source": "nazonazo.nihonsimondai.com",

      "source_no": 1

    }

  ]

}

```



### `dev_explanation`（開発者用・任意）
- 正答の意図・ダジャレの型・出典番号など。**ゲーム UI では参照しない**。
- ビルド時に自動生成。手編集して上書き可能。

### フリガナ（任意）

- 漢字を含む文は `pykakasi` で読み行を自動表示。

- 手動ルビ: `ruby`, `options_ruby`, `hint_ruby`（`README` 旧例参照）。



### データ再生成・品質調整

```bash
python scripts/build_questions_from_nazoq.py # nazoq.com から取得（推奨）
python scripts/build_questions_from_web.py   # 旧サイトから再取得
python scripts/reconcile_questions.py        # 正答・問題文・ヒントを出典と整合
python scripts/export_review_excel.py        # 確認用 Excel
python scripts/import_review_csv.py        # CSV 編集後 → questions.json
```

- ヒント: `data/hints_by_no.json`（1〜300、ゲーム用）
- 個別修正: `scripts/curated_overrides.json`（正答・ヒントの上書き）

### 確認用 CSV（難易度別・ゲームも参照）

```bash
python scripts/export_review_csv.py
python scripts/import_review_csv.py   # JSON へ反映（reconcile 等の前後）
```

- `data/questions_review_easy.csv`
- `data/questions_review_normal.csv`
- `data/questions_review_hard.csv`
- `data/questions_review.xlsx` … **Excel 版（推奨）** 難易度ごとシート・正解列ハイライト

```bash
python scripts/export_review_excel.py
python scripts/export_review_csv.py
```

カラム: `ID`, `問題文`, `選択肢A`, `選択肢B`, `選択肢C`, `選択肢D`, `正解記号`, `正解テキスト`, `ヒント`, `開発者解説`（`questions_review_easy.csv` 形式）。

- **選択肢A〜D**: プレイ時の4択（B〜D がすべて空の行だけ、旧仕様どおり誤答を自動生成）。
- **正解記号**: 正解列（`A`〜`D`）。通常 `A`。
- **正解テキスト**: 解説・確認用（読み・補足付き可）。**選択肢Aと同一でなくてよい**。ゲームの選択肢表示は **A〜D列のまま**（正解は **正解記号** の列を選ぶ）。
- 旧9列 CSV（選択肢D なし）も読み込み互換。

**プレイ時**: モードに応じた択数（3/4/6）をデータから抽選し、**表示順をランダムにシャッフル**。画面上のラベルは上から **A, B, C…**。


