#!/usr/bin/env python3
"""
Automatic patcher for Gradio schema bug in gradio_saas_integrated.py
This fixes the "TypeError: argument of type 'bool' is not iterable" error
"""

import sys

def patch_gradio_file():
    file_path = "gradio_saas_integrated.py"

    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find the line "from huggingface_hub import login"
        insert_index = None
        for i, line in enumerate(lines):
            if 'from huggingface_hub import login' in line:
                insert_index = i + 1
                break

        if insert_index is None:
            print("❌ Could not find 'from huggingface_hub import login' line")
            return False

        # Check if patch already exists
        for line in lines[insert_index:insert_index+10]:
            if 'patched_get_type' in line:
                print("✅ Patch already applied, no changes needed")
                return True

        # Create the patch
        patch = [
            "\n",
            "# PATCH: Fix Gradio schema bug\n",
            "import gradio_client.utils as gc_utils\n",
            "original_get_type = gc_utils.get_type\n",
            "\n",
            "def patched_get_type(schema):\n",
            "    if not isinstance(schema, dict):\n",
            "        return \"Any\"\n",
            "    return original_get_type(schema)\n",
            "\n",
            "gc_utils.get_type = patched_get_type\n",
            "\n"
        ]

        # Insert the patch
        lines[insert_index:insert_index] = patch

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print("✅ Successfully patched gradio_saas_integrated.py")
        print(f"   Inserted patch at line {insert_index + 1}")
        return True

    except Exception as e:
        print(f"❌ Error patching file: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Gradio Schema Bug Patcher")
    print("=" * 60)
    print()

    if patch_gradio_file():
        print()
        print("Next steps:")
        print("1. Restart Gradio: pkill -9 python && nohup python gradio_saas_integrated.py > gradio.log 2>&1 &")
        print("2. Wait 30 seconds for UI to load")
        print("3. Try logging in again")
        sys.exit(0)
    else:
        sys.exit(1)
