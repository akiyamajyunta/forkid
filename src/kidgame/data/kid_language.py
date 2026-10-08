"""子ども向け（イージー）の語彙チェック。"""

from __future__ import annotations

import re

# 誤答に使わない語（正答は問題のためそのまま残す）
_KID_BLOCK_SUBSTRINGS = (
    "こたえ",
    "答え",
    "万引き",
    "Gメン",
    "ホップ",
    "ビール",
    "お酒",
    "酒",
    "タバコ",
    "ブラジャー",
    "うんこ",
    "うんち",
    "モツ煮",
    "しりもち",
    "タクシー",
    "つけすぎ",
    "プルプルになった",
    "ヘタは",
    "A:",
    "B:",
    "／",
    "♣",
    "♠",
    "ナイフ",
    "拳銃",
    "ピストル",
    "いじめ",
    "殺",
    "死体",
    "レイプ",
    "セックス",
    "ブラジャ",
)

# 誤答のフォールバック（やさしい言葉）
KID_SIMPLE_DISTRACTORS: tuple[str, ...] = (
    "りんご",
    "みかん",
    "バナナ",
    "おにぎり",
    "たまご",
    "パン",
    "うさぎ",
    "ねこ",
    "いぬ",
    "ぞう",
    "くるま",
    "でんしゃ",
    "ほし",
    "つき",
    "はな",
    "えんぴつ",
    "かばん",
    "くつ",
    "ぼうし",
    "まど",
    "はさみ",
    "ふくろ",
    "おはな",
)

_KID_MAX_OPTION_LEN = 18


def is_kid_friendly_distractor(text: str) -> bool:
    if not text or len(text) > _KID_MAX_OPTION_LEN:
        return False
    for bad in _KID_BLOCK_SUBSTRINGS:
        if bad in text:
            return False
    # 漢字だらけの長い語は避ける（ひらがな・カタカナを少し含むものを優先）
    kanji = len(re.findall(r"[一-龥]", text))
    if kanji >= 6 and "（" not in text:
        return False
    return True


def kid_dai_fallbacks(keyword: str) -> list[str]:
    """だじゃれキーワード用のやさしい誤答例。"""
    return [
        f"お{keyword}",
        f"{keyword}ちゃん",
        f"小さな{keyword}",
        f"{keyword}さん",
        f"赤い{keyword}",
    ]
