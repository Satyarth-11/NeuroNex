import os

jsx_path = r"C:\Users\satya\.gemini\antigravity-ide\scratch\neuronex\frontend\src\pages\Validation.jsx"
with open(jsx_path, encoding="utf-8") as f:
    text = f.read()

in_str = None
in_comment = False
stack = []
pairs = {')': '(', '}': '{', ']': '['}

i = 0
n = len(text)
while i < n:
    ch = text[i]
    if in_comment:
        if ch == '*' and i + 1 < n and text[i + 1] == '/':
            in_comment = False
            i += 2
            continue
        elif ch == '\n':
            in_comment = False
    elif in_str:
        if ch == in_str and text[i - 1] != '\\':
            in_str = None
    else:
        if ch == '/' and i + 1 < n and text[i + 1] == '*':
            in_comment = True
            i += 2
            continue
        elif ch == '/' and i + 1 < n and text[i + 1] == '/':
            in_comment = True
            i += 2
            continue
        elif ch in ('"', "'", '`'):
            in_str = ch
        elif ch in ('(', '{', '['):
            line_no = text[:i].count('\n') + 1
            stack.append((ch, line_no))
        elif ch in (')', '}', ']'):
            line_no = text[:i].count('\n') + 1
            if not stack:
                print(f"Unmatched closing {ch} at line {line_no}")
                break
            top, top_line = stack.pop()
            if pairs[ch] != top:
                print(f"Mismatched {ch} at line {line_no} matching {top} from line {top_line}")
                break
    i += 1

if stack:
    print(f"Unclosed {len(stack)} brackets. Top 5:")
    for ch, line in stack[-5:]:
        print(f"  {ch} from line {line}")
else:
    print("ALL BRACKETS, PARENTHESES, AND BRACES ARE PERFECTLY BALANCED!")
