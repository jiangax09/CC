import json

def constant_fold(bril_program):
    for func in bril_program["functions"]:
        env = {}  # map var -> const value
        new_instrs = []
        for instr in func["instrs"]:
            if instr["op"] == "const":
                env[instr["dest"]] = instr["value"]
                new_instrs.append(instr)
            elif instr["op"] == "add":
                a, b = instr["args"]
                if a in env and b in env:

                    # Fold at compile time
                    new_instrs.append({
                        "op": "const",
                        "type": "int",
                        "dest": instr["dest"],
                        "value": env[a] + env[b]
                    })
                    env[instr["dest"]] = env[a] + env[b]
                else:
                    new_instrs.append(instr)
            else:
                new_instrs.append(instr)
        func["instrs"] = new_instrs
    return bril_program


program = json.loads(open("input.bril").read())
optimized = constant_fold(program)
print(json.dumps(optimized, indent=2))
