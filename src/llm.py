"""LLM wrapper with tool-calling support."""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "gpt-4o-mini"

# gpt-4o-mini pricing ($ per 1M tokens)
IN_PER_1M = 0.15
OUT_PER_1M = 0.60

_client_instance = None


def _client():
    """Lazy client: importing this module never needs a key; only calls do."""
    global _client_instance
    if _client_instance is None:
        _client_instance = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client_instance



def chat(messages: list, tools: list | None = None,
         temperature: float = 0.2) -> tuple:
    """One chat completion; optionally with tool schemas.

    Returns (message, cost_usd). The message may carry .tool_calls.
    """
    kwargs = {"model": MODEL, "messages": messages, "temperature": temperature}
    if tools:
        kwargs["tools"] = tools
    resp = _client().chat.completions.create(**kwargs)
    msg = resp.choices[0].message
    u = resp.usage
    cost = (u.prompt_tokens / 1e6) * IN_PER_1M + \
           (u.completion_tokens / 1e6) * OUT_PER_1M
    return msg, cost
