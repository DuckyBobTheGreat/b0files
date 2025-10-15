##Recusively checks folders for models and loras then appends them to a list
"""
generate_links_json.py (enhanced)
---------------------------------
Scans categorized directories (loras, checkpoints, diffusion_models, workflows, etc.)
and outputs/updates a JSON dictionary like:

{
  "#######": "####### LORAS ########",
  "lorafile1.safetensors": "",
  "lorafile2.safetensors": "",
  "#######": "####### CHECKPOINTS ########",
  "checkpoint1.safetensors": "",
  ...
}

Existing entries and links remain untouched.
New files are appended under their respective category headers.
"""

import os
import json

# ======================================================
# 🔧 CONFIGURATION
# ======================================================

# Use a dictionary: category -> directory path
DIRECTORY_MAP = {
    "loras": r"E:/gen/img/Models/loras",
    "checkpoints": r"E:/gen/img/Models/checkpoints",
    "diffusion_models": r"E:/gen/img/Models/diffusion_models",
    "workflows": r"E:/gen/img/user/default/workflows",
    # add others as needed:
    # "vae": r"E:/gen/img/Models/vae",
    # "unets": r"E:/gen/img/Models/unet"
}

# Output JSON file
OUTPUT_JSON = r"E:\GitHubRepos\golden-key\links_template_new.json"

# ======================================================
# 🧱 CORE LOGIC
# ======================================================

def load_existing_data(json_path):
    """Load existing JSON data if file exists, otherwise return an empty dict."""
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    print(f"📖 Loaded {len(data)} existing entries from {json_path}")
                    return data
                else:
                    print("⚠️ Existing file is not a valid dictionary, ignoring it.")
        except Exception as e:
            print(f"⚠️ Error reading existing JSON: {e}")
    return {}


def gather_files_by_category(directory_map):
    """Return dict {category: [filenames]} from all given directories."""
    result = {}

    for category, folder in directory_map.items():
        print(f"📁 Scanning [{category.upper()}]: {folder}")
        result[category] = []
        if not os.path.exists(folder):
            print(f"  ⚠️ Folder not found, skipping.")
            continue

        for file in os.listdir(folder):
            path = os.path.join(folder, file)
            if os.path.isfile(path):
                result[category].append(file)
        result[category].sort(key=str.lower)
    return result


def update_links_json(existing_data, categorized_files):
    """Merge new entries into JSON, grouped under headers."""
    added_total = 0
    skipped_total = 0

    # Make a new ordered dict-like structure preserving old entries
    updated_data = existing_data.copy()

    for category, files in categorized_files.items():
        header_key = f"####### {category.upper()} ########"
        if header_key not in updated_data.values():
            # Add category header line
            updated_data[f"#######_{category}"] = header_key

        added = skipped = 0
        for filename in files:
            if filename not in updated_data:
                updated_data[filename] = ""
                added += 1
            else:
                skipped += 1

        added_total += added
        skipped_total += skipped
        print(f"  → {category}: added {added}, skipped {skipped}")

    return updated_data, added_total, skipped_total


# ======================================================
# 🚀 MAIN
# ======================================================

def main():
    print("=== Generating / Updating categorized link template JSON ===")

    # Load existing file (if present)
    data = load_existing_data(OUTPUT_JSON)

    # Gather files by category
    categorized_files = gather_files_by_category(DIRECTORY_MAP)

    # Update dataset
    data, added, skipped = update_links_json(data, categorized_files)

    # Write out final data
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n✅ Update complete.")
    print(f"  → Added {added} new filenames")
    print(f"  → Skipped {skipped} existing filenames")
    print(f"  → Total entries now: {len(data)}")
    print(f"  📄 Saved to: {OUTPUT_JSON}")


# ======================================================
# 🏁 RUN SCRIPT
# ======================================================
if __name__ == "__main__":
    main()
