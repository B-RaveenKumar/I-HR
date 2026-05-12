import os

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'bank_advice_report' in line:
            print(f"Line {i+1}: {repr(line)}")
