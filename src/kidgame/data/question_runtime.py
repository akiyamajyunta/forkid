from __future__ import annotations

import random
from dataclasses import dataclass

from kidgame.data.furigana import RubySegment
from kidgame.data.models import Difficulty, OPTION_COUNT_BY_DIFFICULTY, Question


@dataclass(frozen=True, slots=True)
class PlayQuestion:
    """プレイ中の1問（選択肢数はモードに合わせて確定）。"""

    id: str
    question: str
    options: tuple[str, ...]
    answer_index: int
    hint: str
    ruby: tuple[RubySegment, ...] | None = None
    options_ruby: tuple[tuple[RubySegment, ...], ...] | None = None
    hint_ruby: tuple[RubySegment, ...] | None = None
    source: str = ""


def _filled_option_indices(question: Question) -> list[int]:
    return [i for i, text in enumerate(question.options) if str(text).strip()]


def resolve_for_play(
    question: Question,
    mode: Difficulty,
    *,
    rng: random.Random | None = None,
) -> PlayQuestion:
    r = rng if rng is not None else random
    active = _filled_option_indices(question)
    if question.answer_index not in active:
        raise ValueError(
            f"Question {question.id}: correct option at index "
            f"{question.answer_index} is empty or missing"
        )
    need = min(OPTION_COUNT_BY_DIFFICULTY[mode], len(active))
    if len(active) < need:
        raise ValueError(
            f"Question {question.id} needs at least {need} non-empty options, "
            f"got {len(active)}"
        )

    wrong_indices = [i for i in active if i != question.answer_index]
    pick_indices = [question.answer_index] + r.sample(wrong_indices, need - 1)
    r.shuffle(pick_indices)

    options = tuple(question.options[i] for i in pick_indices)
    answer_index = pick_indices.index(question.answer_index)

    opt_ruby = question.options_ruby
    if opt_ruby and len(opt_ruby) == len(question.options):
        mapped_ruby = tuple(opt_ruby[i] for i in pick_indices)
    else:
        mapped_ruby = None

    return PlayQuestion(
        id=question.id,
        question=question.question,
        options=options,
        answer_index=answer_index,
        hint=question.hint,
        ruby=question.ruby,
        options_ruby=mapped_ruby,
        hint_ruby=question.hint_ruby,
        source=question.source,
    )
