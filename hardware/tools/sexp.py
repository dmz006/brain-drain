"""Minimal S-expression reader/writer for KiCad files."""

from __future__ import annotations

import re
import uuid as _uuid

_TOKEN = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))', re.S)


def parse(text: str):
    """Parse one or more S-expressions into nested Python lists (strings kept quoted-aware)."""
    stack = [[]]
    pos = 0
    n = len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            done = stack.pop()
            stack[-1].append(done)
        elif m.group(3):
            stack[-1].append(Str(m.group(3)[1:-1].replace('\\"', '"')))
        elif m.group(4):
            stack[-1].append(m.group(4))
    return stack[0]


class Str(str):
    """A string that must be emitted quoted."""


def q(s: str) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def emit(node, indent: int = 0) -> str:
    """Pretty-print a nested list back to KiCad-style text."""
    pad = "\t" * indent
    if isinstance(node, Str):
        return q(node)
    if not isinstance(node, list):
        return str(node)
    if not node:
        return "()"
    head = node[0]
    simple = all(not isinstance(c, list) for c in node)
    if simple:
        return "(" + " ".join(emit(c) for c in node) + ")"
    out = "(" + emit(head)
    inline = []
    i = 1
    while i < len(node) and not isinstance(node[i], list):
        inline.append(emit(node[i]))
        i += 1
    if inline:
        out += " " + " ".join(inline)
    for c in node[i:]:
        out += "\n" + pad + "\t" + emit(c, indent + 1)
    out += "\n" + pad + ")"
    return out


def find(node, tag):
    for c in node:
        if isinstance(c, list) and c and c[0] == tag:
            return c
    return None


def find_all(node, tag):
    return [c for c in node if isinstance(c, list) and c and c[0] == tag]


def new_uuid() -> str:
    return str(_uuid.uuid4())


def fmt(x: float) -> str:
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"
