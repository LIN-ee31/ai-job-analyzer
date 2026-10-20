
def validate_result(data):

    required_fields = [
        "job_title",
        "company",
        "location",
        "education",
        "major_requirement",
        "required_skills",
        "preferred_skills",
        "attendance",
        "duration"
    ]

    # 1. 检查整体类型
    if not isinstance(data, dict):
        raise ValueError("提取结果必须是字典")

    # 2. 检查字段是否完整
    for field in required_fields:
        if field not in data:
            raise ValueError(f"缺少字段：{field}")

    print("字段完整性检查通过")

    # 3. 普通字段：必须是字符串或None
    text_fields = [
        "job_title",
        "company",
        "location",
        "education",
        "major_requirement",
        "attendance",
        "duration"
    ]

    for field in text_fields:
        value = data[field]

        if value is not None and not isinstance(value, str):
            raise ValueError(
                f"{field} 必须是字符串或null"
            )

    # 4. 技能字段：必须是列表
    list_fields = [
        "required_skills",
        "preferred_skills"
    ]

    for field in list_fields:
        value = data[field]

        if not isinstance(value, list):
            raise ValueError(f"{field} 必须是列表")

        # 列表中的每个元素必须是字符串
        for item in value:
            if not isinstance(item, str):
                raise ValueError(
                    f"{field} 中的元素必须是字符串"
                )

    print("数据结构检查通过")
