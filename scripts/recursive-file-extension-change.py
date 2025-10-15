import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext

# === Common extensions list ===
COMMON_EXTENSIONS = [
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
    ".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv",
    ".mp3", ".wav", ".ogg", ".flac",
    ".txt", ".doc", ".docx", ".pdf", ".csv", ".json", ".xml",
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".exe", ".dll", ".py", ".js", ".html", ".css"
]

def browse_folder(listbox, folder_list):
    folder = filedialog.askdirectory()
    if folder and folder not in folder_list:
        folder_list.append(folder)
        listbox.insert(tk.END, folder)

def remove_folder(listbox, folder_list):
    selected = listbox.curselection()
    for index in reversed(selected):
        folder_list.pop(index)
        listbox.delete(index)

def add_mapping():
    src_ext = src_entry.get().strip().lower()
    dst_ext = dst_entry.get().strip().lower()
    if not src_ext.startswith("."): src_ext = "." + src_ext
    if not dst_ext.startswith("."): dst_ext = "." + dst_ext
    if src_ext and dst_ext:
        ext_mappings[src_ext] = dst_ext
        mapping_box.insert(tk.END, f"{src_ext} → {dst_ext}")
        src_entry.set("")
        dst_entry.set("")

def remove_mapping():
    selected = mapping_box.curselection()
    for index in reversed(selected):
        key = list(ext_mappings.keys())[index]
        ext_mappings.pop(key)
        mapping_box.delete(index)

def select_key_dest():
    folder = filedialog.askdirectory()
    if folder:
        key_dest_var.set(folder)

def log_message(panel, msg):
    panel.config(state="normal")
    panel.insert(tk.END, msg + "\n")
    panel.see(tk.END)
    panel.config(state="disabled")

def convert_files():
    results_box_encode.config(state="normal")
    results_box_encode.delete(1.0, tk.END)
    results_box_encode.config(state="disabled")

    if not folder_list_encode or not ext_mappings:
        messagebox.showwarning("Warning", "Add at least one folder and one mapping.")
        return

    key_map = {}
    count = 0
    for folder in folder_list_encode:
        for root, _, files in os.walk(folder):
            for f in files:
                name, ext = os.path.splitext(f)
                if ext.lower() in ext_mappings:
                    old_path = os.path.join(root, f)
                    new_path = os.path.join(root, name + ext_mappings[ext])
                    try:
                        os.rename(old_path, new_path)
                        key_map[new_path] = old_path
                        count += 1
                        log_message(results_box_encode, f"Renamed: {old_path} → {new_path}")
                    except Exception as e:
                        log_message(results_box_encode, f"Error renaming {old_path}: {e}")

    if key_map:
        dest_folder = key_dest_var.get() or os.getcwd()
        key_path = os.path.join(dest_folder, "key.json")
        with open(key_path, "w", encoding="utf-8") as fp:
            json.dump(key_map, fp, indent=2, ensure_ascii=False)
        messagebox.showinfo("Done", f"Converted {count} files.\nkey.json saved to:\n{key_path}")
        log_message(results_box_encode, f"\n✅ Completed. {count} files converted.\nKey saved: {key_path}")
    else:
        messagebox.showinfo("No matches", "No matching files found.")
        log_message(results_box_encode, "No matching files found.")

def select_decode_folder():
    folder = filedialog.askdirectory()
    if folder:
        decode_folder_var.set(folder)

def select_key_file():
    file = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if file:
        decode_key_var.set(file)

def decode_files():
    results_box_decode.config(state="normal")
    results_box_decode.delete(1.0, tk.END)
    results_box_decode.config(state="disabled")

    folder = decode_folder_var.get()
    key_file = decode_key_var.get()

    if not folder or not key_file:
        messagebox.showwarning("Warning", "Select both a target folder and a key.json file.")
        return

    try:
        with open(key_file, "r", encoding="utf-8") as fp:
            key_map = json.load(fp)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read key.json: {e}")
        return

    restored = 0
    for new_path, old_path in key_map.items():
        if new_path.startswith(folder) and os.path.exists(new_path):
            try:
                os.rename(new_path, old_path)
                restored += 1
                log_message(results_box_decode, f"Restored: {new_path} → {old_path}")
            except Exception as e:
                log_message(results_box_decode, f"Error restoring {new_path}: {e}")

    log_message(results_box_decode, f"\n✅ Completed. {restored} files restored.")
    messagebox.showinfo("Decode complete", f"Restored {restored} files.")

# === MAIN WINDOW ===
root = tk.Tk()
root.title("File Extension Encoder / Decoder")
root.geometry("800x600")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

# === ENCODE PANEL ===
encode_frame = ttk.Frame(notebook)
notebook.add(encode_frame, text="Encode")

folder_list_encode = []
ext_mappings = {}
key_dest_var = tk.StringVar()

# Folder controls
tk.Label(encode_frame, text="Target Folders:").pack(anchor="w", padx=10, pady=(10,0))
folder_box = tk.Listbox(encode_frame, height=6)
folder_box.pack(fill="x", padx=10)
tk.Button(encode_frame, text="Add Folder", command=lambda: browse_folder(folder_box, folder_list_encode)).pack(pady=2)
tk.Button(encode_frame, text="Remove Selected", command=lambda: remove_folder(folder_box, folder_list_encode)).pack(pady=2)

# Extension mappings
tk.Label(encode_frame, text="Extension Mappings (from → to):").pack(anchor="w", padx=10, pady=(10,0))
mapping_box = tk.Listbox(encode_frame, height=6)
mapping_box.pack(fill="x", padx=10)

frm = tk.Frame(encode_frame)
frm.pack(pady=4)

tk.Label(frm, text="From:").grid(row=0, column=0, padx=5)
src_entry = tk.StringVar()
src_combo = ttk.Combobox(frm, textvariable=src_entry, values=COMMON_EXTENSIONS, width=10)
src_combo.grid(row=0, column=1)

tk.Label(frm, text="To:").grid(row=0, column=2, padx=5)
dst_entry = tk.StringVar()
dst_combo = ttk.Combobox(frm, textvariable=dst_entry, values=COMMON_EXTENSIONS, width=10)
dst_combo.grid(row=0, column=3)

tk.Button(frm, text="Add Pair", command=add_mapping).grid(row=0, column=4, padx=5)
tk.Button(frm, text="Remove Selected", command=remove_mapping).grid(row=0, column=5, padx=5)

# Destination folder for key.json
tk.Label(encode_frame, text="Destination Folder for key.json:").pack(anchor="w", padx=10, pady=(10,0))
tk.Entry(encode_frame, textvariable=key_dest_var).pack(fill="x", padx=10)
tk.Button(encode_frame, text="Select Folder", command=select_key_dest).pack(pady=2)

# Convert button
tk.Button(encode_frame, text="Convert Files", width=20, command=convert_files).pack(pady=10)

# Results panel
tk.Label(encode_frame, text="Results:").pack(anchor="w", padx=10)
results_box_encode = scrolledtext.ScrolledText(encode_frame, height=10, state="disabled")
results_box_encode.pack(fill="both", expand=True, padx=10, pady=5)

# === DECODE PANEL ===
decode_frame = ttk.Frame(notebook)
notebook.add(decode_frame, text="Decode")

decode_folder_var = tk.StringVar()
decode_key_var = tk.StringVar()

tk.Label(decode_frame, text="Target Folder to Decode:").pack(anchor="w", padx=10, pady=(10,0))
tk.Entry(decode_frame, textvariable=decode_folder_var).pack(fill="x", padx=10)
tk.Button(decode_frame, text="Select Folder", command=select_decode_folder).pack(pady=2)

tk.Label(decode_frame, text="Key File (key.json):").pack(anchor="w", padx=10, pady=(10,0))
tk.Entry(decode_frame, textvariable=decode_key_var).pack(fill="x", padx=10)
tk.Button(decode_frame, text="Select key.json", command=select_key_file).pack(pady=2)

tk.Button(decode_frame, text="Decode Files", width=20, command=decode_files).pack(pady=10)

tk.Label(decode_frame, text="Results:").pack(anchor="w", padx=10)
results_box_decode = scrolledtext.ScrolledText(decode_frame, height=15, state="disabled")
results_box_decode.pack(fill="both", expand=True, padx=10, pady=5)

root.mainloop()
