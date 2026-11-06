"""Command line for compare.py: arguments and readable API errors."""

import argparse
from contextlib import contextmanager

import openai

EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh", "max")


def _positive_int(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected a whole number, got {text!r}")
    if value < 1:
        raise argparse.ArgumentTypeError("must be 1 or more")
    return value


def _efforts(text):
    values = [v.strip() for v in text.split(",") if v.strip()]
    bad = [v for v in values if v not in EFFORTS]
    if bad or not values:
        raise argparse.ArgumentTypeError(f"unknown effort {bad or text!r}; use any of {', '.join(EFFORTS)}")
    return values


def parse_args():
    p = argparse.ArgumentParser(description="Same question, different reasoning effort: correctness, reasoning "
                                            "tokens and latency.")
    p.add_argument("question", choices=("easy", "hard"), help="easy: what's 2 plus 3; hard: the 14-constraint budget")
    p.add_argument("--effort", type=_efforts, default=["none", "low", "medium", "high"],
                   help="comma-separated reasoning efforts (default: none,low,medium,high)")
    p.add_argument("--runs", type=_positive_int, default=3, help="runs per effort (default: 3)")
    p.add_argument("--summary", action="store_true",
                   help="print the reasoning summary of the last run: the API returns a summary, not the reasoning")
    return p.parse_args()


@contextmanager
def api_errors():
    """Turns the usual OpenAI failures into one-line messages instead of tracebacks."""
    try:
        yield
    except openai.AuthenticationError:
        raise SystemExit("OpenAI rejected the key. Check OPENAI_API_KEY in .env.")
    except openai.PermissionDeniedError as e:
        raise SystemExit(f"This key can't use the model: {e.message}")
    except openai.NotFoundError as e:
        raise SystemExit(f"{e.message}\nSet another model with OPENAI_MODEL in .env.")
    except openai.BadRequestError as e:
        raise SystemExit(f"{e.message}\nNot every model accepts every effort; try a shorter --effort list.")
    except openai.RateLimitError:
        raise SystemExit("Rate limit or no credit on the OpenAI account. Check billing or try again in a minute.")
    except openai.APIConnectionError:
        raise SystemExit("Could not reach the OpenAI API. Check your internet connection.")
