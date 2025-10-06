from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Union, Dict, Any, Tuple


# === Types ===
class Type(Enum):
    INT = "int"
    BOOL = "bool"

    def __str__(self) -> str:
        return self.value


# === Operands ===
@dataclass(frozen=True)
class Var:
    name: str

    def to_json(self):
        return {"var": self.name}

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Imm:
    # Immediate literal: integer or boolean
    value: Union[int, bool]

    def to_json(self):
        return {"imm": self.value}

    def __str__(self) -> str:
        return str(self.value).lower() if isinstance(self.value, bool) else str(self.value)


Operand = Union[Var, Imm]


# === Instructions ===
@dataclass
class Instr:
    op: str
    args: List[Operand] = field(default_factory=list)
    dest: Optional[str] = None  # name of destination variable (if value-producing)
    labels: List[str] = field(default_factory=list)  # for jmp/br
    func: Optional[str] = None  # for call
    # Additional metadata may be added if needed (e.g. types)

    def to_json(self) -> Dict[str, Any]:
        j: Dict[str, Any] = {"op": self.op}
        if self.dest is not None:
            j["dest"] = self.dest
        if self.func is not None:
            j["func"] = self.func
        if self.args:
            j["args"] = [a.to_json() if isinstance(a, (Var, Imm)) else a for a in self.args]
        if self.labels:
            j["labels"] = self.labels
        return j

    def __str__(self) -> str:
        parts: List[str] = []
        if self.dest:
            parts.append(f"{self.dest} =")
        parts.append(self.op)
        if self.func:
            parts.append(self.func)
        if self.args:
            parts.append(" ".join(str(a) for a in self.args))
        if self.labels:
            parts.append(" ".join(self.labels))
        return " ".join(parts)


# Convenience constructors for common ops
def instr_arith(op: str, dest: str, a: Operand, b: Operand) -> Instr:
    return Instr(op=op, args=[a, b], dest=dest)


def instr_cmp(op: str, dest: str, a: Operand, b: Operand) -> Instr:
    return Instr(op=op, args=[a, b], dest=dest)


def instr_logic(op: str, dest: Optional[str], *args: Operand) -> Instr:
    return Instr(op=op, args=list(args), dest=dest)


def instr_not(dest: str, a: Operand) -> Instr:
    return Instr(op="not", args=[a], dest=dest)


def instr_jmp(label: str) -> Instr:
    return Instr(op="jmp", labels=[label])


def instr_br(cond: Operand, tlabel: str, flabel: str) -> Instr:
    return Instr(op="br", args=[cond], labels=[tlabel, flabel])


def instr_call(dest: Optional[str], func_name: str, args: List[Operand]) -> Instr:
    return Instr(op="call", func=func_name, args=args, dest=dest)


def instr_ret(val: Optional[Operand] = None) -> Instr:
    return Instr(op="ret", args=[val] if val is not None else [])


# === Basic block / Label ===
@dataclass
class Block:
    label: str
    instrs: List[Instr] = field(default_factory=list)
    succs: List[Block] = field(default_factory=List)

    def to_json(self):
        return {"label": self.label, "instrs": [i.to_json() for i in self.instrs]}

    def __str__(self) -> str:
        lines = [f"{self.label}:"]
        for i in self.instrs:
            lines.append(f"  {i}")
        return "\n".join(lines)


# === Function ===
@dataclass
class Function:
    name: str
    params: List[Tuple[str, Type]]  # list of (param_name, type)
    ret: Optional[Type]  # None for void
    blocks: List[Block] = field(default_factory=list)
    # Optionally: locals / types map can be inferred by validator

    def to_json(self):
        return {
            "name": self.name,
            "params": [{"name": n, "type": str(t)} for n, t in self.params],
            "ret": str(self.ret) if self.ret else None,
            "blocks": [b.to_json() for b in self.blocks],
        }

    def find_block(self, label: str) -> Optional[Block]:
        for b in self.blocks:
            if b.label == label:
                return b
        return None

    def __str__(self) -> str:
        header = f"func {self.name}({', '.join(f'{n}:{t}' for n, t in self.params)}) -> {self.ret if self.ret else 'void'}"
        body = "\n".join(str(b) for b in self.blocks)
        return header + "\n" + body


# === Program ===
@dataclass
class Program:
    functions: Dict[str, Function] = field(default_factory=dict)

    def add_function(self, f: Function):
        if f.name in self.functions:
            raise KeyError(f"function {f.name} already defined")
        self.functions[f.name] = f

    def to_json(self):
        return {"functions": [f.to_json() for f in self.functions.values()]}

    def __str__(self) -> str:
        return "\n\n".join(str(f) for f in self.functions.values())
