import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ===============================================================
# JSON Key-Value Filename Generator (with Merge Option)
# ---------------------------------------------------------------
# This script scans selected folders for all filenames
# and creates a JSON file mapping either:
#   { "filename": "" }   ← if Position = Key (pos 0)
# or { "": "filename" }  ← if Position = Value (pos 1)
#
# Options:
#  • Add multiple folders to scan
#  • Scan recursively (include subfolders)
#  • Include or exclude extensions
#  • Merge new results with an existing JSON mapping
# ===============================================================


# ---------- Functions ----------

def add_folder():
    """Add a folder to the list of scan targets."""
    folder = filedialog.askdirectory(title="Select Folder to Scan")
    if folder and folder not in folder_listbox.get(0, tk.END):
        folder_listbox.insert(tk.END, folder)


def remove_selected_folder():
    """Remove selected folder(s) from listbox."""
    selected = list(folder_listbox.curselection())
    for i in reversed(selected):
        folder_listbox.delete(i)


def clear_folders():
    """Clear all folder entries."""
    folder_listbox.delete(0, tk.END)


def browse_output():
    """Select where to save the JSON mapping file."""
    file = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        title="Save Mapping File As"
    )
    if file:
        output_path_var.set(file)


def browse_merge_file():
    """Select an existing JSON file to merge with."""
    file = filedialog.askopenfilename(
        title="Select Existing JSON File to Merge With",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )
    if file:
        merge_path_var.set(file)
        merge_var.set(True)


def scan_and_generate():
    """Scan selected folders and generate (or merge) JSON mapping."""
    folders = folder_listbox.get(0, tk.END)
    include_ext = include_ext_var.get()
    recursive = recursive_var.get()
    pos = pos_var.get()  # "key" or "value"
    output_file = output_path_var.get()
    merge_enabled = merge_var.get()
    merge_path = merge_path_var.get()

    if not folders:
        messagebox.showerror("Error", "Please add at least one folder to scan.")
        return
    if not output_file:
        messagebox.showerror("Error", "Please select where to save the JSON file.")
        return

    all_names = set()

    # --- Scan folders ---
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        walker = os.walk(folder) if recursive else [(folder, [], os.listdir(folder))]
        for root, dirs, files in walker:
            for name in files:
                name_entry = name if include_ext else os.path.splitext(name)[0]
                all_names.add(name_entry)

    if not all_names:
        messagebox.showwarning("Warning", "No files found in the selected folders.")
        return

    # --- Build mapping ---
    if pos == "key":
        mapping = {name: "" for name in sorted(all_names)}
    else:  # pos == "value"
        mapping = {"": name for name in sorted(all_names)}

    # --- Merge logic ---
    if merge_enabled and merge_path:
        try:
            if os.path.exists(merge_path):
                with open(merge_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    if not isinstance(existing, dict):
                        messagebox.showerror("Error", "Merge file must be a valid JSON object.")
                        return
            else:
                existing = {}
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read merge file:\n{e}")
            return

        # Merge intelligently
        for k, v in mapping.items():
            if k not in existing and v not in existing.values():
                existing[k] = v
        mapping = existing

    # --- Write JSON ---
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Success", f"JSON mapping saved to:\n{output_file}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to write JSON file:\n{e}")


# ---------- GUI SETUP ----------

root = tk.Tk()
root.title("Folder Scanner → JSON Key-Value Generator (Merge Capable)")
root.geometry("800x720")
root.resizable(False, False)

style = ttk.Style(root)
style.configure("TLabel", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10))

frame = ttk.Frame(root, padding=15)
frame.pack(fill="both", expand=True)

# Folder selection controls
ttk.Label(frame, text="Folders to Scan:").grid(row=0, column=0, sticky="w")
folder_listbox = tk.Listbox(frame, height=6, width=70, selectmode=tk.EXTENDED)
folder_listbox.grid(row=1, column=0, columnspan=3, pady=5, sticky="we")

ttk.Button(frame, text="Add Folder", command=add_folder).grid(row=2, column=0, sticky="w", pady=5)
ttk.Button(frame, text="Remove Selected", command=remove_selected_folder).grid(row=2, column=1, sticky="w", pady=5)
ttk.Button(frame, text="Clear All", command=clear_folders).grid(row=2, column=2, sticky="w", pady=5)

# Options
include_ext_var = tk.BooleanVar(value=True)
recursive_var = tk.BooleanVar(value=True)
pos_var = tk.StringVar(value="key")

ttk.Checkbutton(frame, text="Include file extensions", variable=include_ext_var).grid(row=3, column=0, sticky="w", pady=5)
ttk.Checkbutton(frame, text="Scan recursively (include subfolders)", variable=recursive_var).grid(row=3, column=1, sticky="w", pady=5)

# Position choice
ttk.Label(frame, text="Where to put scanned filenames:").grid(row=4, column=0, sticky="w", pady=(10, 0))
pos_frame = ttk.Frame(frame)
pos_frame.grid(row=5, column=0, columnspan=3, sticky="w", pady=5)
ttk.Radiobutton(pos_frame, text="Keys (pos 0) → { 'filename': '' }", variable=pos_var, value="key").pack(anchor="w")
ttk.Radiobutton(pos_frame, text="Values (pos 1) → { '': 'filename' }", variable=pos_var, value="value").pack(anchor="w")

# ---------- Output File ----------
ttk.Label(frame, text="Output JSON File:").grid(row=6, column=0, sticky="w", pady=10)

output_path_var = tk.StringVar()
ttk.Entry(frame, textvariable=output_path_var, width=60).grid(row=6, column=1, padx=5)
ttk.Button(frame, text="Browse", command=browse_output).grid(row=6, column=2, padx=5)

# ---------- Merge Option ----------
merge_var = tk.BooleanVar(value=False)
merge_path_var = tk.StringVar()

ttk.Checkbutton(frame, text="Merge with existing JSON file", variable=merge_var).grid(row=7, column=0, sticky="w", pady=5)
ttk.Entry(frame, textvariable=merge_path_var, width=60).grid(row=7, column=1, padx=5)
ttk.Button(frame, text="Browse", command=browse_merge_file).grid(row=7, column=2, padx=5)

# ---------- Example Info ----------
example_text = (
    "Example Output:\n\n"
    "If Position = Keys (pos 0):\n"
    "{\n  \"cat\": \"\",\n  \"apple\": \"\"\n}\n\n"
    "If Position = Values (pos 1):\n"
    "{\n  \"\": \"cat\",\n  \"\": \"apple\"\n}\n\n"
    "Options explained:\n"
    "• 'Include file extensions' → keep .png, .jpg, etc.\n"
    "• 'Scan recursively' → include all subfolders\n"
    "• 'Merge with existing JSON' → keep previous entries, add new ones."
)
example_box = tk.Text(frame, height=12, width=85, wrap="word", bg="#f7f7f7", relief="solid")
example_box.insert("1.0", example_text)
example_box.configure(state="disabled")
example_box.grid(row=8, column=0, columnspan=3, pady=10)

# ---------- Generate Button ----------
ttk.Button(
    frame,
    text="Start Scanning and Generate JSON File",
    command=scan_and_generate
).grid(row=9, column=1, pady=15, sticky="n")

# ---------- Footer ----------
ttk.Label(
    frame,
    text="Tip: Use this to prepare rename maps for the renamer script.",
    foreground="gray"
).grid(row=10, column=0, columnspan=3, pady=5)

root.mainloop()
