REGISTRY = {
    "send_report": {
        "schedulable": True,
        "description": "Send periodic report",
        "inputs_schema": [
            {"name": "email", "type": "email", "required": True},
            {"name": "days", "type": "int", "required": False, "min": 1, "max": 30},
        ],
    },
    "reindex_search": {
        "schedulable": True,
        "description": "Rebuild search index",
        "inputs_schema": [
            {"name": "segment", "type": "str", "required": False, "enum": ["all", "news", "users"]},
        ],
    },
    "heavy_etl": {
        "schedulable": False,
        "description": "Heavy ETL (not user-schedulable)",
        "inputs_schema": [],
    },
}
