import re
from datetime import datetime

def _is_email(v: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v or ""))

def validate_inputs(schema_list, payload: dict):
    errors = {}
    for field in schema_list:
        name = field["name"]
        required = field.get("required", False)
        ftype = field.get("type", "str")
        val = payload.get(name, None)

        if required and val is None:
            errors[name] = "required"
            continue

        if val is None:
            continue

        try:
            if ftype == "int":
                ival = int(val)
                if "min" in field and ival < field["min"]: raise ValueError("min")
                if "max" in field and ival > field["max"]: raise ValueError("max")
            elif ftype == "email":
                if not _is_email(val): raise ValueError("email")
            elif ftype == "date":
                fmt = field.get("format", "%Y-%m-%d")
                datetime.strptime(val, fmt if "%" in fmt else "%Y-%m-%d")
            elif ftype == "str":
                if "enum" in field and val not in field["enum"]: raise ValueError("enum")
        except Exception as e:
            errors[name] = f"invalid({e})"
    return errors
