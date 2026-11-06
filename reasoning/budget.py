"""The hard question from the video: close the 2027 budget under 14 constraints. Amounts are in US$ thousands.

The constraints pin down a single allocation (tests/test_budget.py proves it); it totals 3,840, the "$3.84M" on Ana's
post-it. Code checks every answer; the model's own claim that it is right is never trusted.
"""

from pydantic import BaseModel

DEPARTMENTS = ("engineering", "sales", "marketing", "operations", "hr", "finance", "legal")


class Allocation(BaseModel):
    engineering: int
    sales: int
    marketing: int
    operations: int
    hr: int
    finance: int
    legal: int


def _legal_rule(a):
    return a.legal == a.hr if a.marketing > 400 else a.legal == a.hr + 80


# (rule as the model reads it, check)
CONSTRAINTS = (
    ("The seven amounts add up to exactly 3,840.", lambda a: sum(_values(a)) == 3840),
    ("Every amount is a multiple of 40.", lambda a: all(v % 40 == 0 for v in _values(a))),
    ("Every department gets at least 200.", lambda a: min(_values(a)) >= 200),
    ("Engineering gets more than any other department.",
     lambda a: all(a.engineering > v for k, v in a.model_dump().items() if k != "engineering")),
    ("Engineering gets exactly Sales plus Marketing.", lambda a: a.engineering == a.sales + a.marketing),
    ("Sales gets 50% more than Marketing.", lambda a: 2 * a.sales == 3 * a.marketing),
    ("Operations gets half of Engineering.", lambda a: 2 * a.operations == a.engineering),
    ("Finance plus Legal equals Operations.", lambda a: a.finance + a.legal == a.operations),
    ("If Marketing gets more than 400, Legal gets the same as HR; otherwise Legal gets 80 more than HR.", _legal_rule),
    ("Finance gets 50% more than HR.", lambda a: 2 * a.finance == 3 * a.hr),
    ("HR, Legal and Finance together get less than Sales plus 200.",
     lambda a: a.hr + a.legal + a.finance < a.sales + 200),
    ("Marketing gets at least twice what HR gets.", lambda a: a.marketing >= 2 * a.hr),
    ("Sales gets more than Operations.", lambda a: a.sales > a.operations),
    ("No department gets more than a third of the total.", lambda a: 3 * max(_values(a)) <= 3840),
)

PROMPT = ("Close the 2027 budget with these 14 constraints. Split it across seven departments: "
          + ", ".join(DEPARTMENTS) + ". Amounts are whole numbers in US$ thousands.\n\n"
          + "\n".join(f"{i}. {text}" for i, (text, _) in enumerate(CONSTRAINTS, 1))
          + "\n\nReturn the amount for each department.")


def _values(a):
    return list(a.model_dump().values())


def broken(a: Allocation) -> list[int]:
    """Numbers (1-based) of the constraints this allocation breaks; empty means the budget closes."""
    return [i for i, (_, ok) in enumerate(CONSTRAINTS, 1) if not ok(a)]
