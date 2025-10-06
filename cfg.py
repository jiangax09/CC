import json
import sys

from ir import *

TERMS = ['jmp', 'br', 'ret']

# block_lable -> Block
block_map = {}

def successors(instr):
    op = instr['op']
    if op in ['jmp', 'br']:
        return instr['labels']
    elif op == 'ret':
        return []
    else:
        raise ValueError("{} is not a terminator".format(op))


def build_cfg(f):
    blocks = []
    block_id = 0
    curr_block = []
    label_block = {}
    for inst in f['instrs']:
        # build instruction
        label = inst.get('label')
        if label is not None:
            label_block[label] = block_id
        elif inst.get('op') is not None:
            op = inst['op']
            instr = None
            if op == "jmp":
                label = inst['labels'][0]
                instr = instr_jmp(label)
            elif op == 'br':
                tlabel = instr['labels'][0]
                flabel = instr['labels'][1]
                cond = Var(inst['args'][0])
                instr = instr_br(cond, tlabel, flabel)
            elif op == 'add' or op == 'mul' or op == 'div' or op == 'sub':
                opnd0 = Var(inst['args'][0])
                opnd1 = Var(inst['args'][1])
                instr = instr_arith(op, opnd0, opnd1)
            elif op == 'and' or op == 'or':
                opnd0 = Var(inst['args'][0])
                opnd1 = Var(inst['args'][1])
                instr = instr_lgoic(op, opnd0, opnd1)
            elif op == 'not':
                opnd0 = Var(inst['args'][0])
                instr = instr_lgoic(op, opnd0)
            elif op == 'eq' or op == 'ge' or op == 'gt' or op == 'lt' or op == 'le':
                opnd0 = Var(inst['args'][0])
                opnd1 = Var(inst['args'][1])
                instr = instr_cmp(op, opnd0, opnd1)

            curr_block.append(instr)

        if op in TERMS:
            block_map['bb.' + block_id] = curr_block
            blocks.append(curr_block)
            block_id += 1
            curr_block = []

    for bb in blocks:
        term = bb[-1]

    return func

def main():
    prog = json.load(sys.stdin)
    print(prog)
    funcs = []
    for func in prog['functions']:
        f = build_cfg(func)
        funcs.append(f)


if __name__ == '__main__':
    mycfg()
