import unittest

from reasoning.budget import CONSTRAINTS, PROMPT, Allocation, broken

ANSWER = Allocation(engineering=1200, sales=720, marketing=480, operations=600, hr=240, finance=360, legal=240)


class BudgetTest(unittest.TestCase):
    def test_fourteen_constraints_in_the_prompt(self):
        self.assertEqual(len(CONSTRAINTS), 14)
        self.assertIn("14. ", PROMPT)

    def test_answer_closes_at_384m(self):
        self.assertEqual(broken(ANSWER), [])
        self.assertEqual(sum(ANSWER.model_dump().values()), 3840)

    def test_three_million_does_not_close(self):
        # Beto's instant answer: a round 3,000 split evenly-ish
        beto = Allocation(engineering=600, sales=440, marketing=400, operations=400, hr=400, finance=400, legal=360)
        self.assertIn(1, broken(beto))

    def test_wrong_branch_of_the_legal_rule_is_caught(self):
        self.assertIn(9, broken(ANSWER.model_copy(update={"legal": 320, "finance": 280})))

    def test_single_solution(self):
        # Constraints 5, 6, 7 and 10 fix sales, engineering, operations and finance from marketing and hr, so
        # searching marketing, hr and legal over every allowed amount covers all candidates.
        steps = range(200, 1281, 40)
        found = []
        for m in steps:
            for h in steps:
                for legal in steps:
                    if (3 * m) % 2 or (3 * h) % 2:
                        continue
                    s = 3 * m // 2
                    e = s + m
                    a = Allocation(engineering=e, sales=s, marketing=m, operations=e // 2, hr=h, finance=3 * h // 2,
                                   legal=legal)
                    if e % 2 == 0 and not broken(a):
                        found.append(a)
        self.assertEqual(found, [ANSWER])


if __name__ == "__main__":
    unittest.main()
