import re

with open('/tmp/ssmp.s', 'r') as f:
    lines = f.readlines()

current_func = ""
func_counts = {}

# Characters we are looking for: E(69), P(80), !(33), 9(57), R(82), 4(52), H(72), L(76)
targets = ["#69", "#80", "#33", "#57", "#82", "#52", "#72", "#76"]

for line in lines:
    if re.match(r'^[0-9a-fA-F]+ <.*>:$', line):
        current_func = line.strip()
        func_counts[current_func] = {t: 0 for t in targets}
    elif current_func:
        for t in targets:
            if t in line or f"{t}\t" in line or f"{t} " in line or f"{t};" in line or line.endswith(t):
                func_counts[current_func][t] += 1

print("Functions with matches:")
for func, counts in func_counts.items():
    score = sum(1 for v in counts.values() if v > 0)
    if score >= 6:
        print(f"\n{func}: score {score}/8")
        for k, v in counts.items():
            if v > 0:
                print(f"  {k}: {v} times")
