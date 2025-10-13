import json
import sys
import copy

from ir import *

TERMS = ['jmp', 'br', 'ret']

# block_label -> Block
block_map = {}

def successors(instr):
    op = instr['op']
    if op in ['jmp', 'br']:
        return instr['labels']
    elif op == 'ret':
        return []
    else:
        raise ValueError("{} is not a terminator".format(op))

def get_symbol(symbol_table, symbol_name):
    if symbol_name not in symbol_table:
        raise ValueError(f"undefind {symbol_name}")
    return symbol_table[symbol_name]

def create_symbol(symbol_table, symbol_name, symbol_type, def_instr=None):
    symbol_table[symbol_name] = Var(symbol_name, symbol_type, def_instr)

def create_block(block_map, label):
    block = Block(label, [], [])
    block_map[label] = block
    return block

def add_fallthrough(func):
    for idx, bb in enumerate(func.blocks):
        instrs = bb.instrs
        if idx < len(func.blocks) -1 and (len(instrs) == 0 or instrs[-1] not in ['br', 'jmp', 'ret']):
            label = func.blocks[idx + 1].label
            instrs.append(instr_jmp(label))

def add_succs(func, label_block):
    blocks = func.blocks
    for bb in blocks:
        assert len(bb.instrs) > 0, f"block {bb.label} is empty!!"

        term = bb.instrs[-1]
        # print(f"term = {term}")
        if term.op in ['br', 'jmp']:
            for label in term.labels:
                next = label_block[label]
                bb.succs.append(next)


def build_function(f):
    func = Function(f['name'], [], None, [])
    blocks = func.blocks

    label_block = {}
    blocks.append(create_block(label_block, 'entry'))
    curr_block = blocks[-1]

    symbol_table = {}
    arg_pairs = f.get('args', [])
    params = func.params
    for arg_pair in arg_pairs:
        ty = Type.INT if arg_pair['type'] == 'int' else Type.BOOL
        arg_name = arg_pair['name']
        create_symbol(symbol_table, arg_name, ty)
        params.append((arg_name, ty))

    for inst in f['instrs']:
        label = inst.get('label')
        if label is not None:
            block = create_block(block_map, label)
            blocks.append(block)
            curr_block = blocks[-1]
            label_block[label] = curr_block

        elif inst.get('op') is not None:
            op = inst['op']
            instr = None
            if op == 'const':
                ty = Type.INT if inst['type'] == 'int' else Type.BOOL
                if ty == Type.INT:
                    val = inst['value']
                elif inst['type'].lower == 'false':
                    val = False
                else:
                    val = True
                imm = Imm(val, ty)
                instr = instr_const(inst['dest'], imm)
                dest_var = create_symbol(symbol_table, inst['dest'], ty, instr)
                instr.args.insert(0, dest_var)

            if op in ['print', 'call']:
                call_args = []
                if op != 'print':
                    op = inst['funcs'][0]
                for arg_name in inst['args']:
                    call_args.append(get_symbol(symbol_table, arg_name))
                instr = instr_call(None, op, call_args)
                dest_name = inst['dest'] if inst.get('dest') is not None else 'void'
                if inst.get('type') is None:
                    dest_type = Type.INT
                else:
                    dest_type = Type.INT if inst['type'] == 'int' else Type.BOOL
                dest_var = create_symbol(symbol_table, dest_name, dest_type, instr)
                instr.args.insert(0, dest_var)

            if op == 'id':
                # print(f"inst = {inst}")
                src = get_symbol(symbol_table, inst['args'][0])
                dest_name = inst['dest']
                instr = instr_id(dest_name, src)
                dest_var = create_symbol(symbol_table, dest_name, src.elem_type, instr)
                instr.args.insert(0, dest_var)

            if op == "jmp":
                label = inst['labels'][0]
                instr = instr_jmp(label)
            elif op == "ret":
                ret_names = inst.get('args')
                if ret_names is not None:
                    ret_name = ret_names[0]
                    ret_val = get_symbol(symbol_table, ret_name)

                instr = instr_ret(ret_val)
            elif op == 'br':
                tlabel = inst['labels'][0]
                flabel = inst['labels'][1]
                cond = get_symbol(symbol_table, inst['args'][0])
                print(f"cond = {cond}")
                instr = instr_br(cond, tlabel, flabel)
            elif op in ['add', 'mul', 'div', 'sub']:
                opnd0 = get_symbol(symbol_table, inst['args'][0])
                opnd1 = get_symbol(symbol_table, inst['args'][1])

                instr = instr_arith(op, inst['dest'], opnd0, opnd1)
                dest_var = create_symbol(symbol_table, inst['dest'], opnd0.elem_type, instr)
                instr.args.insert(0, dest_var)
            elif op == 'and' or op == 'or':
                opnd0 = get_symbol(symbol_table, inst['args'][0])
                opnd1 = get_symbol(symbol_table, inst['args'][1])
                instr = instr_lgoic(op, inst['dest'], opnd0, opnd1)
                dest_var = create_symbol(symbol_table, inst['dest'], opnd0.elem_type, instr)
                instr.args.insert(0, dest_var)
            elif op == 'not':
                opnd0 = get_symbol(symbol_table, inst['args'][0])
                instr = instr_lgoic(inst['dest'], opnd0)
                dest_var = create_symbol(symbol_table, inst['dest'], opnd0.elem_type, instr)
                instr.args.insert(0, dest_var)
            elif op in ['eq', 'ge', 'gt', 'lt', 'le']:
                opnd0 = get_symbol(symbol_table, inst['args'][0])
                opnd1 = get_symbol(symbol_table, inst['args'][1])
                instr = instr_cmp(op, inst['dest'], opnd0, opnd1)
                dest_var = create_symbol(symbol_table, inst['dest'], opnd0.elem_type, instr)
                instr.args.insert(0, dest_var)

            curr_block.append(instr)

    for key in symbol_table.keys():
        print(f"{key, symbol_table[key]}")

    last_bb = blocks[-1]
    if len(last_bb.instrs) == 0 or last_bb.instrs[-1].op != 'ret':
        last_bb.instrs.append(instr_ret())

    # add fall-through
    add_fallthrough(func)
    print(f"func = {func}")

    add_succs(func, label_block)
    return func

def main():
    prog = json.load(sys.stdin)
    print(prog)
    funcs = []
    for func in prog['functions']:
        f = build_function(func)
        funcs.append(f)


if __name__ == '__main__':
    main()
