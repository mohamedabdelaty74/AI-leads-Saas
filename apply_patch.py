#!/usr/bin/env python3
"""Apply comprehensive Gradio schema bug patch"""

with open("gradio_saas_integrated.py", 'r') as f:
    lines = f.readlines()

# Remove any existing broken patches
cleaned = []
skip_mode = False
for i, line in enumerate(lines):
    if i > 18 and i < 40:
        if 'import gradio_client.utils as gc_utils' in line:
            skip_mode = True
        if skip_mode and ('# Import SaaS client' in line or 'try:' in line.strip()):
            skip_mode = False
            cleaned.append(line)
            continue
        if skip_mode:
            continue
    cleaned.append(line)

# Find insert position
insert_index = None
for i, line in enumerate(cleaned):
    if 'from huggingface_hub import login' in line:
        insert_index = i + 1
        break

# Create the correct patch
patch = [
    '\n',
    '# PATCH: Fix Gradio schema bugs\n',
    'import gradio_client.utils as gc_utils\n',
    'original_get_type = gc_utils.get_type\n',
    '\n',
    'def patched_get_type(schema):\n',
    '    if not isinstance(schema, dict):\n',
    '        return "Any"\n',
    '    return original_get_type(schema)\n',
    '\n',
    'gc_utils.get_type = patched_get_type\n',
    '\n',
    'original_json_schema_to_python_type = gc_utils._json_schema_to_python_type\n',
    '\n',
    'def patched_json_schema_to_python_type(schema, defs=None):\n',
    '    if not isinstance(schema, dict):\n',
    '        if schema is True:\n',
    '            return "Any"\n',
    '        elif schema is False:\n',
    '            return "None"\n',
    '        else:\n',
    '            return "Any"\n',
    '    return original_json_schema_to_python_type(schema, defs)\n',
    '\n',
    'gc_utils._json_schema_to_python_type = patched_json_schema_to_python_type\n',
    '\n'
]

# Insert patch
cleaned[insert_index:insert_index] = patch

# Write back
with open("gradio_saas_integrated.py", 'w') as f:
    f.writelines(cleaned)

print("✅ Successfully applied comprehensive patch!")
