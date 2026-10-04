#!/usr/bin/env python3
"""Run the agent: give it a task, watch it plan, call tools, and answer.

Usage:
    python agent.py
"""
from src import loop


def main():
    print("Agent ready. Give it a task (empty line quits).\n")
    total_cost = 0.0
    while True:
        try:
            task = input("task> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not task:
            break
        result = loop.run(task)
        total_cost += result["cost_usd"]
        print(f"\nagent> {result['answer']}")
        print(f"    [steps: {result['steps']} | "
              f"~${result['cost_usd']:.4f}]")
        print()
    print(f"Session cost: ~${total_cost:.4f}")


if __name__ == "__main__":
    main()
