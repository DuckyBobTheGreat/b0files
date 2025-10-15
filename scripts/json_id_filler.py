import os
import json
import random
import string
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ===============================================================
# JSON Random Alphanumeric ID Filler (Unique IDs)
# ---------------------------------------------------------------
# Loads a JSON file like:
#   { "apple": "", "banana": "" }
# Fills all empty values with unique, randomly generated
# alphanumeric IDs (uppercase letters + digits).
#
# Options:
#   • Choose JSON file to process
#   • Choose where to save updated file
#   • Choose ID length
#   • Option to overwrite original file
#   • Guarantees all IDs are unique
# ===============================================================


def browse_input_file():
    """Select input JSON file."""
    file = filedialog.askopenfilename(
        title="Select JSON File to Process",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )
    if file:
        input_path_var.set(file)


def browse_output_file():
    """Select output path for updated JSON."""
    file = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        title="Save Updated JSON File As"
    )
    if file:
        output_path_var.set(file)


def generate_unique_id(length, used_ids):
    """Generate a unique alphanumeric ID not in used_ids."""
    chars = string.ascii_uppercase + string.digits
    while True:
        new_id = ''.join(random.choice(chars) for _ in range(length))
        if new_id not in used_ids:
            used_ids.add(new_id)
            return new_id


def process_json():
    """Fill empty values in JSON with unique random alphanumeric IDs."""
    input_file = input_path_var.get()
    output_file = output_path_var.get()
    id_length = id_length_var.get()
    overwrite = overwrite_var.get()

    if not input_file:
        messagebox.showerror("Error", "Please select a JSON input file.")
        return

    if not overwrite and not output_file:
        messagebox.showerror("Error", "Please select where to save the updated file.")
        return

    # Load JSON
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read JSON file:\n{e}")
        return

    if not isinstance(data, dict):
        messagebox.showerror("Error", "The JSON file must contain an object (key:value pairs).")
        return

    # Track used IDs (include any existing non-empty values to avoid collisions)
    used_ids = set(v for v in data.values() if isinstance(v, str) and v.strip())

    updated = 0
    for key in data:
        if data[key] == "":
            data[key] = generate_unique_id(id_length, used_ids)
            updated += 1

    if updated == 0:
        messagebox.showinfo("Done", "No empty values found — nothing to update.")
        return

    # Determine output file path
    save_path = input_file if overwrite else output_file or input_file.replace(".json", "_updated.json")

    # Save updated JSON
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        messagebox.showinfo(
            "Success",
            f"Updated {updated} entries with unique random IDs.\nSaved to:\n{save_path}"
        )
    except Exception as e:
        messagebox.showerror("Error", f"Failed to write JSON file:\n{e}")


# ---------- GUI SETUP ----------

root = tk.Tk()
root.title("JSON Random Unique ID Generator")
root.geometry("640x400")
root.resizable(False, False)

style = ttk.Style(root)
style.configure("TLabel", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10))

frame = ttk.Frame(root, padding=15)
frame.pack(fill="both", expand=True)

# Input file
ttk.Label(frame, text="Select JSON File to Process:").grid(row=0, column=0, sticky="w")
input_path_var = tk.StringVar()
ttk.Entry(frame, textvariable=input_path_var, width=50).grid(row=0, column=1, padx=5)
ttk.Button(frame, text="Browse", command=browse_input_file).grid(row=0, column=2)

# Output file
ttk.Label(frame, text="Output JSON File:").grid(row=1, column=0, sticky="w", pady=10)
output_path_var = tk.StringVar()
ttk.Entry(frame, textvariable=output_path_var, width=50).grid(row=1, column=1, padx=5)
ttk.Button(frame, text="Browse", command=browse_output_file).grid(row=1, column=2)

# Overwrite checkbox
overwrite_var = tk.BooleanVar(value=False)
ttk.Checkbutton(frame, text="Overwrite original file", variable=overwrite_var).grid(row=2, column=1, sticky="w")

# ID length selector
ttk.Label(frame, text="Random ID Length:").grid(row=3, column=0, sticky="w", pady=10)
id_length_var = tk.IntVar(value=6)
ttk.Spinbox(frame, from_=4, to=32, textvariable=id_length_var, width=5).grid(row=3, column=1, sticky="w")

# Example explanation
example_text = (
    "Example:\n"
    "Input JSON:\n"
    "{\n  \"apple\": \"\",\n  \"banana\": \"\"\n}\n\n"
    "Output (length 6):\n"
    "{\n  \"apple\": \"A9D4QZ\",\n  \"banana\": \"P7K1TB\"\n}\n\n"
    "All generated IDs are guaranteed unique."
)
example_box = tk.Text(frame, height=10, width=70, wrap="word", bg="#f7f7f7", relief="solid")
example_box.insert("1.0", example_text)
example_box.configure(state="disabled")
example_box.grid(row=4, column=0, columnspan=3, pady=10)

# Run button
ttk.Button(frame, text="Generate Unique Random IDs", command=process_json).grid(row=5, column=1, pady=10)

# Footer
ttk.Label(frame, text="This fills all blank JSON values with unique random alphanumeric IDs.", foreground="gray").grid(row=6, column=0, columnspan=3, pady=5)

root.mainloop()
