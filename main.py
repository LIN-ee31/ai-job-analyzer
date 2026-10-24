import json
import os
import time
from pathlib import Path

import openai
from dotenv import load_dotenv
from openai import OpenAI, DefaultHttpxClient

from validator import validate_result

# ===== 实验配置：每次实验只改这里 =====
MODEL = "deepseek-v4.1-flash"
USE_SCHEMA = False
PROMPT_VERSION = "v3"
RUN_NAME = "deepseek_v3_run3_check"
# =====================================

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

output_path = OUTPUT_DIR / f"batch_output_{RUN_NAME}.json"
error_path = OUTPUT_DIR / f"batch_errors_{RUN_NAME}.json"
summary_path = OUTPUT_DIR / f"run_summary_{RUN_NAME}.json"
prompt_path = BASE_DIR / "prompts" / f"{PROMPT_VERSION}.txt"

# 运行前检查
if output_path.exists():
    raise SystemExit(f"{output_path.name} 已存在，请修改 RUN_NAME，避免覆盖旧结果")
if not prompt_path.exists():
    raise SystemExit(f"找不到 {prompt_path}，请检查 prompts 文件夹里的文件名")

# 1. 读取 API Key，连接百炼
load_dotenv(BASE_DIR / ".env")
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("API Key读取失败，请检查.env文件")

client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    http_client=DefaultHttpxClient(trust_env=False),
    timeout=60.0,
    max_retries=0
)

# 2. 读取测试集和 Prompt
with open(BASE_DIR / "eval_cases.json", "r", encoding="utf-8") as f:
    cases = json.load(f)

system_prompt = prompt_path.read_text(encoding="utf-8")

# 3. 输出格式：严格 Schema 或 JSON Mode
nullable_str = {"type": ["string", "null"]}
str_list = {"type": "array", "items": {"type": "string"}}

schema = {
    "type": "object",
    "properties": {
        "job_title": nullable_str,
        "company": nullable_str,
        "location": nullable_str,
        "education": nullable_str,
        "major_requirement": nullable_str,
        "required_skills": str_list,
        "preferred_skills": str_list,
        "attendance": nullable_str,
        "duration": nullable_str,
    },
    "required": [
        "job_title", "company", "location", "education",
        "major_requirement", "required_skills", "preferred_skills",
        "attendance", "duration",
    ],
    "additionalProperties": False,
}

if USE_SCHEMA:
    response_format = {
        "type": "json_schema",
        "json_schema": {"name": "jd_extraction", "strict": True, "schema": schema},
    }
else:
    response_format = {"type": "json_object"}

# 4. 批量分析
all_results = []
errors = []
prompt_tokens = 0
completion_tokens = 0
start_all = time.perf_counter()

for case in cases:
    case_id = case["id"]
    print("\n本次分析案例：", case_id)
    answer = None
    start = time.perf_counter()

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请提取以下招聘信息，输出JSON：\n" + case["jd"]}
            ],
            response_format=response_format,
            extra_body={"enable_thinking": False},
            max_tokens=1000
        )
        print(f"耗时：{time.perf_counter() - start:.1f} 秒")

        if response.usage:
            prompt_tokens += response.usage.prompt_tokens
            completion_tokens += response.usage.completion_tokens

        answer = response.choices[0].message.content
        data = json.loads(answer)
        validate_result(data)

    except openai.APIError as e:
        errors.append({"case_id": case_id, "error_type": "API调用失败",
                       "error_message": str(e), "raw_output": answer})
        print("❌ API调用失败：", e)
        continue

    except json.JSONDecodeError as e:
        errors.append({"case_id": case_id, "error_type": "JSON解析失败",
                       "error_message": str(e), "raw_output": answer})
        print("❌ JSON解析失败：", e)
        continue

    except ValueError as e:
        errors.append({"case_id": case_id, "error_type": "结构校验失败",
                       "error_message": str(e), "raw_output": answer})
        print("❌ 结构校验失败：", e)
        continue

    all_results.append({"case_id": case_id, "result": data})
    print("✅ 已完成案例：", case_id)

total_seconds = time.perf_counter() - start_all

# 5. 保存结果
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

with open(error_path, "w", encoding="utf-8") as f:
    json.dump(errors, f, ensure_ascii=False, indent=2)

summary = {
    "run_name": RUN_NAME,
    "model": MODEL,
    "use_schema": USE_SCHEMA,
    "prompt_version": PROMPT_VERSION,
    "run_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    "case_count": len(cases),
    "success": len(all_results),
    "failed": len(errors),
    "prompt_tokens": prompt_tokens,
    "completion_tokens": completion_tokens,
    "total_seconds": round(total_seconds, 1),
}
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

# 6. 汇总
print("\n===== 运行汇总 =====")
for key, value in summary.items():
    print(f"{key}: {value}")
if errors:
    print("失败案例：", [e["case_id"] for e in errors])