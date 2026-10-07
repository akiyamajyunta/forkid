"""開発者向けなぞなぞ解説文の生成（ゲームでは未使用）。"""

from __future__ import annotations


def make_dev_explanation(question: str, answer: str, source_no: int) -> str:
    q = question.replace("?", "？").strip()
    a = answer.strip()
    lines: list[str] = [
        f"出典: nazonazo.nihonsimondai.com 第{source_no}問。",
        f"正答: 「{a}」。",
    ]

    if "たべられない" in q or "食べられない" in q:
        lines.append(
            "パターン: 「XはXでも、たべられないX」型。"
            "同じ読み・似た語の別意味（道具・飾り・動物名など）を当てるダジャレ。"
        )
    elif "のめない" in q:
        lines.append(
            "パターン: 「のめない」で液体・海を連想させつつ、"
            "正解は「うみ〜」など別種の語句であることが多い。"
        )
    elif "いえの" in q or "家の" in q or "おうち" in q:
        lines.append(
            "パターン: 家・室内と屋外、または身体・持ち物など"
            "「いつもそこにある／いない」対比の比喩。"
        )
    elif "友達" in q:
        lines.append("パターン: 擬人化。常についてくる自然現象・影などを「友達」に例える。")
    elif "夜" in q and ("朝" in q or "なくな" in q):
        lines.append("パターン: 昼夜で現れ方が変わるもの（星・月・露など）。")
    elif "走" in q or "進" in q:
        lines.append(
            "パターン: 動き・時間の比喩（針・影・地平線など、"
            "見えているのに追いつけない／戻るもの）。"
        )
    elif "口" in q or "話" in q or "しゃべ" in q:
        lines.append(
            "パターン: 口・舌・耳の有無と、電話・こだま・言葉など"
            "「伝える」仕組みのひっかけ。"
        )
    elif "名前" in q and "なくな" in q:
        lines.append("パターン: 「名前を呼ぶと消える」→ こだま、エコーなど。")
    elif "お腹" in q or "食べ物" in q:
        lines.append("パターン: 空腹・満腹や有無で性質が変わるもの（風船・文房具など）。")
    elif len(a) <= 2:
        lines.append("パターン: 答えが短い語（1〜2文字）。抽象名詞・自然現象系。")
    else:
        lines.append(
            "パターン: 問いの字面どおりではなく、連想・音・意味のずれから正答にたどり着く。"
        )

    lines.append(f"意図: 「{q}」→「{a}」になるよう読み替える。")
    lines.append("※ ゲーム内ヒント・UI では使わない開発者メモ。")
    return "\n".join(lines)
