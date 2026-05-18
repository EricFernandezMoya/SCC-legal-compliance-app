from legislation_update import apply_accepted_changes, fetch_pending_review, save_reviewer_decisions

import tkinter as tk
from tkinter import ttk, messagebox


def openReviewWindow(review_data, review_id, reviewed_by, save_reviewer_decisions, on_complete_callback):
    """
    review_data: dict containing the full review outcome (including proposed_changes)
    review_id: ID of the review row in DB
    reviewed_by: username or user_id
    save_reviewer_decisions: your backend function
    on_complete_callback: callback after saving decisions
    """

    win = tk.Toplevel()
    win.title("Review Proposed Rule Changes")
    win.geometry("900x700")
    win.grab_set()

    # Scrollable frame
    canvas = tk.Canvas(win)
    scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Store decisions here
    decisions = []

    # -------------------------
    # Edit popup window
    # -------------------------
    def open_edit_window(change, decision_record):
        edit_win = tk.Toplevel(win)
        edit_win.title("Edit Proposed Value")
        edit_win.geometry("600x500")
        edit_win.grab_set()

        text = tk.Text(edit_win, wrap="word")
        text.pack(fill="both", expand=True)

        # Load current text
        if change["type"] == "NEW_RULE":
            text.insert("1.0", change["proposed_rule"]["check"])
        else:
            text.insert("1.0", change["proposed_value"])

        def save_edit():
            new_text = text.get("1.0", "end").strip()
            decision_record["decision"] = "ACCEPT_WITH_EDITS"
            decision_record["edited_value"] = new_text
            edit_win.destroy()
            messagebox.showinfo("Saved", "Edits saved.")

        ttk.Button(edit_win, text="Save", command=save_edit).pack(pady=10)

    
    def set_status(status_var, status_label, text, color):
        status_var.set(text)
        status_label.config(foreground=color)

    def approve(dr, status_var, status_label):
        dr["decision"] = "ACCEPT"
        set_status(status_var, status_label, "Approved", "#059669")  # green
        messagebox.showinfo("Approved", "Rule approved.")

    def decline(dr, status_var, status_label):
        dr["decision"] = "DECLINE"
        set_status(status_var, status_label, "Declined", "#DC2626")  # red
        messagebox.showinfo("Declined", "Rule declined.")

    def edit_rule(change, dr, status_var, status_label):
        open_edit_window(change, dr)
        set_status(status_var, status_label, "Edited", "#D97706")  # orange
    # -------------------------
    # Build UI for each change
    # -------------------------
    for idx, change in enumerate(review_data["proposed_changes"], 1):

        # 1. Create the decision record FIRST
        decision_record = {
            "change": change,
            "decision": None,
            "edited_value": None
        }
        decisions.append(decision_record)

        # 2. Create the frame
        frame = ttk.LabelFrame(scroll_frame, text=f"Change {idx}", padding=10)
        frame.pack(fill="x", pady=10)

        status_var = tk.StringVar(value="Pending")
        status_label = ttk.Label(frame, textvariable=status_var, foreground="#6B7280")  # grey
        status_label.pack(anchor="w", pady=(0, 5))

        # 3. Wrapped labels (so text doesn’t overflow)
        def wrapped_label(parent, text):
            return ttk.Label(parent, text=text, wraplength=800, justify="left")

        wrapped_label(frame, f"Type: {change['type']}").pack(anchor="w")
        wrapped_label(frame, f"Reason:\n{change['reason']}").pack(anchor="w", pady=3)

        if change["type"] == "NEW_RULE":
            rule = change["proposed_rule"]
            wrapped_label(frame, f"New Rule ID: {rule['id']}").pack(anchor="w")
            wrapped_label(frame, f"Check:\n{rule['check']}").pack(anchor="w", pady=3)

        elif change["type"] == "MODIFY_RULE":
            wrapped_label(frame, f"Rule ID: {change['rule_id']}").pack(anchor="w")
            wrapped_label(frame, f"Field: {change['field']}").pack(anchor="w")
            wrapped_label(frame, f"Current Value:\n{change['current_value']}").pack(anchor="w", pady=3)
            wrapped_label(frame, f"Proposed Value:\n{change['proposed_value']}").pack(anchor="w", pady=3)

        # 4. Buttons — NOW decision_record exists
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(anchor="e", pady=10)
        
        ttk.Button(
            btn_frame,
            text="Approve",
            command=lambda dr=decision_record, sv=status_var, sl=status_label: approve(dr, sv, sl)
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="Decline",
            command=lambda dr=decision_record, sv=status_var, sl=status_label: decline(dr, sv, sl)
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="Edit",
            command=lambda c=change, dr=decision_record, sv=status_var, sl=status_label: edit_rule(c, dr, sv, sl)
        ).pack(side="left", padx=5)
    # -------------------------
    # Finalize button
    # -------------------------
    def finalize():
        # Ensure all decisions made
        incomplete = [d for d in decisions if d["decision"] is None]
        if incomplete:
            messagebox.showwarning("Incomplete", "You must approve, decline, or edit all rules.")
            return

        # Save to DB
        save_reviewer_decisions(review_id, decisions, reviewed_by)

        confirm = messagebox.askyesno(
                "Confirm Save",
                "Are you sure you want to save this changes?",
            )
        if not confirm:
            return

        apply_accepted_changes(review_id, reviewed_by)

        win.grab_release()
        win.destroy()

        on_complete_callback()

    ttk.Button(scroll_frame, text="Finalize Review", command=finalize).pack(pady=20)

    return win
