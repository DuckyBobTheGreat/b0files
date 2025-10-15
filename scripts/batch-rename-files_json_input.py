import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ===============================================================
# JSON Key–Value Filename Replacer (Exact Match)
# ---------------------------------------------------------------
# - JSON mapping example:
#     { "cat": "dog", "apple": "banana" }
# - Modes:
#     * Scan for Keys (rename key → value)
#     * Scan for Values (rename value → key)
# - Match Target:
#     * Base name only (no extension)  -> "cat.png" -> "dog.png"
#     * Full filename (with extension) -> "cat.png" -> "dog.png" (if JSON uses full names)
# - Scope:
#     * Single folder
#     * Recursive (include subfolders)
# - Exact match behavior:
#     * If matching "Base name", compares the part before the dot ONLY.
#     * If matching "Full filename", compares the entire filename INCLUDING extension.
# ===============================================================

def browse_folder():
    folder_selected = filedialog.askdirectory(title="Select Folder to Process")
    if folder_selected:
        folder_path_var.set(folder_selected)

def browse_json_file():
    file_selected = filedialog.askopenfilename(
        title="Select JSON Mapping File",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )
    if file_selected:
        json_path_var.set(file_selected)

def unique_path(path):
    """Return a unique path by appending (1), (2), ... if needed."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while True:
        cand = f"{base} ({i}){ext}"
        if not os.path.exists(cand):
            return cand
        i += 1

def rename_files():
    folder = folder_path_var.get()
    json_file = json_path_var.get()
    mode = mode_var.get()                 # "key" or "value"
    recursive = recursive_var.get()       # bool
    match_target = match_var.get()        # "basename" or "full"

    # Validate inputs
    if not folder or not json_file:
        messagebox.showerror("Error", "Please select both a folder and a JSON mapping file.")
        return

    # Load JSON mapping
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read JSON file:\n{e}")
        return

    if not isinstance(mapping, dict):
        messagebox.showerror("Error", "JSON must be an object with key:value pairs.")
        return

    # Prepare lookup dict depending on mode (for O(1) exact matches)
    if mode == "key":
        lookup = mapping  # find filename part in keys → rename to value
    else:
        # invert mapping: value -> key
        try:
            lookup = {v: k for k, v in mapping.items()}
        except TypeError:
            messagebox.showerror("Error", "JSON must contain only string keys and values.")
            return

    # Choose walker
    try:
        if recursive:
            walker = os.walk(folder)
        else:
            walker = [(folder, [], os.listdir(folder))]
    except FileNotFoundError:
        messagebox.showerror("Error", "Selected folder was not found.")
        return

    renamed = 0
    skipped_existing = 0
    errors = 0

    for root, dirs, files in walker:
        for filename in files:
            try:
                if match_target == "basename":
                    base, ext = os.path.splitext(filename)
                    target = base  # exact match against base name only
                else:
                    target = filename  # exact match against full filename (with ext)

                if target in lookup:
                    replacement = lookup[target]
                    if match_target == "basename":
                        new_name = f"{replacement}{os.path.splitext(filename)[1]}"
                    else:
                        new_name = replacement

                    old_path = os.path.join(root, filename)
                    new_path = os.path.join(root, new_name)

                    # Avoid collisions by generating a unique path
                    if os.path.exists(new_path):
                        new_path = unique_path(new_path)
                        skipped_existing += 1  # counted as collision handled

                    os.rename(old_path, new_path)
                    renamed += 1
            except Exception:
                errors += 1

    summary = (
        f"Renamed files: {renamed}\n"
        f"Collisions auto-resolved: {skipped_existing}\n"
        f"Errors: {errors}"
    )
    messagebox.showinfo("Done", summary)

# ========================= GUI SETUP ===========================
root = tk.Tk()
root.title("JSON Key–Value Filename Replacer (Exact Match)")
root.geometry("700x500")
root.resizable(False, False)

style = ttk.Style(root)
style.configure("TLabel", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10))

# Variables
folder_path_var = tk.StringVar()
json_path_var = tk.StringVar()
mode_var = tk.StringVar(value="key")       # "key" or "value"
recursive_var = tk.BooleanVar(value=True)  # scan subfolders
match_var = tk.StringVar(value="basename") # "basename" or "full"

# Layout
frame = ttk.Frame(root, padding=15)
frame.pack(fill="both", expand=True)

# Folder
ttk.Label(frame, text="Select Folder to Scan:").grid(row=0, column=0, sticky="w")
ttk.Entry(frame, textvariable=folder_path_var, width=60).grid(row=0, column=1, padx=5)
ttk.Button(frame, text="Browse", command=browse_folder).grid(row=0, column=2)

# JSON file
ttk.Label(frame, text="Select JSON Mapping File:").grid(row=1, column=0, sticky="w", pady=8)
ttk.Entry(frame, textvariable=json_path_var, width=60).grid(row=1, column=1, padx=5)
ttk.Button(frame, text="Browse", command=browse_json_file).grid(row=1, column=2)

# Mode (keys/values)
ttk.Label(frame, text="Scan Mode:").grid(row=2, column=0, sticky="w", pady=8)
mode_frame = ttk.Frame(frame)
mode_frame.grid(row=2, column=1, sticky="w", padx=0)
ttk.Radiobutton(mode_frame, text="Scan for Keys (rename key → value)", variable=mode_var, value="key").pack(anchor="w")
ttk.Radiobutton(mode_frame, text="Scan for Values (rename value → key)", variable=mode_var, value="value").pack(anchor="w")

# Match target
ttk.Label(frame, text="Match Target:").grid(row=3, column=0, sticky="w", pady=8)
match_frame = ttk.Frame(frame)
match_frame.grid(row=3, column=1, sticky="w", padx=0)
ttk.Radiobutton(match_frame, text="Base name only (no extension)", variable=match_var, value="basename").pack(anchor="w")
ttk.Radiobutton(match_frame, text="Full filename (with extension)", variable=match_var, value="full").pack(anchor="w")

# Recursive
ttk.Checkbutton(frame, text="Scan Recursively (include subfolders)", variable=recursive_var).grid(row=4, column=1, sticky="w", pady=8)

# Example box
example = (
    "Example JSON:\n"
    '{\n'
    '  "cat": "dog",\n'
    '  "apple": "banana"\n'
    '}\n\n'
    "• With Match Target = Base name:\n"
    "    cat.png  → dog.png\n"
    "    apple.jpg → banana.jpg\n"
    "• With Match Target = Full filename:\n"
    "    cat.png (key) must exist in JSON exactly as 'cat.png'\n"
)
example_box = tk.Text(frame, height=10, width=80, wrap="word", bg="#f7f7f7", relief="solid")
example_box.insert("1.0", example)
example_box.configure(state="disabled")
example_box.grid(row=5, column=0, columnspan=3, pady=10)

# Action
ttk.Button(frame, text="Start Renaming", command=rename_files).grid(row=6, column=1, pady=12)

# Footer
ttk.Label(
    frame,
    text="Exact match is enforced on the selected target (base name or full filename).",
    foreground="gray"
).grid(row=7, column=0, columnspan=3, pady=5)

root.mainloop()
