# なぞなぞデータ管理仕様 (README_DATA.md)



## 担当範囲

問題データ（JSON）のフォーマット定義、データの読み込み・シャッフル・管理処理。



## 出典

- 問題文・正答は [なぞなぞ問題いっぱい](https://nazonazo.nihonsimondai.com/) より最大300問を取得（`scripts/build_questions_from_web.py`）。

- 選択肢（誤答）は正答プールから自動生成（各問6択を保持）。



## JSONフォーマット仕様

- ローカルの `.json` ファイルから問題を取得・管理する。

- **難易度は問題の属性**（`levels` 配列）。1問が複数モードに登録可能。

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
python scripts/build_questions_from_web.py   # サイトから再取得
python scripts/reconcile_questions.py        # 正答・問題文・ヒントを出典と整合
python scripts/export_review_excel.py        # 確認用 Excel
```

- ヒント: `data/hints_by_no.json`（1〜300、ゲーム用）
- 個別修正: `scripts/curated_overrides.json`（正答・ヒントの上書き）

### 確認用 CSV（ゲーム未使用）

```bash
python scripts/export_review_csv.py
```

- `data/questions_review.xlsx` … **Excel 版（推奨）** 見出し固定・フィルタ・正解列ハイライト
- `data/questions_review.csv` … CSV 版（UTF-8 BOM）

```bash
python scripts/export_review_excel.py
python scripts/export_review_csv.py
```


