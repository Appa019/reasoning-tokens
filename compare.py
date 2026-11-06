"""Asks the same question at several reasoning efforts and checks each answer in code.

Run: python compare.py easy|hard [--effort none,low,high] [--runs 3] [--summary]
"""

import time

from openai import OpenAI

from reasoning.budget import PROMPT, Allocation, broken
from reasoning.cli import api_errors, parse_args
from reasoning.config import load_env, model

EASY = "What's 2 plus 3? Reply with the number only."


def ask(client, model_name, question, effort, summary):
    """One call. Returns (correct, reasoning tokens, output tokens, seconds, reasoning summary text)."""
    reasoning = {"effort": effort, **({"summary": "auto"} if summary else {})}
    t0 = time.perf_counter()
    if question == "easy":
        r = client.responses.create(model=model_name, input=EASY, reasoning=reasoning)
        correct = r.output_text.strip().rstrip(".") == "5"
    else:
        r = client.responses.parse(model=model_name, input=PROMPT, reasoning=reasoning, text_format=Allocation)
        correct = r.output_parsed is not None and not broken(r.output_parsed)
    seconds = time.perf_counter() - t0
    summary_text = "\n".join(s.text for item in r.output if item.type == "reasoning" for s in item.summary)
    u = r.usage
    return correct, u.output_tokens_details.reasoning_tokens, u.output_tokens, seconds, summary_text


def main():
    args = parse_args()
    load_env()
    client, model_name = OpenAI(), model()
    print(f"{args.question} question, {model_name}, {args.runs} runs per effort\n")
    print(f"{'effort':<9}{'correct':>9}{'reasoning tok':>15}{'output tok':>12}{'seconds':>9}")
    summary_text = ""
    with api_errors():
        for effort in args.effort:
            runs = [ask(client, model_name, args.question, effort, args.summary) for _ in range(args.runs)]
            ok = sum(r[0] for r in runs)
            avg = [sum(r[i] for r in runs) / len(runs) for i in (1, 2, 3)]
            print(f"{effort:<9}{f'{ok}/{len(runs)}':>9}{avg[0]:>15.0f}{avg[1]:>12.0f}{avg[2]:>9.1f}", flush=True)
            summary_text = runs[-1][4] or summary_text
    print("\nReasoning tokens are billed as output tokens, and you never see them: only their count.")
    if args.summary:
        print("\nReasoning summary of the last run (a summary written for you, not the reasoning itself):\n")
        print(summary_text or "(the model returned no summary)")


if __name__ == "__main__":
    main()
