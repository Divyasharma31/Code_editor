import re

def parse_prompt(raw_text: str):
    """
    Parses a generic coding problem prompt to extract components.
    This uses heuristics commonly found in LeetCode/HackerEarth.
    """
    data = {
        "title": "Untitled Problem",
        "description": "",
        "constraints": "",
        "time_limit_ms": 1000,
        "test_cases": []
    }
    
    lines = raw_text.strip().split('\n')
    if not lines:
        return data

    # 1. First non-empty line as title
    data["title"] = lines[0].strip()

    # 2. Extract Time Limit (e.g., "Time Limit: 1.5s" or "Time limit: 2000 ms")
    time_limit_match = re.search(r'time\s*limit.*?([0-9.]+)\s*(s|sec|ms)', raw_text, re.IGNORECASE)
    if time_limit_match:
        val = float(time_limit_match.group(1))
        unit = time_limit_match.group(2).lower()
        if unit.startswith('s'):
            data["time_limit_ms"] = int(val * 1000)
        else:
            data["time_limit_ms"] = int(val)

    # 3. Extract Constraints
    constraints_match = re.search(r'constraints?:?\s*(.*?)(?=example|input|output|$)', raw_text, re.IGNORECASE | re.DOTALL)
    if constraints_match:
        data["constraints"] = constraints_match.group(1).strip()
    
    # 4. Extract Test Cases (Examples with Input / Output)
    # Looking for patterns like "Input: ... Output: ..."
    examples = re.finditer(r'Input\s*:?\s*(.*?)\s*Output\s*:?\s*(.*?)(?=Example|Input|$)', raw_text, re.IGNORECASE | re.DOTALL)
    for idx, match in enumerate(examples):
        inp = match.group(1).strip()
        out = match.group(2).strip()
        if inp and out:
            data["test_cases"].append({
                "input_data": inp,
                "expected_output": out,
                "is_sample": True
            })

    # 5. Extract Description (Everything between Title and first section like Example or Constraint)
    desc_match = re.split(r'(?i)(constraints?:|example\s*\d*:|input\s*:)', raw_text, 1)
    if len(desc_match) > 0:
        desc_lines = desc_match[0].strip().split('\n')[1:] # Skip title
        data["description"] = '\n'.join(desc_lines).strip()
    
    if not data["description"]:
        data["description"] = "No description provided."

    return data
