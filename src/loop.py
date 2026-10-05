"""The agent harness: the loop that makes an LLM an agent.

The core insight: the model never acts. Each turn it outputs either a
final answer or tool calls (JSON). This loop executes the calls with
real Python functions and feeds the results back as messages. The
"agent" is the loop — the model is the planner inside it.

Message flow per step:
  user task -> assistant(tool_calls) -> tool results -> assistant ... 
  until the assistant answers without tool calls, or max_steps hits.
"""
import json

from . import llm, tools

SYSTEM = """You are a careful assistant that solves tasks using tools.
Rules:
- Use tools when you need facts, arithmetic, or files. Never guess a
  number you could compute or a fact you could look up.
- Never ask the user for information a tool could provide. You have
  tools — retrieve it yourself instead of asking.
- After each tool result, decide the next step. Chain tools when a task
  needs more than one.
- If a tool returns an error, read it and try a corrected call.
- When finished, answer directly with the result. Keep it short."""



def run(task: str, max_steps: int = 8, verbose: bool = True) -> dict:
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": task}]
    total_cost = 0.0
    tools_used = []

    for step in range(max_steps):
        msg, cost = llm.chat(messages, tools=tools.tool_schemas())
        total_cost += cost
        messages.append(msg)  # the SDK message serializes back into history

        if not msg.tool_calls:
            return {"answer": msg.content, "cost_usd": total_cost,
                    "steps": step + 1, "finished": True, "tools_used": tools_used}

        for call in msg.tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
                result = f"Error: unparseable arguments for '{name}'"
            else:
                result = tools.execute(name, args)
                tools_used.append(name)
            if verbose:
                print(f"  [tool] {name}({call.function.arguments})")
                print(f"  [result] {str(result)[:220]}")
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": str(result)})

    return {"answer": "Stopped: max steps reached without a final answer.",
            "cost_usd": total_cost, "steps": max_steps, "finished": False, "tools_used": tools_used}
