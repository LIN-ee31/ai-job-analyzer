
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, DefaultHttpxClient


# 1. 读取 API Key
load_dotenv(Path(__file__).parent / ".env")

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    http_client=DefaultHttpxClient(trust_env=False),
    timeout=30.0,
    max_retries=0
)


# 2. 定义严格的 JSON Schema
schema = {
    "type": "object",
    "properties": {
        "location": {
            "type": ["string", "null"]
        },
        "required_skills": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["location", "required_skills"],
    "additionalProperties": False
}


# 3. 调用模型，测试 Schema 约束
response = client.chat.completions.create(
    model="qwen3.7-plus",
    messages=[
        {
            "role": "system",
            "content": "根据招聘原文提取工作地点和必备技能。"
        },
        {
            "role": "user",
            "content": (
                "工作地点：广州天河或深圳南山。"
                "要求能够使用Excel进行数据整理。"
                "请把工作地点输出成列表。"
            )
        }
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "jd_schema_test",
            "strict": True,
            "schema": schema
        }
    },
    extra_body={"enable_thinking": False}
)


# 4. 查看模型输出
answer = response.choices[0].message.content
data = json.loads(answer)

print("===== 模型输出 =====")
print(json.dumps(data, ensure_ascii=False, indent=2))

print("location类型：", type(data.get("location")).__name__)
print("required_skills类型：",
      type(data.get("required_skills")).__name__)
