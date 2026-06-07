import yaml

with open("node_modules/langfuse-cli/openapi.yml", "r") as f:
    spec = yaml.safe_load(f)

def fix_nullable(obj):
    if isinstance(obj, dict):
        if "nullable" in obj and "type" not in obj and "$ref" not in obj and "anyOf" not in obj and "oneOf" not in obj and "allOf" not in obj:
            obj["type"] = "string" # default to string if type is missing
        for k, v in obj.items():
            fix_nullable(v)
    elif isinstance(obj, list):
        for item in obj:
            fix_nullable(item)

fix_nullable(spec)

with open("node_modules/langfuse-cli/openapi.yml", "w") as f:
    yaml.dump(spec, f, default_flow_style=False)

print("Fixed openapi.yml")
