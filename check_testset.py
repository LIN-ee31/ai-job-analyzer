import json
from pathlib import Path

from validator import validate_result

path = Path(__file__).parent / "testset" / "test_cases.json"
with open(path, "r", encoding="utf-8") as f:
    cases = json.load(f)

for case in cases:
    expected = case["expected"]
    try:
        validate_result(expected)
        filled = sum(1 for v in expected.values() if v not in (None, []))
        print(f"{case['id']}：结构合格，非空字段 {filled}/9")
    except ValueError as e:
        print(f"{case['id']}：结构错误：{e}")
