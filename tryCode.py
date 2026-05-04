import tkinter as tk

def on_search(event=None):
    query = search_var.get().lower()
    results_listbox.delete(0, tk.END)

    for item in data:
        if query in item.lower():
            results_listbox.insert(tk.END, item)

def on_select(event):
    selection = results_listbox.curselection()
    if not selection:
        return

    value = results_listbox.get(selection[0])
    print("Selected:", value)

root = tk.Tk()

data = [
    "Contract A",
    "Contract B",
    "Legal Document 2020",
    "Privacy Act 1988",
    "Work Health and Safety Regulation",
    "Environmental Protection Act"
]

search_var = tk.StringVar()

search_entry = tk.Entry(root, textvariable=search_var, width=40)
search_entry.pack(pady=5)
search_entry.bind("<KeyRelease>", on_search)

results_listbox = tk.Listbox(root, width=40, height=6)
results_listbox.pack()

results_listbox.bind("<<ListboxSelect>>", on_select)

root.mainloop()
