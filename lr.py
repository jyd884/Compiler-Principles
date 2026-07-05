import sys
from collections import defaultdict, deque


def format_item(item):
    left, right, dot = item
    dotted = right[:dot] + "." + right[dot:]
    return f"{left} -> {dotted}"


def print_dfa(states, transitions):
    print("LR(0) DFA states:")
    for index, state in enumerate(states):
        print(f"I{index}:")
        for item in sorted(state):
            print(f"  {format_item(item)}")

    print("LR(0) DFA transitions:")
    for (state_idx, symbol), next_state in sorted(transitions.items()):
        print(f"  I{state_idx} --{symbol}--> I{next_state}")


def print_analysis_tables(states, action, goto_tbl, grammar):
    terminals = sorted(grammar.Vt | {"$"})
    nonterminals = sorted(x for x in grammar.Vn if x != "S'")

    print("SLR(1) ACTION table:")
    print("State\t" + "\t".join(terminals))
    for state_idx in range(len(states)):
        row = [f"I{state_idx}"]
        for symbol in terminals:
            row.append(action.get((state_idx, symbol), ""))
        print("\t".join(row))

    print("SLR(1) GOTO table:")
    print("State\t" + "\t".join(nonterminals))
    for state_idx in range(len(states)):
        row = [f"I{state_idx}"]
        for symbol in nonterminals:
            value = goto_tbl.get((state_idx, symbol), "")
            row.append("" if value == "" else str(value))
        print("\t".join(row))


def print_parse_trace(grammar, productions, trace, accepted, error_message=None):
    print("LR parse trace:")
    print("Step\tState stack\tSymbol stack\tInput\tAction")
    for entry in trace:
        print(
            f"{entry['step']}\t{entry['states']}\t{entry['symbols']}\t"
            f"{entry['input']}\t{entry['action']}"
        )

    if accepted:
        print("Parse result: accepted")
        print("Applied productions:")
        for prod_idx in productions:
            left, right = grammar.prods[prod_idx]
            print(f"  r{prod_idx}: {left} -> {right}")
    else:
        print("Parse result: rejected")
        if error_message:
            print("Reason:", error_message)

class Grammar:
    def __init__(self, file_path):
        self.start = None
        self.prods = [] # list of (LHS, RHS)
        self.Vn = set()
        self.Vt = set()
        self.target = ""
        self.parse_file(file_path)
        
    def parse_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = [l.strip() for l in f if l.strip()]
        if not lines: return
        if '(' not in lines[-1]:
            self.target = lines[-1]
            lines = lines[:-1]
        for idx, line in enumerate(lines):
            left, right = line.split('(', 1)
            right = right.rstrip(')')
            if idx == 0:
                self.start = left
            self.prods.append((left, right))
            self.Vn.add(left)
            for c in right:
                if c.isupper() or c in ["S'"]:
                    self.Vn.add(c)
                else:
                    self.Vt.add(c)
        if self.start:
            self.Vn.add("S'")
            self.prods.insert(0, ("S'", self.start))

class LR0:
    def __init__(self, grammar):
        self.g = grammar
        self.items = [] # list of (LHS, RHS, dot_pos)
        self.prods_idx = {}
        for i, (l, r) in enumerate(self.g.prods):
            self.prods_idx[(l, r)] = i
            for dot in range(len(r) + 1):
                self.items.append((l, r, dot))
                
    def closure(self, I):
        J = set(I)
        changed = True
        while changed:
            changed = False
            for (l, r, dot) in list(J):
                if dot < len(r) and r[dot] in self.g.Vn:
                    B = r[dot]
                    for (pl, pr) in self.g.prods:
                        if pl == B:
                            item = (pl, pr, 0)
                            if item not in J:
                                J.add(item)
                                changed = True
        return frozenset(J)

    def goto(self, I, X):
        J = set()
        for (l, r, dot) in I:
            if dot < len(r) and r[dot] == X:
                J.add((l, r, dot + 1))
        return self.closure(J)

    def build_dfa(self):
        init_item = ("S'", self.g.start, 0)
        I0 = self.closure({init_item})
        self.C = [I0]
        self.transitions = {} # (state_idx, symbol) -> state_idx
        
        queue = deque([0])
        while queue:
            i = queue.popleft()
            I = self.C[i]
            symbols = set()
            for (l, r, dot) in I:
                if dot < len(r):
                    symbols.add(r[dot])
            for X in symbols:
                next_I = self.goto(I, X)
                if not next_I: continue
                if next_I not in self.C:
                    self.C.append(next_I)
                    queue.append(len(self.C)-1)
                j = self.C.index(next_I)
                self.transitions[(i, X)] = j

    def first(self, symbol):
        pass # Simplified for SLR(1)
        
    def build_slr1_table(self):
        # compute first and follow
        first = {x: set() for x in self.g.Vn | self.g.Vt}
        for x in self.g.Vt: first[x].add(x)
        changed = True
        while changed:
            changed = False
            for l, r in self.g.prods:
                if r:
                    before = len(first[l])
                    first[l] |= first[r[0]]
                    if len(first[l]) > before: changed = True

        follow = {x: set() for x in self.g.Vn}
        follow["S'"].add("$")
        changed = True
        while changed:
            changed = False
            for l, r in self.g.prods:
                for i, B in enumerate(r):
                    if B in self.g.Vn:
                        before = len(follow[B])
                        if i + 1 < len(r):
                            follow[B] |= (first[r[i+1]] - {''})
                        else:
                            follow[B] |= follow[l]
                        if len(follow[B]) > before: changed = True

        action = {}
        goto_tbl = {}
        for i, I in enumerate(self.C):
            for (l, r, dot) in I:
                if dot == len(r):
                    if l == "S'":
                        action[(i, "$")] = "acc"
                    else:
                        for a in follow[l]:
                            if (i, a) not in action:
                                action[(i, a)] = f"r{self.prods_idx[(l, r)]}"
                else:
                    a = r[dot]
                    if a in self.g.Vt:
                        if (i, a) in self.transitions:
                            action[(i, a)] = f"s{self.transitions[(i, a)]}"
            for A in self.g.Vn:
                if (i, A) in self.transitions:
                    goto_tbl[(i, A)] = self.transitions[(i, A)]
                    
        return action, goto_tbl, follow

    def parse(self, action, goto_tbl, target):
        input_symbols = list(target) + ["$"]
        state_stack = [0]
        symbol_stack = ["$"]
        input_index = 0
        trace = []
        applied_productions = []
        step = 0

        while True:
            current_state = state_stack[-1]
            current_symbol = input_symbols[input_index]
            table_action = action.get((current_state, current_symbol))

            trace.append({
                "step": step,
                "states": " ".join(map(str, state_stack)),
                "symbols": " ".join(symbol_stack),
                "input": "".join(input_symbols[input_index:]),
                "action": table_action or "error",
            })

            if table_action is None:
                return trace, applied_productions, False, (
                    f"No ACTION entry for state {current_state} and symbol {current_symbol}"
                )

            if table_action == "acc":
                return trace, applied_productions, True, None

            if table_action.startswith("s"):
                next_state = int(table_action[1:])
                symbol_stack.append(current_symbol)
                state_stack.append(next_state)
                input_index += 1
            elif table_action.startswith("r"):
                prod_idx = int(table_action[1:])
                left, right = self.g.prods[prod_idx]
                for _ in right:
                    symbol_stack.pop()
                    state_stack.pop()

                goto_state = goto_tbl.get((state_stack[-1], left))
                if goto_state is None:
                    return trace, applied_productions, False, (
                        f"No GOTO entry for state {state_stack[-1]} and symbol {left}"
                    )

                symbol_stack.append(left)
                state_stack.append(goto_state)
                applied_productions.append(prod_idx)
                trace[-1]["action"] = f"{table_action} ({left} -> {right})"
            else:
                return trace, applied_productions, False, (
                    f"Unknown action {table_action}"
                )

            step += 1

if __name__ == "__main__":
    g = Grammar("g.in")
    lr0 = LR0(g)
    init_closure = lr0.closure({("S'", g.start, 0)})
    lr0.build_dfa()
    action, goto_tbl, follow = lr0.build_slr1_table()
    trace, productions, accepted, error_message = lr0.parse(action, goto_tbl, g.target)
    print("LR(0) initial closure I0:")
    for item in sorted(init_closure):
        print(format_item(item))
    print_dfa(lr0.C, lr0.transitions)
    print_analysis_tables(lr0.C, action, goto_tbl, g)
    print_parse_trace(g, productions, trace, accepted, error_message)
    print("DFA states:", len(lr0.C))
    print("Action table size:", len(action))
