"""問題文・正答から子ども向けの間接ヒントを生成（答えの文字は出さない）。"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_OVERRIDES_PATH = Path(__file__).resolve().parent / "curated_overrides.json"
_HINTS_BY_NO_PATH = Path(__file__).resolve().parents[1] / "data" / "hints_by_no.json"


@lru_cache(maxsize=1)
def _hints_by_no() -> dict[str, str]:
    if not _HINTS_BY_NO_PATH.is_file():
        return {}
    return json.loads(_HINTS_BY_NO_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _overrides() -> dict[str, dict]:
    if not _OVERRIDES_PATH.is_file():
        return {}
    return json.loads(_OVERRIDES_PATH.read_text(encoding="utf-8"))


def _has_pun_answer(answer: str) -> bool:
    return "（" in answer or "(" in answer or "×" in answer


def _pun_family_hint(question: str, answer: str) -> str | None:
    a = answer
    if "急" in a:
        return "「いそぐ」と 同じ に 聞こえる 数字 かも"
    if "避暑" in a or "でか" in a:
        return "暑い・大きい など、別の 言葉 に 聞こえる 仕事 か 人 だよ"
    if "腐" in a or "腐乱" in a:
        return "「ふ」と 聞こえる パン の 名前 かも"
    if "チュウ" in a or "ちゅう" in a.lower():
        return "「チュウ」の 下… 言葉 の 位置 で 考えてみて"
    if "カモン" in a or "カモ" in a:
        return "「ん」を つける と 呼びかけ に 聞こえる 鳥 だよ"
    if "ハンガー" in a or "バー" in a:
        return "棒（バー）を 取る と 別の 言葉 に なる よ"
    if "ミドリ" in a and "3" in question:
        return "「3」と 鳥 の 数 を かけてみて"
    if "ワン" in a or "ワイン" in a:
        return "中の 文字 が なくなる と 別の 言葉 に なる 飲み物 だよ"
    if "はこぶね" in a or "箱舟" in a:
        return "荷物 を はこぶ + 船 の 言葉 遊び だよ"
    if "カナダ" in a:
        return "漢字で 書けない 国 の 名前 だよ"
    if "シド" in a and "そら" in question:
        return "音階 の 最後 の 音 に 関係 する よ"
    if "ぷんぷん" in a:
        return "怒った とき の 音 に 似た 言葉 だよ"
    if "２じ" in a or "2字" in a:
        return "「おやつ」は 何文字？ 今 の 時刻 も 文字数 で 答える よ"
    if "９秒" in a or "急病" in a:
        return "「急」と 聞こえる 時間 の 単位 だよ"
    if "表" in a and "ヒョウ" in a:
        return "「表」と 読める 動物 の 名前 だよ"
    if "皿だ" in a or "サラダ" in a:
        return "器（さら）そのもの が 答え になる 料理 だよ"
    if "パジャマ" in a:
        return "寝るとき 着る けど 邪魔 に 感じる こと も ある よ"
    if "右" in a and "漢字" in a:
        return "漢字の どちら側 に 「口」がある か 考えてみて"
    if "マイカー" in a:
        return "イカ + 車 の 言葉 遊び だよ"
    if "植木" in a and "庭" in question:
        return "「えき」と 読める 庭 の もの だよ"
    if "なべぶた" in a:
        return "鍋 の ふた の こと だよ"
    if "ぞうきん" in a:
        return "よごれ を ふく 布 の こと だよ"
    if "くまなく" in a or "熊（" in a:
        return "「くまなく」探す と 同じ 音 の 動物 だよ"
    if "コンブ" in a and "キツネ" in question:
        return "昆布 + おなら の ダジャレ だよ"
    if "肉まん" in a:
        return "黙って 食べる 蒸した 食べ物 だよ"
    if "昼食や夕食" in a:
        return "朝 以外 の 食事 の 名前 だよ"
    if "医者" in a and "コンサート" in question:
        return "見られる 側 で お金 が かかる 人 だよ"
    if "こっくり" in a:
        return "眠く なる と 出る うなずき の 音 だよ"
    if "左手" in a and "右手" in question:
        return "右手 だけ では できない 体 の 一部 だよ"
    if "ニセ札" in a:
        return "本物 じゃ ない お金。知ってる 人 は 欲しく ない よ"
    if "方向音痴" in a:
        return "歌 は 上手 なのに 道 に 迷う 人 の こと だよ"
    if "ハゲタカ" in a:
        return "「はげ」と 髪 の ない 鳥 だよ"
    if "バター" in a and "倒れ" in question:
        return "パン に のせる と なめらか になる 食べ物 だよ"
    if "ジャマイカ" in a:
        return "「じゃま」が 聞こえる 国 だよ"
    if "ポケット" in a and "ポット" in question:
        return "ポット + 毛（も）の 言葉 遊び だよ"
    if "パパイヤ" in a:
        return "「パパ」が 嫌 な 果物 の 名前 だよ"
    if "こしょう" in a and "くしゃみ" in question:
        return "くしゃみ の 音 と 同じ 調味料 だよ"
    if "コンドル" in a and "キツネ" in question:
        return "お金（こん）+ 変身 の ダジャレ だよ"
    if "9(急)" in a or a == "9(急)":
        return "「いそぐ」と 同じ 音 の 数字 だよ"
    if "サンゴ" in a:
        return "3×5=15 の ダジャレ だよ"
    if "刑事" in a:
        return "「でかい」刑事 の 言葉 遊び だよ"
    if "秘書" in a:
        return "暑い と 涼しい 場所 へ… 仕事 の ダジャレ だよ"
    if "床屋" in a:
        return "「かり」に 行って 「から」れる 場所 だよ"
    return None


def make_contextual_hint(question: str, answer: str, source_no: int) -> str:
    q = question.strip()
    a = answer.strip()
    key = str(source_no)
    ov = _overrides().get(key, {})
    if ov.get("hint"):
        return ov["hint"]
    by_no = _hints_by_no()
    if key in by_no:
        return by_no[key]

    # 正答キー（hint_generator から移管・拡充）
    from hint_generator import _ANSWER_HINTS  # noqa: PLC0415

    if a in _ANSWER_HINTS:
        return _ANSWER_HINTS[a]

    pun = _pun_family_hint(q, a)
    if pun:
        return pun

    if _has_pun_answer(a):
        return "ことば の 音 や 漢字 の 数 で ひっかける なぞ だよ。声に 出して 考えてみて"

    if "たべられない" in q or "食べられない" in q:
        return "同じ 言葉 だけど 食べ物 じゃ ない 意味 かも？"
    if "のめない" in q:
        return "海の 水 じゃ なく、名前 に「うみ」が つく もの かも"
    if "着かない" in q and ("走" in q or "飛" in q):
        return "見える 先 に ずっと ある 線 みたい な もの"
    if "戻ってき" in q and "進" in q:
        return "同じ 場所 を ぐるぐる 回る イメージ"
    if "くっついて" in q and "友達" in q:
        return "光 と いっしょ に 動く 黒い 仲間"
    if "家の前" in q or "家の 前" in q:
        return "家 の 前 を 通る けど 中には 入らない 道"
    if "いつもおうち" in q or "いつも おうち" in q:
        return "外に 出ても 体 について くる もの かも"
    if "夏" in q and "冬" in q:
        return "季節 で 動き方 が 変わる 木 から 落ちる もの かも"
    if "空に" in q and "のぼ" in q:
        return "上 へ のぼる けど 鳥 でも 飛行機 でも ない もの"
    if "一滴" in q and "水" in q:
        return "木 より 高く 登れる 小さな 虫 だよ"
    if "足がない" in q and ("話" in q or "お話" in q):
        return "届けて くれる 手紙 や 電話 の ような もの かも"
    if "夜" in q and ("朝" in q or "いなくな" in q):
        return "夜 見える 空 の 光 だよ"
    if "窓" in q and "ガラス" in q:
        return "割ら なく ても 部屋 に 入る 明るさ"
    if "うまれ" in q and "まだ" in q:
        return "まだ 中 に いる 食べ物 や 時間 の 話 かも"
    if "増えていく" in q and "生き" in q:
        return "生きる ほど 大きく なる 数字 かも"
    if "おてんとう" in q:
        return "日さん で とけたり 小さく なる もの だよ"
    if "食べ物があると" in q and "なき" in q:
        return "油 が 熱い と 音 を 立てる 道具 かも"
    if "耳も口もない" in q:
        return "山 で 声 が 返って くる 自然 の 仕組み だよ"
    if "名前を呼ぶと" in q and "いなくな" in q:
        return "静か に している 状態 が こわれる よ"
    if "赤い服" in q and "紙" in q:
        return "赤い 体 で 手紙 を 入れる 箱 だよ"
    if "お腹がいっぱい" in q:
        return "空気 を 入れる と 軽く なる 丸い もの だよ"
    if "口からだして" in q and "耳" in q:
        return "声 に 出して 聞く 言葉 だよ"
    if "水を飲み込むと" in q:
        return "水 で 消える あたたかい もの だよ"
    if "赤い帽子" in q:
        return "火 を つける と 短く なる もの だよ"
    if "よろい" in q and "エビ" in a:
        return "背中 が 丸い 海 の 生き物 だよ"
    if "鏡" in a or "見る人によって" in q:
        return "自分 の 顔 が うつる 道具 だよ"
    if "手袋" in a and "部屋" in q:
        return "指 が 五つ ある 部屋 の ような もの だよ"
    if "お風呂" in a:
        return "上 は お湯、下 は ガス… お風呂 の こと だよ"
    if "サイコロ" in a:
        return "振る と 目 が いくつ 出る か わかる 遊び道具 だよ"
    if "ピアノ" in a:
        return "白 と 黒 の 鍵盤 で 音 を 出す 楽器 だよ"
    if "恋愛" in a:
        return "胸 が ドキドキ する 気持ち の こと だよ"
    if "結婚指輪" in a:
        return "指 に つける 丸い 装飾 の こと だよ"

    # 最後: 問いの主題を反復（直球は避ける）
    snippet = re.sub(r"[?？!！。、]", "", q)
    if len(snippet) > 28:
        snippet = snippet[:28] + "…"
    return "ことば の 音 や 漢字 の 数 で ひっかける なぞ だよ。声に 出して 考えてみて"
