from cfg import *
from ir import *

def local(bb):
    symb2vn = {}
    symb2versions = {}
    vns = []
    newBB = []
    for inst in bb.instrs:
        dest = inst.dest
        if dest == None:
            newBB.append(dest)
        else:
            inst.op == 'const'
            key = inst.op
            opnd0 = inst.args[0]
            version = symb2versions.get(opnd, 0)
            opnd0 += str(version)
            opnd0 += opnd0 + str(version)
            vn0 = symb2vn[opnd0]
            if len(inst.args) > 1:
                opnd1 = inst.args[1]
                version1 = symb2versions.get(opnd, 0)
                opnd1 += str(version1)
                vn1 = symb2vn[opnd1]
            else:
                vn1 = None
            key += opnd0 + opnd1
            if key in symb2vn.keys:
                vn = sym

            # update symbol version since current one is killed
            symb2versions[dest] = symb2versions(dest, 0) + 1


    return newBB

def main():
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        f = build_function(func)
        newF = Function(f.name, f.params, None, [])
        newBlocks = newF.blocks
        for block in f.blocks:
            newBB = local(block)
            newBlocks.append(newBB)

if __name__ == '__main__':
    main()
