"""Tool implementations and their OpenAI function schemas.

A tool is a Python function plus a JSON schema describing it. The model
never runs the function — it outputs a tool_call, and loop.py executes it.
Keep tools small, total, and honest about failures: return error strings,
don't raise, so the model can recover.
"""
import ast
import importlib
import importlib.util
import operator
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------- calculator

_ALLOWED_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.USub: operator.neg,
    ast.Mod: operator.mod,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.left),
                                           _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("only plain arithmetic (+ - * / ** %) is allowed")


def calculator(expression: str) -> str:
    """Evaluate a plain arithmetic expression, e.g. '3842.17 * 0.15'."""
    try:
        return str(_safe_eval(ast.parse(expression, mode="eval").body))
    except Exception as e:
        return f"Error: {e}"


# ------------------------------------------------------------- ask_statement
# Wraps the Project 3 RAG pipeline as a tool: the agent can question the
# ingested statement. Loaded lazily so the agent imports fine without it.

AGENT_DIR = Path(__file__).resolve().parent.parent
DOCCHAT_SRC = AGENT_DIR.parent / "docchat" / "src"
DOCCHAT_STORE = os.getenv("DOCCHAT_STORE",
                          str(AGENT_DIR.parent / "docchat" / "store-200"))

_docchat = None


def _load_docchat():
    global _docchat
    if _docchat is not None:
        return _docchat
    init = DOCCHAT_SRC / "__init__.py"
    if not init.exists():
        raise RuntimeError(
            f"docchat src not found at {DOCCHAT_SRC} "
            f"(expected a sibling 'docchat' folder; set DOCCHAT_STORE "
            f"and keep the folders side by side)")
    spec = importlib.util.spec_from_file_location(
        "docchat_src", init, submodule_search_locations=[str(DOCCHAT_SRC)])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["docchat_src"] = pkg
    spec.loader.exec_module(pkg)
    store = importlib.import_module("docchat_src.store")
    rag = importlib.import_module("docchat_src.rag")
    chunks, matrix = store.load(DOCCHAT_STORE)
    _docchat = (chunks, matrix, rag)
    return _docchat


def ask_statement(question: str) -> str:
    """Ask a question about the ingested bank statement."""
    try:
        chunks, matrix, rag = _load_docchat()
    except Exception as e:
        return f"Error: {e}"
    res = rag.answer(question, chunks, matrix, top_k=3, min_score=0.25,
                     hybrid=True)
    return res["answer"]


# ---------------------------------------------------------------- file tools
# Sandboxed to ./workspace_files so the agent can't wander the filesystem.

WORKSPACE = AGENT_DIR / "workspace_files"


def _safe_path(path: str) -> Path:
    p = (WORKSPACE / path).resolve()
    if WORKSPACE.resolve() not in p.parents and p != WORKSPACE.resolve():
        raise ValueError(f"path escapes workspace: {path}")
    return p


def read_file(path: str) -> str:
    """Read a text file from the agent workspace."""
    try:
        return _safe_path(path).read_text(encoding="utf-8")
    except Exception as e:
        return f"Error: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a text file in the agent workspace."""
    try:
        p = _safe_path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"Error: {e}"


# ------------------------------------------------------------------ registry

def _schema(name: str, description: str, props: dict, required: list) -> dict:
    return {"type": "function",
            "function": {"name": name, "description": description,
                         "parameters": {"type": "object",
                                        "properties": props,
                                        "required": required}}}


TOOLS = {
    "calculator": {
        "func": calculator,
        "schema": _schema(
            "calculator",
            "Evaluate a plain arithmetic expression. Use for any math; "
            "do not do arithmetic yourself.",
            {"expression": {"type": "string",
                            "description": "e.g. '3842.17 * 0.15'"}},
            ["expression"]),
    },
    "ask_statement": {
        "func": ask_statement,
        "schema": _schema(
            "ask_statement",
            "Ask a question about the user's ingested bank statement, which "
            "contains balances, merchant transactions (e.g. Amazon, groceries), "
            "interest charges, and fees. Use it for anything about spending or financials.",

            {"question": {"type": "string",
                          "description": "a focused question about the statement"}},
            ["question"]),
    },
    "read_file": {
        "func": read_file,
        "schema": _schema(
            "read_file",
            "Read a UTF-8 text file from the agent workspace.",
            {"path": {"type": "string",
                      "description": "relative path, e.g. 'notes.txt'"}},
            ["path"]),
    },
    "write_file": {
        "func": write_file,
        "schema": _schema(
            "write_file",
            "Write text to a file in the agent workspace.",
            {"path": {"type": "string", "description": "relative path"},
             "content": {"type": "string",
                         "description": "full file content"}},
            ["path", "content"]),
    },
}


def tool_schemas() -> list[dict]:
    return [t["schema"] for t in TOOLS.values()]


def execute(name: str, args: dict) -> str:
    """Run a tool by name. Unknown tools and bad args become error strings
    the model can recover from — never exceptions."""
    tool = TOOLS.get(name)
    if tool is None:
        return f"Error: unknown tool '{name}'. Available: {list(TOOLS)}"
    try:
        return str(tool["func"](**args))
    except TypeError as e:
        return f"Error: bad arguments for '{name}': {e}"
    except Exception as e:
        return f"Error: {e}"
