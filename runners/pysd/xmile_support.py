# SPDX-FileCopyrightText: 2026 Raphael Ginster
# SPDX-FileCopyrightText: 2026 Matthias Papesch
# SPDX-FileCopyrightText: 2026 Vasiliy Seibert
# SPDX-License-Identifier: MIT
"""What it takes to run a Stella model (``.stmx``) with PySD as Stella does.

PySD reads XMILE, the format Stella saves in, but three things stand between
a Stella model and a run that agrees with Stella:

1. **Equations Stella writes and PySD's grammar rejects.** They are rewritten
   in a copy of the model, never in the file under ``models/``:

   ====================================  ===========================================
   Stella writes                         PySD reads
   ====================================  ===========================================
   ``a // b`` (safe division)            ``SAFEDIV(a, b)``, which PySD builds as zidz
   ``IF a THEN b ELSE IF c THEN d ...``  every conditional in brackets
   ``MOD``, ``if``, ``Then``             ``mod``, ``IF``, ``THEN``
   ``a*b {note}``                        ``a*b``
   ====================================  ===========================================

2. **Which RK2.** XMILE says ``method="RK2"`` and nothing more. Stella's RK2 is
   Heun's method: against Stella's own export of the Kaibab model it agrees to
   5e-12, the midpoint rule to no better than 3e-6.

3. **STEP is held for a whole DT.** Stella evaluates ``STEP`` once at the start
   of each time step and keeps the value through every Runge-Kutta stage. A
   plain Runge-Kutta re-evaluates it per stage, switches it on one stage early
   and follows the stage's trial state. In the predator-removal scenario that
   alone leaves the final deer population 22% off Stella's. Holding it closes
   the gap to 5e-12.

Adapted from pysdmdoc (https://github.com/rginster/pysdmdoc, MIT), where the
same comparison was made.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from xml.etree import ElementTree

XMILE_SUFFIXES = (".stmx", ".xmile", ".itmx", ".xml")

#: Suffixes PySD's own reader opens.  Anything else is handed over as .xmile.
PYSD_SUFFIXES = (".stmx", ".xmile", ".xml")


def is_xmile(path) -> bool:
    return Path(path).suffix.lower() in XMILE_SUFFIXES


# ---------------------------------------------------------------------------
# Equations

_TOKEN = re.compile(
    r"""
    (?P<space>\s+)
  | (?P<comment>\{[^}]*\})
  | (?P<quoted>"(?:\\.|[^"\\])*")
  | (?P<number>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)
  | (?P<name>[^\W\d][\w$'.]*)
  | (?P<op>//|<=|>=|<>|[-+*/^(),\[\]<>=:!&|])
    """,
    re.VERBOSE | re.UNICODE,
)

_KEYWORDS = {"if", "then", "else", "and", "or", "not", "mod"}
_CANONICAL_KEYWORDS = {"IF", "THEN", "ELSE", "mod"}
_NEEDS_REWRITE = re.compile(
    r"//|\b(?:else|then)\s+if\b|\b(?:if|then|else|mod)\b", re.IGNORECASE
)
_COMMENT = re.compile(r"\{[^{}]*\}")


def _tokens(text: str) -> list[str]:
    out, position = [], 0
    while position < len(text):
        match = _TOKEN.match(text, position)
        if match is None:
            out.append(text[position])
            position += 1
            continue
        position = match.end()
        if match.lastgroup not in ("space", "comment"):
            out.append(match.group())
    return out


class _Rewriter:
    """Recursive descent that re-emits an equation in PySD's dialect."""

    _BOUNDARIES = (",", "<", ">", "=", "<=", ">=", "<>", "&", "|", ":", "!")

    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.position = 0

    def peek(self):
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def peek_word(self) -> str:
        token = self.peek()
        return token.lower() if token else ""

    def take(self) -> str:
        token = self.tokens[self.position]
        self.position += 1
        return token

    def level(self, stops: tuple = ()) -> str:
        parts = []
        while self.peek() is not None and self.peek() not in (")", "]"):
            token = self.peek()
            word = token.lower()
            if word in stops or token in stops:
                break
            if word == "if":
                parts.append(self.conditional(stops))
            elif word in _KEYWORDS:
                self.take()
                parts.append(word if word == "mod" else word.upper())
            elif token in self._BOUNDARIES:
                parts.append(self.take())
            elif token in ("+", "-") and parts and parts[-1] not in (",", "(") \
                    and parts[-1].lower() not in _KEYWORDS:
                parts.append(self.take())
            else:
                parts.append(self.product())
        return " ".join(parts)

    def conditional(self, outer: tuple = ()) -> str:
        """``IF c THEN a ELSE b`` in brackets.  A dangling ELSE belongs to the
        innermost IF, because the else branch also stops at the outer stops."""
        self.take()
        ends = (")", "]", ",")
        condition = self.level(stops=("then",) + ends)
        if self.peek_word() != "then":
            return f"IF {condition}"
        self.take()
        then = self.level(stops=("else",) + ends)
        if self.peek_word() != "else":
            return f"IF {condition} THEN {then}"
        self.take()
        otherwise = self.level(stops=ends + tuple(outer))
        return f"(IF {condition} THEN {then} ELSE {otherwise})"

    def product(self) -> str:
        left = self.factor()
        while self.peek() in ("*", "/", "//"):
            operator = self.take()
            right = self.factor()
            left = (f"SAFEDIV({left}, {right})" if operator == "//"
                    else f"{left} {operator} {right}")
        return left

    def factor(self) -> str:
        signs = ""
        while self.peek() in ("+", "-"):
            signs += self.take()
        base = self.primary()
        while self.peek() == "^":
            self.take()
            exponent_signs = ""
            while self.peek() in ("+", "-"):
                exponent_signs += self.take()
            base = f"{base} ^ {exponent_signs}{self.primary()}"
        return f"{signs}{base}"

    def primary(self) -> str:
        token = self.peek()
        if token is None:
            return ""
        if token == "(":
            self.take()
            inner = self.level()
            if self.peek() == ")":
                self.take()
            return f"({inner})"
        if token.lower() == "if":
            return self.conditional()
        text = self.take()
        if self.peek() == "(" and (text[0].isalpha() or text[0] in "_\""
                                   or not text[0].isascii()):
            self.take()
            arguments = self.level()
            if self.peek() == ")":
                self.take()
            text = f"{text}({arguments})"
        if self.peek() == "[":
            self.take()
            subscripts = self.level()
            if self.peek() == "]":
                self.take()
            text = f"{text}[{subscripts}]"
        return text


def _needs_rewrite(equation: str) -> bool:
    if "//" in equation:
        return True
    for match in _NEEDS_REWRITE.finditer(equation):
        text = match.group(0)
        if any(c.isspace() for c in text) or text not in _CANONICAL_KEYWORDS:
            return True
    return False


def _strip_comments(equation: str) -> str:
    parts = re.split(r'("(?:\\.|[^"\\])*")', equation)
    return "".join(part if index % 2 else _COMMENT.sub(" ", part)
                   for index, part in enumerate(parts))


def rewrite_equation(equation: str) -> str:
    """An equation PySD can parse.  One that needs nothing is returned as is."""
    stripped = _strip_comments(equation)
    if not _needs_rewrite(stripped):
        return equation if stripped == equation else " ".join(stripped.split())
    parser = _Rewriter(_tokens(stripped))
    out = parser.level()
    while parser.peek() is not None:
        out += " " + parser.take() + " " + parser.level()
    return out


# ---------------------------------------------------------------------------
# The file

def _local(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def canonical(name: str) -> str:
    """One spelling for a Stella name: ``\\n``, ``_`` and runs of spaces fold."""
    name = str(name).strip().strip('"')
    name = name.replace("\\n", " ").replace("\n", " ").replace("_", " ")
    return " ".join(name.split()).lower()


def replace_tables(text: str, tables: dict) -> tuple[str, list[str]]:
    """Put new points into graphical functions, as Stella's import does.

    ``tables`` maps a variable name to ``(xs, ys)``.  PySD builds a Stella
    graphical function as a function of its input, and a table handed to
    ``run(params=...)`` would replace it by a time series indexed by *time*.
    So the points go into the model copy before it is translated.  Returns
    the new text and the names that were replaced.
    """
    if not tables:
        return text, []
    from lxml import etree

    wanted = {canonical(name): points for name, points in tables.items()}
    root = etree.fromstring(text.encode("utf-8"))
    replaced = []
    for element in root.iter():
        if _local(element.tag) not in ("aux", "flow") or not element.get("name"):
            continue
        points = wanted.get(canonical(element.get("name")))
        gf = next((c for c in element if _local(c.tag) == "gf"), None)
        if points is None or gf is None:
            continue
        xs, ys = points
        namespace = gf.tag[: -len("gf")]
        for child in list(gf):
            if _local(child.tag) in ("xscale", "xpts", "ypts"):
                gf.remove(child)
        xpts = etree.SubElement(gf, f"{namespace}xpts")
        xpts.text = ",".join(repr(float(x)) for x in xs)
        ypts = etree.SubElement(gf, f"{namespace}ypts")
        ypts.text = ",".join(repr(float(y)) for y in ys)
        replaced.append(" ".join(element.get("name").replace("\\n", " ").split()))
    text = etree.tostring(root, xml_declaration=True, encoding="utf-8").decode()
    return text, replaced


def prepare_text(path: Path, tables: dict | None = None) -> tuple[str, list[str]]:
    """The model as PySD can build it, and a note per change made."""
    text = Path(path).read_text(encoding="utf-8")
    notes: list[str] = []
    text, replaced = replace_tables(text, tables or {})
    notes += [f"graphical function {name}: points from the input" for name in replaced]

    def replace(match: re.Match) -> str:
        # The equation text is XML-escaped in the file.
        plain = html.unescape(match.group(2))
        rewritten = rewrite_equation(plain)
        if rewritten == plain:
            return match.group(0)
        notes.append(f"{' '.join(plain.split())}  ->  {rewritten}")
        escaped = (rewritten.replace("&", "&amp;").replace("<", "&lt;")
                   .replace(">", "&gt;"))
        return f"{match.group(1)}{escaped}{match.group(3)}"

    # (?<!/) keeps a self-closing <eqn/>, as in <model_units>, from opening a
    # match that would run on to the next variable's </eqn>.
    text = re.sub(r"(<eqn\b[^>]*(?<!/)>)(.*?)(</eqn>)", replace, text, flags=re.S)
    return text, notes


class ModelFacts:
    """What the runner needs to know about a Stella model before it runs it."""

    def __init__(self, path: Path):
        root = ElementTree.parse(str(path)).getroot()
        self.vendor = ""
        self.method = ""
        self.stocks: set[str] = set()
        #: Variables defined by a graphical function, by canonical name.
        self.graphical: set[str] = set()
        self.step_variables: list[str] = []
        self.names: dict[str, str] = {}
        for element in root.iter():
            tag = _local(element.tag)
            if tag == "vendor" and element.text:
                self.vendor = element.text.strip()
            elif tag == "sim_specs":
                self.method = element.get("method", "")
            elif tag in ("stock", "flow", "aux") and element.get("name"):
                eqn = next((c for c in element if _local(c.tag) == "eqn"), None)
                if eqn is None:
                    continue  # a diagram object, not the variable itself
                display = " ".join(
                    element.get("name").replace("\\n", " ").split()
                )
                self.names[canonical(display)] = display
                if tag == "stock":
                    self.stocks.add(canonical(display))
                if any(_local(c.tag) == "gf" for c in element):
                    self.graphical.add(canonical(display))
                if eqn.text and re.search(r"\bSTEP\s*\(", eqn.text, re.I):
                    self.step_variables.append(display)

    @property
    def is_stella(self) -> bool:
        return "isee" in self.vendor.lower()

    def integration_method(self) -> str | None:
        """The declared method as a name :mod:`rk_integrator` knows.

        XMILE lists fallbacks after a comma, e.g. ``"gear, rk4"``.  RK45 and
        Gear have RK4 as their fallback in the specification.
        """
        for candidate in (m.strip().lower() for m in self.method.split(",")):
            if candidate == "rk2":
                return "rk2-heun" if self.is_stella else "rk2-midpoint"
            if candidate in ("euler", "rk4"):
                return candidate
            if candidate in ("rk45", "gear"):
                return "rk4"
        return None
