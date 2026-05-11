import tkinter as tk
from tkinter import Frame, ttk

class SearchableTable(Frame):
    def __init__(self, parent, columns, load_function, on_double_click=None, width=800, height=500):
        super().__init__(parent, bg="lightBlue1")

        self.columns = columns
        self.load_function = load_function
        self.on_double_click = on_double_click
        
        # Table frame
        table_frame = Frame(self)
        table_frame.place(relx=0.5, y=60, width=width, height=height, anchor='n')


        # Search bar
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(self, textvariable=self.search_var, width=40)
        search_entry.place(x=50, y=20)

        # Scrollbars
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical")
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal")

        # Treeview
        self.table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )
        self.table.place(relx=0.5, y=60, anchor='n')

        y_scroll.config(command=self.table.yview)
        x_scroll.config(command=self.table.xview)

        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        self.table.pack(fill="both", expand=True)

        # Column setup
        for col in columns:
            self.table.heading(col, text=col.capitalize())
            self.table.column(col, width=150)

        # Load data
        self.all_data = self.load_function()
        self.refresh_table(self.all_data)
        
        # Bind search
        self.search_var.trace("w", self.filter_data)
        self.table.bind("<Double-1>", self._handle_double_click)

    def _handle_double_click(self, event):
        if not self.on_double_click:
            return

        selected = self.table.focus()
        if not selected:
            return

        row_id = selected
        values = self.table.item(selected, "values")

        self.on_double_click(row_id, values)

    def refresh_table(self, data):
        
        for row in self.table.get_children():
            self.table.delete(row)

        for row in data:
            safe_row = [(value or "") for value in row[1:]]  # skip ID
            self.table.insert("", "end", iid=row[0], values=safe_row)

    def filter_data(self, *args):
        query = self.search_var.get().lower()
        filtered = []

        for row in self.all_data:
            _, *values = row
            values = [(v or "") for v in values]

            if any(query in str(v).lower() for v in values):
                filtered.append(row)

        self.refresh_table(filtered)
