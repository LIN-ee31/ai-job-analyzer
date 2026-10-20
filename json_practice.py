
import json

# 一段符合JSON格式的字符串
raw = '''
{
    "job_title": "AI应用开发实习生",
    "required_skills": ["Python", "API调用"],
    "preferred_skills": ["RAG"]
}
'''

# 将JSON字符串转换成Python对象
data = json.loads(raw)

print("转换前：", type(raw))
print("转换后：", type(data))

print("岗位名称：", data["job_title"])
print("必备技能：", data["required_skills"])

