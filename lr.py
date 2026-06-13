import sys
from collections import defaultdict, deque

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

if __name__ == "__main__":
    g = Grammar("g.in")
    lr0 = LR0(g)
    lr0.build_dfa()
    action, goto_tbl, follow = lr0.build_slr1_table()
    print("DFA states:", len(lr0.C))
    print("Action table size:", len(action))
