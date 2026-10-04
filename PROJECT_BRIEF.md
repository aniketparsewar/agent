# Project 4 Brief — Agent (tool-using loop)

## Goal
Build a ReAct-style agent from first principles: an LLM that plans, tools
it can call, and the harness loop that connects them. The model proposes;
your code disposes.

## Why this matters
Agents are the current frontier of applied AI engineering. After this
project you can explain what actually makes something "an agent": not a
smarter model, but a loop that lets the model call tools, see results,
and decide the next step. Everything so far (prompting, evals, RAG) plugs
in — your Project 3 pipeline is one of this agent's tools.

## Scope (keep it small)
- Local CLI + REPL. Four tools: calculator, ask_statement (your RAG
  pipeline), read_file, write_file (sandboxed to ./workspace_files).
- One task at a time. No memory between tasks. Max 8 steps per task.

## Weekend task list

### Day 1 — Make it run
- [ ] Setup: venv, requirements, `.env` (same key as before)
- [ ] `python agent.py` — try the three demo tasks below, watch the trace
- [ ] Read `src/loop.py` and `src/tools.py` until you can explain: who
      executes the tools? What does the model actually output? Where does
      the "thinking" happen?
- [ ] Exercises: add a 5th tool of your own; then deliberately break a
      tool description and watch the agent misuse it

### Day 2 — Make it yours
- [ ] Eval: write 6 golden tasks with expected tool sequences, point your
      prompt-lab harness at `loop.run`, measure tool-selection accuracy
- [ ] Harder tasks: multi-step, error recovery (ask about a missing file),
      a task designed to hit max_steps
- [ ] `git init`, commit, push to GitHub. Fill in README's "What I learned."

## Demo tasks (Day 1)
1. `What is 15% of my total Amazon spending?`
   Needs ask_statement (list the transactions) + calculator. Two tools,
   one task — the whole point of the project.
2. `What was my new balance? Write it to balance.txt`
   ask_statement + write_file. Then `read_file` to verify: `Read balance.txt`
3. `What is 3842.17 * 0.15?`
   Should use the calculator, not mental math. Watch whether it does.

## Done means
- [ ] Multi-step tasks solve via 2+ tools; the trace shows plan -> act -> observe
- [ ] You can explain the agent loop cold: model outputs JSON, code executes
- [ ] Prompt-lab scores for tool selection (measured, not vibes)
- [ ] Repo public on GitHub

## Stretch
- Web search tool (your browser.search via a small wrapper)
- Cost/step guards per task; per-tool timeouts
- Two agents: a planner and a worker passing messages

## Concepts this teaches (for interviews later)
"What's an agent?" → an LLM inside a tool-calling loop: the model plans
the next step, code executes tools, results feed back in. "Why do models
need tools?" → they're bad at arithmetic, can't see your files, and
can't fetch fresh facts — tools cover exactly those gaps. "What breaks?"
→ bad tool descriptions (the model can't use what it can't understand),
error cascades, runaway loops (hence max_steps), and cost per task.
