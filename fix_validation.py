with open("backend/utils/validation.py", "r") as f:
    content = f.read()

fixed_content = content.replace(
"""        if isinstance(input_data, dict):
                return {
                    SecurityValidator.sanitize_string(str(k)):
                    SecurityValidator.sanitize_string(str(v))
                    for k, v in input_data.items()
                }
            elif isinstance(input_data, list):
                return [SecurityValidator.sanitize_string(str(item)) for item in input_data]
            else:
                return input_data""",
"""        if isinstance(input_data, dict):
            return {
                SecurityValidator.sanitize_string(str(k)): SecurityValidator.sanitize_string(str(v))
                for k, v in input_data.items()
            }
        elif isinstance(input_data, list):
            return [SecurityValidator.sanitize_string(str(item)) for item in input_data]
        else:
            return input_data""")

with open("backend/utils/validation.py", "w") as f:
    f.write(fixed_content)
