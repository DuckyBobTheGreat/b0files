import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ===============================================================
# Batch Filename Replacer GUI Tool
# ---------------------------------------------------------------
# This script creates a simple desktop application that lets users:
#   1. Choose a folder to scan recursively.
#   2. Find all filenames containing a specific string.
#   3. Replace that string with another string.
#   4. Optionally save a key file (filenamekey.json) that maps
#      old filenames to new filenames for easy reversion later.
# ===============================================================


# ---------- Folder Browsing Functions ----------

def browse_folder():
    """Open a dialog to select the input folder to process."""
    folder_selected = filedialog.askdirectory(title="Select Folder to Process")
    if folder_selected:
        folder_path_var.set(folder_selected)


def browse_output_folder():
    """Open a dialog to select the output folder to save the key JSON file."""
    folder_selected = filedialog.askdirectory(title="Select Folder to Save Key File")
    if folder_selected:
        output_folder_var.set(folder_selected)


# ---------- Core Rename Logic ----------

def rename_files():
    """
    Scan through the selected folder recursively and rename all files
    containing the target substring. Also optionally generate a JSON key file
    to record all renames for potential reversal later.
    """
    folder = folder_path_var.get()
    output_folder = output_folder_var.get()
    find_str = find_var.get()
    replace_str = replace_var.get()

    # Validate required inputs
    if not folder or not find_str or not replace_str:
        messagebox.showerror("Error", "Please select a folder and enter both strings.")
        return

    rename_map = {}   # Dictionary to hold {old_filename: new_filename} mappings
    count = 0         # Counter for renamed files

    # Walk through all files recursively in the chosen folder
    for root, dirs, files in os.walk(folder):
        for filename in files:
            # Check if the target substring is in the filename
            if find_str in filename:
                old_path = os.path.join(root, filename)
                new_filename = filename.replace(find_str, replace_str)
                new_path = os.path.join(root, new_filename)

                # Skip renaming if the new filename already exists
                if os.path.exists(new_path):
                    messagebox.showwarning("Warning", f"Skipping {new_filename} (already exists)")
                    continue

                # Rename the file
                os.rename(old_path, new_path)
                rename_map[filename] = new_filename
                count += 1

    # Save key file if output folder is provided
    if output_folder:
        key_file = os.path.join(output_folder, "filenamekey.json")
        key_data = rename_map.copy()
        key_data[find_str] = replace_str  # Also store the key pair used

        with open(key_file, "w", encoding="utf-8") as f:
            json.dump(key_data, f, indent=4, ensure_ascii=False)

        messagebox.showinfo("Done", f"Renamed {count} files.\nKey saved to:\n{key_file}")
    else:
        messagebox.showinfo("Done", f"Renamed {count} files (no key file saved).")


# ---------- GUI SETUP ----------

root = tk.Tk()
root.title("Batch Filename Replacer")
root.geometry("600x320")
root.resizable(False, False)

# Apply some visual style to labels and buttons
style = ttk.Style(root)
style.configure("TLabel", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10))

# Tkinter StringVars to hold form field data
folder_path_var = tk.StringVar()   # Folder to scan
output_folder_var = tk.StringVar() # Folder to save key file
find_var = tk.StringVar()          # Substring to find
replace_var = tk.StringVar()       # Replacement string

# Create the main layout frame
frame = ttk.Frame(root, padding=15)
frame.pack(fill="both", expand=True)

# --- Row 0: Folder to Scan ---
ttk.Label(frame, text="Select Folder to Scan:").grid(row=0, column=0, sticky="w")
ttk.Entry(frame, textvariable=folder_path_var, width=50).grid(row=0, column=1, padx=5)
ttk.Button(frame, text="Browse", command=browse_folder).grid(row=0, column=2)

# --- Row 1: String to Find ---
ttk.Label(frame, text="String to Find:").grid(row=1, column=0, sticky="w", pady=10)
ttk.Entry(frame, textvariable=find_var, width=50).grid(row=1, column=1, padx=5)

# --- Row 2: Replacement String ---
ttk.Label(frame, text="Replace With:").grid(row=2, column=0, sticky="w")
ttk.Entry(frame, textvariable=replace_var, width=50).grid(row=2, column=1, padx=5)

# --- Row 3: Output Folder for Key File ---
ttk.Label(frame, text="Output Folder for Key File:").grid(row=3, column=0, sticky="w", pady=10)
ttk.Entry(frame, textvariable=output_folder_var, width=50).grid(row=3, column=1, padx=5)
ttk.Button(frame, text="Browse", command=browse_output_folder).grid(row=3, column=2)

# --- Row 4: Action Button ---
ttk.Button(frame, text="Start Renaming", command=rename_files).grid(row=4, column=1, pady=20)

# --- Row 5: Footer Note ---
ttk.Label(
    frame,
    text="Note: A filenamekey.json will be created for reversion tracking.",
    foreground="gray"
).grid(row=5, column=0, columnspan=3, pady=10)

# Launch the GUI event loop
root.mainloop()
