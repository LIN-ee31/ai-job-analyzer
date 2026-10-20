
from validator import validate_result

# 准备一份正确的测试数据
sample_data = {
    "job_title": "AI应用开发实习生",
    "company": None,
    "location": "广州",
    "education": "本科及以上",
    "major_requirement": None,
    "required_skills": ["Python"],
    "preferred_skills": ["RAG"],
    "attendance": None,
    "duration": None
}

# 测试1：正确数据应该通过
print("===== 测试1：正确数据 =====")
validate_result(sample_data)


# 测试2：错误数据应该被拦截
print("\n===== 测试2：错误数据 =====")

bad_data = sample_data.copy()
bad_data["preferred_skills"] = "RAG"

try:
    validate_result(bad_data)
except ValueError as error:
    print("成功检测到错误：", error)
else:
    print("测试失败：错误数据没有被拦截")
