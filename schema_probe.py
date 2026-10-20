import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, DefaultHttpxClient

from validator import validate_result

BASE_DIR = Path(__file__).parent
CASE_ID = "JD003"
MODEL = "qwen3.7-plus"

# 1. 读取 API Key，连接百炼
load_dotenv(BASE_DIR / ".env")

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    http_client=DefaultHttpxClient(trust_env=False),
    timeout=60.0,
    max_retries=0
)

# 2. 九字段 Schema
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

# 3. 从 eval_cases.json 读取 JD003
with open(BASE_DIR / "eval_cases.json", encoding="utf-8") as f:
    cases = json.load(f)

case = next((c for c in cases if c.get("id") == CASE_ID), None)
if case is None:
    raise SystemExit(f"eval_cases.json 中找不到 {CASE_ID}")

jd_text = case["jd"]

# 4. Prompt V2（与 main.py 完全相同）
SYSTEM_PROMPT = """你是一名招聘信息结构化提取助手。

请严格根据招聘原文提取信息，不得编造、推测或自行增加要求。

请按照以下JSON结构输出：

{
    "job_title": null,
    "company": null,
    "location": null,
    "education": null,
    "major_requirement": null,
    "required_skills": [],
    "preferred_skills": [],
    "attendance": null,
    "duration": null
}

一、基本规则

1. 必须输出全部9个字段。
2. 普通字段未提及时填写null。
3. 技能列表没有对应内容时填写[]。
4. 只输出JSON，不添加解释或Markdown。
5. 只根据原文提取，不使用常识补充招聘要求。

二、技能提取规则

1. required_skills记录任职要求中明确要求具备的技能和工作能力。
2. preferred_skills记录出现"优先"、"加分"等表述的技能或经验。
3. 不得将加分条件误判为必备条件。
4. 保留技能的能力程度，例如"了解"、"熟悉"、"掌握"、"能够使用"等。
5. 保留工具与任务之间的关系，例如"使用Excel进行数据整理"，不要简化成"Excel"。
6. 对于一组工具的使用经验要求，保留完整的经验条件，不要随意拆成孤立的工具名称。
7. 对于独立的多项能力，可以分别提取，但不能遗漏原文明确的要求。
8. 不要因为某个技能出现在岗位职责中，就自动认定它是硬性任职要求。
9. 任职要求中的明确工作能力可以提取；单纯的兴趣和性格品质不作为技能提取。

三、其他字段规则

1. education只记录学历要求。
2. major_requirement记录专业要求，保留"专业不限"和"相关专业优先"等限定。
3. location出现多个地点时，保留全部地点。
4. attendance保留最低出勤要求及相关限定。
5. duration保留最低实习时长，以及明确说明的优先条件。
6. 原文没有说明的信息必须填写null。

输出前检查：
- 是否遗漏明确的技能或能力要求？
- 是否混淆必备条件和优先条件？
- 是否丢失能力程度、工具用途或任务关系？
- 是否添加了原文没有的信息？

仅输出合法JSON。"""

# 5. 调用模型（严格 Schema）
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "请提取以下招聘信息，输出JSON：\n" + jd_text},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {"name": "jd_extraction", "strict": True, "schema": schema},
    },
    extra_body={"enable_thinking": False},
    max_tokens=1000,
)

# 6. 查看与校验
choice = response.choices[0]
print("finish_reason：", choice.finish_reason)

data = json.loads(choice.message.content)
print("===== 模型输出 =====")
print(json.dumps(data, ensure_ascii=False, indent=2))
print("字段集合一致：", set(data.keys()) == set(schema["required"]))
print("location 类型：", type(data.get("location")).__name__)

try:
    validate_result(data)
    print("validate_result：通过")
except ValueError as e:
    print("validate_result：未通过 ->", e)

# 7. 保存结果
with open(BASE_DIR / "schema_probe_output.json", "w", encoding="utf-8") as f:
    json.dump({"case_id": CASE_ID, "model": MODEL, "result": data},
              f, ensure_ascii=False, indent=2)