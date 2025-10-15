"""
auto_index.py
Scans multiple model directories and adds entries to a JSON registry.

Features:
- Loops through all directories defined in MODEL_PATHS
- Detects base model names via flexible regex patterns
- Skips files already listed in the registry (duplicate prevention)
- Generates random IDs (A####)
- Calculates size automatically
"""

import os
import json
import random
import re

# ======================================================
# 🔧 CONFIGURATION
# ======================================================

# Path to the JSON registry
REGISTRY_PATH = r"E:\GitHubRepos\golden-key\data\names.json"

# Directories to scan by model type
MODEL_PATHS = {
    "lora":       r"E:/gen/img/Models/loras",
    "checkpoint": r"E:/gen/img/Models/checkpoints",
    "checkpoint": r"E:/gen/img/Models/diffusion_models",
    "workflow":   r"E:/gen/img/user/default/workflows"
}

# Base model recognition patterns (regex, case-insensitive)
BASE_MODEL_PATTERNS = {
    "ILLUSTRIOUS":  r"illustrious[a-z0-9_-]*",
    "AURAFLOW":  r"auraflow[a-z0-9_-]*",
    "WAN":      r"wan[a-z0-9_-]*",
    "HUNYUAN":  r"hunyuan[a-z0-9_-]*",
    "QWEN":     r"qwen[a-z0-9_-]*",
    "HiDream":  r"hidream[a-z0-9_-]*",
    "SDXL":     r"sd[\s\-_.]*xl",
    "SD1.5":    r"sd[\s\-_.]*1[\s\-_.]*5",
    "SD3":      r"sd[\s\-_.]*3",
    "PONY":     r"pony[a-z0-9_-]*",
    "FLUX":     r"flux[a-z0-9_-]*"
}

# Skip duplicates already present in the registry (by filename)
SKIP_EXISTING_FILES = True

# ======================================================
# 🧱 HELPERS
# ======================================================

def generate_id(existing_ids):
    """Generate unique ID like A1234."""
    while True:
        new_id = f"A{random.randint(1000, 9999)}"
        if new_id not in existing_ids:
            return new_id

def get_file_size_gb(filepath):
    """Return file size as human-readable GB string."""
    size_bytes = os.path.getsize(filepath)
    size_gb = size_bytes / (1024 ** 3)
    return f"{size_gb:.1f}GB"

def detect_base_model(filename):
    """Detect base model from filename using regex patterns."""
    lower_name = filename.lower()
    for label, pattern in BASE_MODEL_PATTERNS.items():
        if re.search(pattern, lower_name, re.IGNORECASE):
            return label
    return ""

# ======================================================
# 🚀 MAIN
# ======================================================

def main():
    print("=== Starting Auto Index ===")

    # Load or initialize registry
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                registry = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not parse existing JSON ({e}). Starting new registry.")
            registry = {}
    else:
        print(f"📁 No registry found, creating new one at: {REGISTRY_PATH}")
        registry = {}

    existing_ids = set(registry.keys())
    existing_files = {entry["filename"] for entry in registry.values() if "filename" in entry}

    # Iterate through directories
    for model_type, folder in MODEL_PATHS.items():
        print(f"\n🔍 Scanning {model_type}: {folder}")

        if not os.path.exists(folder):
            print(f"❌ Directory not found: {folder}")
            continue

        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        print(f"📂 Found {len(files)} files in {folder}")

        if not files:
            print("⚠️ No files detected — skipping.")
            continue

        for filename in files:
            if SKIP_EXISTING_FILES and filename in existing_files:
                print(f"⏭️ Skipping existing file: {filename}")
                continue

            filepath = os.path.join(folder, filename)
            entry_id = generate_id(existing_ids)
            existing_ids.add(entry_id)
            size = get_file_size_gb(filepath)
            base_model = detect_base_model(filename)

            registry[entry_id] = {
                "filename": filename,
                "model_type": model_type,
                "base_model": base_model,
                "size": size,
                "metadata": {
                    "trigger_words": "",
                    "download_link": "",
                    "description": ""
                }
            }

            existing_files.add(filename)
            print(f"➕ Added {entry_id}: {filename} ({model_type}, {size}, base={base_model or 'none'})")

    # Save registry
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Registry updated at {REGISTRY_PATH}")
    print("=== Done ===")

# ======================================================
# 🏁 RUN SCRIPT
# ======================================================
if __name__ == "__main__":
    main()
