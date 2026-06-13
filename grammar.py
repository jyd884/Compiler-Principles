class Grammar:
    def __init__(self, file_path):
        self.__start = None
        self.__productions = dict()
        self.__Vn = set()
        self.__Vt = set()
        self.__target = ""
        self.__valid = self.__parse_file(file_path)

    def __parse_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                lines = [line.strip() for line in f if line.strip()]
            if not lines:
                print("错误：文法文件为空！")
                return False
            if lines and '(' not in lines[-1]:
                self.__target = lines[-1].strip()
                lines = lines[:-1]
            if not lines:
                print("错误：未找到有效的产生式！")
                return False
            for idx, line in enumerate(lines):
                if '(' not in line:
                    print(f"错误：第{idx+1}行产生式无'('，格式非法！")
                    return False
                left, right = line.split('(', 1)
                right = right.rstrip(')')
                if len(left) != 1 or not left.isupper():
                    print(f"错误：第{idx+1}行左部{left}非单个大写字母！")
                    return False
                for c in right:
                    if not (c.isalnum()):
                        print(f"错误：第{idx+1}行右部{right}含非法字符{c}！")
                        return False
                if idx == 0:
                    self.__start = left
                if left not in self.__productions:
                    self.__productions[left] = []
                if right not in self.__productions[left]:
                    self.__productions[left].append(right)
                self.__Vn.add(left)
                for c in right:
                    if c.isupper():
                        self.__Vn.add(c)
                    else:
                        self.__Vt.add(c)
            for left in self.__productions:
                self.__productions[left].sort(key=len, reverse=True)
            return True
        except FileNotFoundError:
            print("错误：未找到g.in文件！")
            return False
        except Exception as e:
            print(f"错误：文法解析失败，{e}")
            return False

    def is_valid(self):
        return self.__valid

    def get_start(self):
        return self.__start if self.__valid else None

    def get_productions(self):
        return self.__productions if self.__valid else None

    def get_Vn(self):
        return self.__Vn if self.__valid else None

    def get_Vt(self):
        return self.__Vt if self.__valid else None

    def get_target(self):
        return self.__target if self.__valid else None

    def classify(self):
        if not self.__valid:
            return "非法文法，无法分类"
        prod = self.__productions
        Vn, Vt = self.__Vn, self.__Vt
        is_3 = True
        is_right_linear = True
        is_left_linear = True
        for left, rights in prod.items():
            for right in rights:
                if right == "":
                    if left != self.__start:
                        is_3 = False
                    continue
                if len(right) == 1:
                    if right in Vn:
                        continue
                    elif right in Vt:
                        continue
                    else:
                        is_3 = False
                elif len(right) == 2:
                    c1, c2 = right[0], right[1]
                    if not (c1 in Vt and c2 in Vn):
                        is_right_linear = False
                    if not (c1 in Vn and c2 in Vt):
                        is_left_linear = False
                else:
                    is_3 = False
        if is_3 and (is_right_linear or is_left_linear):
            return "3型文法（正规文法）" + ("右线性" if is_right_linear else "左线性")
        is_2 = True
        for left in prod.keys():
            if len(left) != 1 or left not in Vn:
                is_2 = False
                break
        if is_2:
            return "2型文法（上下文无关文法）"
        is_1 = True
        for left, rights in prod.items():
            for right in rights:
                if len(left) > len(right) and right != "":
                    is_1 = False
                    break
            if not is_1:
                break
        if is_1:
            return "1型文法（上下文有关文法）"
        return "0型文法（短语文法）"

    def derive(self, target):
        if not self.__valid:
            return "非法文法，无法推导"
        cls = self.classify()
        if "3型文法" not in cls:
            return f"{cls}，无法进行3型文法推导"
        start = self.__start
        prod = self.__productions
        Vn, Vt = self.__Vn, self.__Vt
        derive_steps = [start]
        current = start
        if "右线性" in cls:
            while True:
                non_terminal_idx = -1
                for i in range(len(current)-1, -1, -1):
                    if current[i] in Vn:
                        non_terminal_idx = i
                        break
                if non_terminal_idx == -1:
                    break
                nt = current[non_terminal_idx]
                found = False
                for right in prod[nt]:
                    if len(right) == 2 and right[0] in Vt and right[1] in Vn:
                        if non_terminal_idx + 2 <= len(target) and target[non_terminal_idx] == right[0]:
                            new_current = current[:non_terminal_idx] + right
                            derive_steps.append(new_current)
                            current = new_current
                            found = True
                            break
                    elif len(right) == 1 and right in Vt:
                        if non_terminal_idx + 1 <= len(target) and target[non_terminal_idx] == right:
                            new_current = current[:non_terminal_idx] + right
                            derive_steps.append(new_current)
                            current = new_current
                            found = True
                            break
                    elif right == "":
                        if non_terminal_idx == len(target):
                            new_current = current[:non_terminal_idx] + current[non_terminal_idx+1:]
                            derive_steps.append(new_current)
                            current = new_current
                            found = True
                            break
                if not found:
                    return "该字符串无法由当前3型文法推导"
        elif "左线性" in cls:
            while True:
                non_terminal_idx = -1
                for i in range(len(current)):
                    if current[i] in Vn:
                        non_terminal_idx = i
                        break
                if non_terminal_idx == -1:
                    break
                nt = current[non_terminal_idx]
                found = False
                for right in prod[nt]:
                    if right == "":
                        new_current = current[non_terminal_idx+1:]
                        derive_steps.append(new_current)
                        current = new_current
                        found = True
                        break
                    if len(right) == 1 and right in Vt:
                        if non_terminal_idx < len(target) and target[len(target)-1 - non_terminal_idx] == right:
                            new_current = current[:non_terminal_idx] + right
                            derive_steps.append(new_current)
                            current = new_current
                            found = True
                            break
                    if len(right) == 2 and right[0] in Vn and right[1] in Vt:
                        if non_terminal_idx < len(target) and target[len(target)-1 - non_terminal_idx] == right[1]:
                            new_current = current[:non_terminal_idx] + right
                            derive_steps.append(new_current)
                            current = new_current
                            found = True
                            break
                if not found:
                    return "该字符串无法由当前3型文法推导"
        if current == target:
            return "推导过程：" + " → ".join(derive_steps)
        else:
            return "该字符串无法由当前3型文法推导"


if __name__ == "__main__":
    g = Grammar("g.in")
    if g.is_valid():
        print("文法合法！")
        print(f"开始符号：{g.get_start()}")
        print(f"非终结符：{g.get_Vn()}")
        print(f"终结符：{g.get_Vt()}")
        print(f"产生式：{g.get_productions()}")
        print(g.classify())
        target = g.get_target()
        if target:
            print(g.derive(target))
    else:
        print("文法非法！")






