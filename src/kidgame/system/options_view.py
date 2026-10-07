from __future__ import annotations



import random

from dataclasses import dataclass, field



from kidgame.data.question_runtime import PlayQuestion

from kidgame.system.config import bomb_eliminate_count





@dataclass

class OptionsView:

    """現在の問題の表示中選択肢（ボムで消えた肢を除く）。"""



    question: PlayQuestion

    hidden_indices: set[int] = field(default_factory=set)



    @classmethod

    def fresh(cls, question: PlayQuestion) -> OptionsView:

        return cls(question=question, hidden_indices=set())



    def visible_entries(self) -> list[tuple[int, str]]:

        return [

            (i, text)

            for i, text in enumerate(self.question.options)

            if i not in self.hidden_indices

        ]



    def visible_count(self) -> int:

        return len(self.question.options) - len(self.hidden_indices)



    def apply_bomb(self, *, rng: random.Random | None = None) -> int:

        r = rng if rng is not None else random

        correct = self.question.answer_index

        wrong_visible = [

            i

            for i in range(len(self.question.options))

            if i != correct and i not in self.hidden_indices

        ]

        to_remove = min(

            bomb_eliminate_count(len(self.question.options)),

            len(wrong_visible),

        )

        if to_remove <= 0:

            return 0

        picked = r.sample(wrong_visible, to_remove)

        self.hidden_indices.update(picked)

        return to_remove


