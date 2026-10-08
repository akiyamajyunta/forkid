"""問題文・正答に合う誤答選択肢の生成。"""

from __future__ import annotations

import random
import re

from kidgame.data.kid_language import (
    KID_SIMPLE_DISTRACTORS,
    is_kid_friendly_distractor,
    kid_dai_fallbacks,
)

_DAI_MO_PATTERN = re.compile(
    r"([ぁ-んァ-ヶ一-龥々〆ヵヶ]+)は\1(?:でも|だが|だけど|でも、)"
)
_DAI_MO_LOOSE = re.compile(
    r"([ぁ-んァ-ヶ一-龥々]{1,8})は([ぁ-んァ-ヶ一-龥々]{1,12})でも"
)

_FOOD_QUESTION_MARKERS = (
    "たべ",
    "食べ",
    "たべもの",
    "食べ物",
    "お菓子",
    "おかし",
    "おやつ",
    "ごはん",
    "ご飯",
    "料理",
    "スープ",
    "ラーメン",
    "うどん",
    "そば",
    "パン",
    "のみもの",
    "飲み物",
    "お酒",
    "しょく",
    "食",
    "にく",
    "肉",
    "さかな",
    "魚",
    "くだもの",
    "果物",
    "やさい",
    "野菜",
    "デザート",
    "ケーキ",
    "あまい",
    "甘い",
    "すっぱい",
    "酸っぱい",
    "しょっぱい",
    "おいしい",
    "レストラン",
    "おすし",
    "寿司",
)

_FOOD_ANSWER_MARKERS = (
    "パン",
    "ケーキ",
    "うどん",
    "そば",
    "ラーメン",
    "カレー",
    "ごはん",
    "おにぎり",
    "寿司",
    "おすし",
    "刺身",
    "さしみ",
    "りんご",
    "みかん",
    "バナナ",
    "いちご",
    "ぶどう",
    "メロン",
    "スイカ",
    "たまご",
    "卵",
    "チーズ",
    "ハム",
    "ソーセージ",
    "餃子",
    "ぎょうざ",
    "団子",
    "だんご",
    "おやき",
    "せんべい",
    "クッキー",
    "チョコ",
    "アイス",
    "プリン",
    "ゼリー",
    "ジュース",
    "お茶",
    "紅茶",
    "コーヒー",
    "ビール",
    "酒",
    "みそ",
    "味噌",
    "しょうゆ",
    "醤油",
    "塩",
    "砂糖",
    "キャベツ",
    "トマト",
    "ナス",
    "なす",
    "にんじん",
    "じゃが",
    "ポテト",
    "コロッケ",
    "天ぷら",
    "とんかつ",
    "からあげ",
    "焼き鳥",
    "やきとり",
    "おでん",
    "鍋",
    "なべ",
    "豆腐",
    "とうふ",
    "納豆",
    "わかめ",
    "のり",
    "かつお",
    "鮭",
    "さけ",
    "鯖",
    "さば",
    "エビ",
    "えび",
    "カニ",
    "かに",
    "イカ",
    "いか",
    "タコ",
    "たこ",
    "ベーコン",
    "ピザ",
    "パスタ",
    "スパゲッティ",
    "ドーナツ",
    "どら焼",
    "まんじゅう",
    "饅頭",
    "羊羹",
    "ようかん",
    "大福",
    "だいふく",
    "もち",
    "餅",
    "おはぎ",
    "しるこ",
    "汁粉",
)


def good_distractor_text(text: str, *, for_kids: bool = False) -> bool:
    if not text or len(text) > (18 if for_kids else 20):
        return False
    if "（" in text or "(" in text or "】" in text or "#" in text:
        return False
    if text.strip() in {"？", "?", "…", "...", "わからない", "こたえ", "答え", "答"}:
        return False
    if for_kids and not is_kid_friendly_distractor(text):
        return False
    return True


def extract_dai_keyword(question: str) -> str | None:
    """「サイはサイでも」型の繰り返しキーワード。"""
    q = question.replace(" ", "").replace("\u3000", "")
    m = _DAI_MO_PATTERN.search(q)
    if m:
        return m.group(1)
    m = _DAI_MO_LOOSE.search(q)
    if m and m.group(1) == m.group(2):
        return m.group(1)
    return None


def question_wants_food_distractors(question: str) -> bool:
    q = question
    return any(m in q for m in _FOOD_QUESTION_MARKERS)


def answer_looks_like_food(text: str) -> bool:
    return any(m in text for m in _FOOD_ANSWER_MARKERS)


def _score_candidate(
    question: str,
    answer: str,
    candidate: str,
    *,
    dai_keyword: str | None,
    food_mode: bool,
    for_kids: bool = False,
) -> float:
    if candidate == answer or not good_distractor_text(candidate, for_kids=for_kids):
        return -1.0

    score = 0.0

    if dai_keyword:
        if candidate.startswith(dai_keyword):
            score += 14.0
        elif dai_keyword in candidate:
            score += 10.0
        elif answer and len(answer) >= 2 and candidate.startswith(answer[:2]):
            score += 6.0

    if food_mode:
        if answer_looks_like_food(candidate):
            score += 12.0
        else:
            score -= 4.0

    if answer:
        if len(candidate) == len(answer):
            score += 2.0
        if candidate and answer and candidate[0] == answer[0]:
            score += 3.0
        # 正答と同じ語尾（…って な〜んだ系の答えが短い名詞）
        if len(answer) >= 2 and len(candidate) >= 2 and candidate[-1] == answer[-1]:
            score += 1.0

    # 問題文に出てくる短い語を含む候補（キーワード寄せ）
    for token in re.findall(r"[ぁ-んァ-ヶ一-龥々]{2,6}", question):
        if token in candidate and token not in ("なんだ", "なあに", "これ", "もの"):
            score += 1.5

    return score


def build_six_options(
    question: str,
    answer: str,
    pool: list[str],
    rng: random.Random,
    *,
    for_kids: bool = False,
    fix_correct_at_a: bool = False,
) -> tuple[list[str], int]:
    """
    正答 + 誤答5 = 6択。問題の型（だじゃれキーワード・食べ物など）に合う誤答を優先。
    """
    dai_keyword = extract_dai_keyword(question)
    food_mode = question_wants_food_distractors(question) and (
        answer_looks_like_food(answer) or food_mode_heuristic(question)
    )

    scored: list[tuple[float, str]] = []
    for cand in pool:
        if cand == answer:
            continue
        s = _score_candidate(
            question,
            answer,
            cand,
            dai_keyword=dai_keyword,
            food_mode=food_mode,
            for_kids=for_kids,
        )
        if s >= 0:
            scored.append((s + rng.random() * 0.35, cand))

    scored.sort(key=lambda x: (-x[0], x[1]))
    distractors: list[str] = []
    seen: set[str] = set()
    for _, cand in scored:
        if cand in seen:
            continue
        seen.add(cand)
        distractors.append(cand)
        if len(distractors) >= 5:
            break

    # キーワード型でまだ足りないときはプールから prefix 一致を追加
    if dai_keyword and len(distractors) < 5:
        for cand in pool:
            if cand == answer or cand in seen:
                continue
            if not good_distractor_text(cand, for_kids=for_kids):
                continue
            if dai_keyword in cand or cand.startswith(dai_keyword):
                seen.add(cand)
                distractors.append(cand)
                if len(distractors) >= 5:
                    break

    fallbacks = _fallback_distractors(dai_keyword, food_mode, answer, for_kids=for_kids)
    for fb in fallbacks:
        if len(distractors) >= 5:
            break
        if fb != answer and fb not in seen and good_distractor_text(fb, for_kids=for_kids):
            seen.add(fb)
            distractors.append(fb)

    options = [answer] + distractors[:5]
    if fix_correct_at_a:
        return options, 0
    rng.shuffle(options)
    return options, options.index(answer)


def food_mode_heuristic(question: str) -> bool:
    """食べる・待たされる など食事シーン。"""
    return bool(
        re.search(r"たべ|食べ|のむ|飲む|おかし|お菓子|しょくじ|食事", question)
    )


def _fallback_distractors(
    dai_keyword: str | None,
    food_mode: bool,
    answer: str,
    *,
    for_kids: bool = False,
) -> list[str]:
    if for_kids:
        if dai_keyword:
            return kid_dai_fallbacks(dai_keyword)
        if food_mode:
            return list(KID_SIMPLE_DISTRACTORS[:10])
        return list(KID_SIMPLE_DISTRACTORS)
    if dai_keyword:
        return [
            f"{dai_keyword}コ",
            f"{dai_keyword}ド",
            f"{dai_keyword}ル",
            f"お{dai_keyword}",
            f"{dai_keyword}ちゃん",
        ]
    if food_mode:
        return ["りんご", "みかん", "おにぎり", "たまご", "うどん", "パン", "ケーキ"]
    return ["えんぴつ", "かばん", "くつ", "ぞう", "でんわ", "まど", "はさみ"]
