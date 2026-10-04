# Agent — a tool-using loop from first principles

A ReAct-style agent: you give it a task, it plans, calls tools, observes
results, and repeats until done. Built with the raw OpenAI SDK — no agent
framework.

## Setup

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Put your OpenAI key in `.env`. The `ask_statement` tool reads your Project 3
vector store (expects a sibling `docchat` folder, default store `store-200`).

## Run

```bat
python agent.py
```

```
task> What is 15% of my total Amazon spending?
  [tool] ask_statement({"question": "Show all Amazon transactions."})
  [result] - Oct 02  AMAZON.CA MARKETPLACE TORONTO ON              $64.99 ...
  [tool] calculator({"expression": "(64.99 + 14.99 + 29.95) * 0.15"})
  [result] 16.4895

agent> 15% of your total Amazon spending ($109.93) is about $16.49.
    [steps: 3 | ~$0.0012]
```

## How it works

- `src/loop.py` — the harness. Sends messages + tool schemas, executes the
  model's tool calls with real Python functions, appends results, repeats.
  The model never acts; the loop does.
- `src/tools.py` — four tools: `calculator` (safe AST arithmetic),
  `ask_statement` (your Project 3 RAG pipeline), `read_file` / `write_file`
  (sandboxed to `./workspace_files/`).
- `src/llm.py` — chat completions with tool schemas + cost tracking.

## What I learned

_(fill in after Day 2)_
