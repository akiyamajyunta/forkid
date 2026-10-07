from __future__ import annotations



from dataclasses import dataclass

from enum import StrEnum

from typing import Any, Self



from kidgame.data.furigana import (

    RubySegment,

    parse_options_ruby,

    parse_ruby_list,

)



MAX_OPTIONS = 6





class Difficulty(StrEnum):

    EASY = "easy"

    NORMAL = "normal"

    HARD = "hard"





# README_SYSTEM: プレイ時の選択肢数（データは最大6択を保持）

OPTION_COUNT_BY_DIFFICULTY: dict[Difficulty, int] = {

    Difficulty.EASY: 3,

    Difficulty.NORMAL: 4,

    Difficulty.HARD: 6,

}





def _parse_levels(raw: dict[str, Any]) -> frozenset[Difficulty]:

    if "levels" in raw:

        items = raw["levels"]

        if not isinstance(items, list) or not items:

            raise ValueError("levels must be a non-empty array")

        return frozenset(Difficulty(str(x).lower()) for x in items)

    if "difficulty" in raw:

        return frozenset({Difficulty(str(raw["difficulty"]).lower())})

    raise ValueError("question must have 'levels' or legacy 'difficulty'")





@dataclass(frozen=True, slots=True)

class Question:

    id: str

    levels: frozenset[Difficulty]

    question: str

    options: tuple[str, ...]

    answer_index: int

    hint: str

    ruby: tuple[RubySegment, ...] | None = None

    options_ruby: tuple[tuple[RubySegment, ...], ...] | None = None

    hint_ruby: tuple[RubySegment, ...] | None = None

    source: str = ""
    dev_explanation: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Self:

        levels = _parse_levels(raw)

        options = tuple(str(o) for o in raw["options"])

        answer_index = int(raw["answer_index"])



        if len(options) < 3 or len(options) > MAX_OPTIONS:

            raise ValueError(

                f"Question {raw.get('id')!r}: options length must be 3..{MAX_OPTIONS}, "

                f"got {len(options)}"

            )

        if not 0 <= answer_index < len(options):

            raise ValueError(

                f"Question {raw.get('id')!r}: answer_index {answer_index} "

                f"out of range for {len(options)} options"

            )



        return cls(

            id=str(raw["id"]),

            levels=levels,

            question=str(raw["question"]),

            options=options,

            answer_index=answer_index,

            hint=str(raw.get("hint", "")),

            ruby=parse_ruby_list(raw.get("ruby")),

            options_ruby=parse_options_ruby(raw.get("options_ruby"), len(options)),

            hint_ruby=parse_ruby_list(raw.get("hint_ruby")),

            source=str(raw.get("source", "")),
            dev_explanation=str(raw.get("dev_explanation", "")),
        )



    def appears_in(self, mode: Difficulty) -> bool:

        return mode in self.levels



    @property

    def correct_answer(self) -> str:

        return self.options[self.answer_index]





@dataclass(frozen=True, slots=True)

class QuestionBank:

    """JSON から読み込んだ全問題の集合。"""



    questions: tuple[Question, ...]



    @classmethod

    def from_dict(cls, data: dict[str, Any]) -> Self:

        if "questions" not in data:

            raise ValueError("JSON root must contain a 'questions' array")

        items = data["questions"]

        if not isinstance(items, list):

            raise ValueError("'questions' must be an array")

        questions = tuple(Question.from_dict(q) for q in items)

        _assert_unique_ids(questions)

        return cls(questions=questions)



    def for_mode(self, mode: Difficulty) -> tuple[Question, ...]:

        return tuple(q for q in self.questions if q.appears_in(mode))



    def grouped_by_mode(self) -> dict[Difficulty, tuple[Question, ...]]:

        return {d: self.for_mode(d) for d in Difficulty}





def _assert_unique_ids(questions: tuple[Question, ...]) -> None:

    seen: set[str] = set()

    for q in questions:

        if q.id in seen:

            raise ValueError(f"Duplicate question id: {q.id!r}")

        seen.add(q.id)


