import json
from pathlib import Path

# ===== 设置 =====
DATA_FILE = "testset/test_cases.json"
RUNS = ["deepseek_v3_test_run1", "deepseek_v3_test_run2"]
# ===============

base_path = Path(__file__).parent
with open(base_path / DATA_FILE, "r", encoding="utf-8") as f:
    cases = json.load(f)

for run_name in RUNS:
    with open(base_path / "outputs" / f"batch_output_{run_name}.json", "r", encoding="utf-8") as f:
        results = {r["case_id"]: r["result"] for r in json.load(f)}

    stats = {}  # 分组名 -> [对的字段数, 总字段数]
    for case in cases:
        case_id = case["id"]
        model_result = results.get(case_id)  # None 表示运行失败，按 0 分计
        half = "T001-T005" if int(case_id[1:]) <= 5 else "T006-T010"
        for field, expected_value in case["expected"].items():
            ok = (model_result is not None and field in model_result
                  and model_result[field] == expected_value)
            kind = "空值字段" if expected_value in (None, []) else "非空字段"
            for key in ("总分", half, kind):
                s = stats.setdefault(key, [0, 0])
                s[0] += ok
                s[1] += 1

    print(run_name)
    for key in ("总分", "T001-T005", "T006-T010", "非空字段", "空值字段"):
        passed, total = stats[key]
        print(f"  {key}：{passed}/{total}")