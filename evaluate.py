import json
from pathlib import Path

from validator import validate_result

# ===== 评测设置 =====
RUN_FILTER = "deepseek"
DETAIL_RUNS = ["deepseek_v3_run3_check"]
DATA_FILE = "testset/test_cases.json"  # 开发集是 "eval_cases.json"
# ===================

base_path = Path(__file__).parent
output_dir = base_path / "outputs"

with open(base_path / DATA_FILE, "r", encoding="utf-8") as f:
    cases = json.load(f)
case_dict = {case["id"]: case["expected"] for case in cases}


def evaluate_run(run_name, show_detail):
    """评测一次实验，返回统计结果。"""

    def show(*args):
        if show_detail:
            print(*args)

    with open(output_dir / f"batch_output_{run_name}.json", "r", encoding="utf-8") as f:
        all_results = json.load(f)
    with open(output_dir / f"batch_errors_{run_name}.json", "r", encoding="utf-8") as f:
        errors = json.load(f)

    output_ids = [record["case_id"] for record in all_results]
    error_ids = [record["case_id"] for record in errors]

    # 数据对不上说明程序有 bug，直接停下
    if len(output_ids) != len(set(output_ids)):
        raise ValueError(f"{run_name}：批量结果中存在重复的案例编号")
    if set(output_ids) & set(error_ids):
        raise ValueError(f"{run_name}：同一案例同时出现在结果和错误记录中")
    unknown = (set(output_ids) | set(error_ids)) - set(case_dict)
    if unknown:
        raise ValueError(f"{run_name}：出现测试集中没有的案例编号 {unknown}")
    lost = set(case_dict) - set(output_ids) - set(error_ids)
    if lost:
        raise ValueError(f"{run_name}：这些案例既没有结果也没有错误记录 {lost}")

    total_passed = 0
    total_fields = 0
    invalid_count = 0

    show(f"\n################ {run_name} 详细结果 ################")

    # 成功的案例：逐字段比较
    for record in all_results:
        case_id = record["case_id"]
        model_result = record["result"]
        expected_data = case_dict[case_id]

        show(f"\n===== {case_id} =====")

        try:
            validate_result(model_result)
        except ValueError as error:
            invalid_count += 1
            show(f"【结构错误】{error}")

        passed = 0
        for field, expected_value in expected_data.items():
            if field not in model_result:
                show(f"【缺失】{field}")
                continue
            actual_value = model_result[field]
            if expected_value == actual_value:
                passed += 1
            else:
                show(f"【不一致】{field}")
                show("  人工答案：", expected_value)
                show("  模型答案：", actual_value)

        show(f"精确匹配：{passed}/{len(expected_data)}")
        total_passed += passed
        total_fields += len(expected_data)

    # 失败的案例：按 0 分计入
    for record in errors:
        case_id = record["case_id"]
        field_count = len(case_dict[case_id])
        show(f"\n===== {case_id}（运行失败）=====")
        show(f"【{record['error_type']}】{record['error_message']}")
        show(f"精确匹配：0/{field_count}（按 0 分计入）")
        total_fields += field_count

    return {
        "structure_ok": len(all_results) - invalid_count,
        "failed": len(errors),
        "passed": total_passed,
        "fields": total_fields,
    }


# 找出所有符合条件的实验，逐个评测
rows = []
for path in sorted(output_dir.glob("run_summary_*.json")):
    with open(path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    run_name = summary["run_name"]
    if summary.get("data_file", "eval_cases.json") != DATA_FILE:
        continue
    if RUN_FILTER not in run_name:
        continue
    score = evaluate_run(run_name, run_name in DETAIL_RUNS)
    rows.append((summary, score))

if not rows:
    print("没有找到符合条件的实验，请先运行 main.py")

# 对比表
print("\n================ 实验对比 ================")
for summary, score in rows:
    print(f"{summary['run_name']}")
    print(f"  结构合格：{score['structure_ok']}/{summary['case_count']}"
          f"    运行失败：{score['failed']} 条")
    print(f"  精确匹配：{score['passed']}/{score['fields']}（失败案例按 0 分计入）")
    print(f"  Token：输入 {summary['prompt_tokens']}，输出 {summary['completion_tokens']}"
          f"    耗时：{summary['total_seconds']} 秒")