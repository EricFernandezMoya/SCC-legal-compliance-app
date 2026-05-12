"""
SCC Compliance Tool — CustomTkinter UI
Sunshine Coast Council branding: primary blue #005B8E, teal #00B5CC.
"""

import json
import os
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk
import requests

try:
    import pillow_avif  # noqa: F401  registers avif decoder
except ImportError:
    pass

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False

# ── Appearance ───────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── Brand palette ────────────────────────────────────────────────────────────
PRIMARY   = "#005B8E"
TEAL      = "#00B5CC"
BG        = "#F4F7FA"
CARD      = "#FFFFFF"
SIDEBAR   = "#FFFFFF"
BORDER    = "#E5E7EB"
SHADOW    = "#D4DCE8"
TXT       = "#1A1A2E"
TXT2      = "#6B7280"
SUCCESS   = "#22C55E"
WARNING   = "#F59E0B"
ERROR     = "#EF4444"
NAV_HOVER = "#EFF6FF"

# ── Rule categories (display order matches spec) ──────────────────────────────
_RULE_CATS = [
    ("CAT1", "C1 — Procurement & Governance"),
    ("CAT2", "C2 — Data & Privacy"),
    ("CAT3", "C3 — Cybersecurity"),
    ("CAT4", "C4 — Intellectual Property"),
    ("CAT5", "C5 — Service Levels & Exit"),
    ("CAT6", "C6 — Work Health & Safety"),
    ("CAT7", "C7 — Legal & Liability"),
]

# ── Paths ────────────────────────────────────────────────────────────────────
_BASE         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOGO_PATH    = os.path.join(os.path.dirname(_BASE), "sunshine-coast-council-vector-logo.png")
_SETTINGS_FILE   = os.path.join(_BASE, ".scc_settings.json")
_ARTIFACT_B_PATH = os.path.join(_BASE, "artifact_b.json")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_logo(target_w=200):
    try:
        from PIL import Image
        img = Image.open(_LOGO_PATH).convert("RGBA")
        orig_w, orig_h = img.size
        target_h = max(1, round(orig_h * target_w / orig_w))
        img = img.resize((target_w, target_h), Image.LANCZOS)
        return ctk.CTkImage(img, size=(target_w, target_h))
    except Exception:
        return None


def _load_settings():
    try:
        with open(_SETTINGS_FILE) as f:
            return json.load(f)
    except Exception:
        return {"api_url": "http://localhost:8000"}


def _save_settings(s):
    try:
        with open(_SETTINGS_FILE, "w") as f:
            json.dump(s, f)
    except Exception:
        pass


def _make_card(parent, padx=24, pady=24, **kw):
    """Return (shadow_frame, inner_white_frame).  Pack/grid the shadow_frame."""
    shadow = ctk.CTkFrame(parent, fg_color=SHADOW, corner_radius=14, **kw)
    inner  = ctk.CTkFrame(shadow, fg_color=CARD, corner_radius=12)
    inner.pack(fill="both", expand=True, padx=(2, 3), pady=(2, 3))
    return shadow, inner


def _section_title(parent, text, pady=(0, 20), padx=(32, 0)):
    ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(size=24, weight="bold"),
        text_color=TXT,
    ).pack(anchor="w", pady=pady, padx=padx)


def _label(parent, text, size=13, colour=TXT2, **kw):
    return ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(size=size),
        text_color=colour, **kw,
    )


def _entry(parent, placeholder="", width=300):
    return ctk.CTkEntry(
        parent, placeholder_text=placeholder,
        corner_radius=8, height=40, width=width,
        fg_color="white", border_color=BORDER, text_color=TXT,
    )


def _btn(parent, text, command, fg=PRIMARY, hover=TEAL, width=None, height=40, **kw):
    kwargs = dict(
        text=text, corner_radius=8, height=height,
        fg_color=fg, hover_color=hover,
        text_color="white", font=ctk.CTkFont(size=14, weight="bold"),
        command=command,
    )
    if width:
        kwargs["width"] = width
    kwargs.update(kw)
    return ctk.CTkButton(parent, **kwargs)


def _ghost_btn(parent, text, command, height=36, **kw):
    return ctk.CTkButton(
        parent, text=text, corner_radius=8, height=height,
        fg_color="transparent", border_color=PRIMARY, border_width=2,
        hover_color=NAV_HOVER, text_color=PRIMARY,
        font=ctk.CTkFont(size=13),
        command=command, **kw,
    )


def _err_banner(parent):
    """Return (frame, label).  Frame is not packed by default."""
    frame = ctk.CTkFrame(parent, fg_color="#FEF2F2", corner_radius=8)
    lbl   = ctk.CTkLabel(frame, text="", text_color=ERROR,
                         font=ctk.CTkFont(size=13), wraplength=720, justify="left")
    lbl.pack(padx=16, pady=10)
    return frame, lbl


def _badge(parent, text, fg, bg):
    f = ctk.CTkFrame(parent, fg_color=bg, corner_radius=6)
    ctk.CTkLabel(f, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=fg).pack(padx=8, pady=3)
    return f


# ── Upload box widget ─────────────────────────────────────────────────────────

def _upload_box(parent, label_text, on_browse):
    """Dashed-border upload box.  Returns the filename label."""
    box = ctk.CTkFrame(parent, fg_color="#F8FAFC", corner_radius=8,
                       border_width=2, border_color=BORDER)
    box.pack(fill="x", pady=(0, 16))

    inner = ctk.CTkFrame(box, fg_color="transparent")
    inner.pack(padx=24, pady=20)

    _label(inner, "📂", size=32).pack()
    _label(inner, label_text).pack(pady=(4, 0))
    _label(inner, "PDF, DOC, DOCX supported", size=11).pack()

    file_lbl = _label(inner, "No file selected", size=12)
    file_lbl.pack(pady=(6, 8))

    _btn(inner, "Browse File", on_browse, height=36, width=140,
         font=ctk.CTkFont(size=13)).pack()

    return file_lbl


# ══════════════════════════════════════════════════════════════════════════════
# Main application class
# ══════════════════════════════════════════════════════════════════════════════

class SCCApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        if _DND_AVAILABLE:
            TkinterDnD._require(self)
        self.title("SCC Compliance Tool")
        self.geometry("1280x820")
        self.minsize(960, 640)
        self.configure(fg_color=BG)

        self._settings  = _load_settings()
        self._logo_img  = _load_logo()
        self._user      = "User"
        self._privilege = ""

        # per-page state
        self._analyse_files       = []
        self._leg_file            = None
        self._leg_review_id       = None
        self._leg_decisions       = []
        self._a_vendors_data      = []
        self._a_selected_group_id = None
        self._a_compare_var       = None   # BooleanVar, created in _build_analyse
        self._a_dropdown_win      = None
        self._a_doc_count         = 0

        # Reports page state
        self._r_vendors_data      = []
        self._r_all_vendor_names  = []
        self._r_selected_group_id = None

        self._build_login()

    # ── API shortcut ─────────────────────────────────────────────────────────
    def _api(self, method, path, cb_ok, cb_err, **kw):
        url = self._settings.get("api_url", "http://localhost:8000") + path
        def _run():
            try:
                r = requests.request(method, url, timeout=120, **kw)
                r.raise_for_status()
                self.after(0, lambda: cb_ok(r.json()))
            except Exception as e:
                self.after(0, lambda: cb_err(str(e)))
        threading.Thread(target=_run, daemon=True).start()

    # ═════════════════════════════════════════════════════════════════════════
    # LOGIN
    # ═════════════════════════════════════════════════════════════════════════

    def _build_login(self):
        self._login_page = ctk.CTkFrame(self, fg_color=BG)
        self._login_page.place(relx=0, rely=0, relwidth=1, relheight=1)

        wrap = ctk.CTkFrame(self._login_page, fg_color=BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        # logo
        if self._logo_img:
            ctk.CTkLabel(wrap, image=self._logo_img, text="",
                         fg_color=BG).pack(pady=(0, 12))

        # title
        ctk.CTkLabel(wrap, text="Software Compliance Tool",
                     font=ctk.CTkFont(size=28, weight="bold"),
                     text_color="#000000").pack(pady=(0, 28))

        sh, card_f = _make_card(wrap)
        sh.pack()

        f = ctk.CTkFrame(card_f, fg_color=CARD, width=340)
        f.pack(fill="both", padx=36, pady=36)

        ctk.CTkLabel(f, text="Sign in",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=TXT).pack(anchor="w", pady=(0, 24))

        _label(f, "Username").pack(anchor="w")
        self._li_user = _entry(f, "Enter username", width=320)
        self._li_user.pack(anchor="w", pady=(4, 16))

        _label(f, "Password").pack(anchor="w")
        self._li_pass = ctk.CTkEntry(f, placeholder_text="Enter password",
                                     corner_radius=8, height=40, width=320, show="•",
                                     fg_color="white", border_color=BORDER, text_color=TXT)
        self._li_pass.pack(anchor="w", pady=(4, 8))

        self._li_err, self._li_err_lbl = _err_banner(f)
        # not packed yet

        _btn(f, "Sign in", self._do_login, height=44, width=320).pack(pady=(16, 0))
        self._li_pass.bind("<Return>", lambda _e: self._do_login())

    def _do_login(self):
        from database.database import selectUserByName
        from userHandling.userHandling import userLogin

        u = self._li_user.get().strip()
        p = self._li_pass.get()

        if not u or not p:
            self._li_err_lbl.configure(text="Please enter username and password.")
            self._li_err.pack(fill="x", pady=(0, 0))
            return

        try:
            rows = selectUserByName(u)
            ok   = bool(rows) and userLogin(u, p)
        except Exception as e:
            self._li_err_lbl.configure(text=f"Database error: {e}")
            self._li_err.pack(fill="x", pady=(0, 0))
            return

        if not ok:
            self._li_err_lbl.configure(text="Invalid username or password.")
            self._li_err.pack(fill="x", pady=(0, 0))
            self._li_pass.delete(0, "end")
            return

        from database.database import selectPrivileges
        self._user = u
        privilege_id = rows[0][4]
        all_privs = selectPrivileges()
        self._privilege = next((r[1] for r in all_privs if r[0] == privilege_id), "")
        self._li_user.delete(0, "end")
        self._li_pass.delete(0, "end")
        self._li_err.pack_forget()
        self._login_page.place_forget()
        self._build_main()
        self._go("dashboard")

    # ═════════════════════════════════════════════════════════════════════════
    # MAIN LAYOUT
    # ═════════════════════════════════════════════════════════════════════════

    def _build_main(self):
        self._root_frame = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self._root_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._pages    = {}
        self._nav_btns = {}

        self._build_sidebar()

        self._content = ctk.CTkFrame(self._root_frame, fg_color=BG, corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        self._build_dashboard()
        self._build_analyse()
        self._build_reports()
        self._build_contracts()
        self._build_legislation()
        self._build_settings()

    # ── Sidebar ──────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self._root_frame, width=220, fg_color=SIDEBAR,
                          corner_radius=0)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        # right-edge shadow line
        ctk.CTkFrame(sb, width=1, fg_color="#D1D5DB", corner_radius=0).pack(
            side="right", fill="y"
        )

        col = ctk.CTkFrame(sb, fg_color=SIDEBAR, corner_radius=0)
        col.pack(side="left", fill="both", expand=True)

        # ── logo
        logo_area = ctk.CTkFrame(col, fg_color=SIDEBAR)
        logo_area.pack(fill="x", padx=18, pady=(24, 16))

        if self._logo_img:
            ctk.CTkLabel(logo_area, image=self._logo_img, text="",
                         fg_color=SIDEBAR).pack(anchor="w")
        else:
            ctk.CTkLabel(logo_area, text="SCC",
                         font=ctk.CTkFont(size=22, weight="bold"),
                         text_color=PRIMARY).pack(anchor="w")
            _label(logo_area, "Compliance Tool", size=11).pack(anchor="w")

        # divider
        ctk.CTkFrame(col, height=1, fg_color=BORDER, corner_radius=0).pack(
            fill="x", padx=16, pady=(0, 16)
        )

        # ── nav
        nav = ctk.CTkFrame(col, fg_color=SIDEBAR)
        nav.pack(fill="x", padx=8)

        is_admin = self._privilege == "ADMIN"
        items = [
            ("dashboard",   "Dashboard"),
            ("analyse",     "Analyse Contract"),
            ("reports",     "Reports"),
            ("contracts",   "Contracts"),
        ]
        if is_admin:
            items += [
                ("legislation", "Legislation Update"),
                ("settings",    "Settings"),
            ]
        for key, label in items:
            b = ctk.CTkButton(
                nav, text=label, anchor="w", height=44, corner_radius=8,
                fg_color="transparent", hover_color=NAV_HOVER,
                text_color=TXT, font=ctk.CTkFont(size=14),
                command=lambda k=key: self._go(k),
            )
            b.pack(fill="x", pady=2)
            self._nav_btns[key] = b

        # spacer
        ctk.CTkFrame(col, fg_color=SIDEBAR).pack(fill="both", expand=True)

        # ── user badge
        ub = ctk.CTkFrame(col, fg_color="#F3F4F6", corner_radius=10)
        ub.pack(fill="x", padx=12, pady=16)
        self._user_lbl = ctk.CTkLabel(ub, text=self._user,
                                      font=ctk.CTkFont(size=12, weight="bold"),
                                      text_color=TXT)
        self._user_lbl.pack(padx=14, pady=(10, 2), anchor="w")
        _label(ub, "Compliance Officer", size=11).pack(padx=14, pady=(0, 10), anchor="w")

    def _go(self, key):
        if key == "analyse":
            self._load_vendors()
        if key == "reports":
            self._load_report_vendors()
        if key == "contracts":
            self._load_contracts_directory()
        for k, b in self._nav_btns.items():
            if k == key:
                b.configure(fg_color=PRIMARY, text_color="white", hover_color=TEAL)
            else:
                b.configure(fg_color="transparent", text_color=TXT, hover_color=NAV_HOVER)

        for f in self._pages.values():
            f.pack_forget()
        self._pages[key].pack(fill="both", expand=True)
        self._user_lbl.configure(text=self._user)

    # ═════════════════════════════════════════════════════════════════════════
    # DASHBOARD
    # ═════════════════════════════════════════════════════════════════════════

    def _build_dashboard(self):
        page = ctk.CTkScrollableFrame(self._content, fg_color=BG, corner_radius=0)
        self._pages["dashboard"] = page

        p = 32  # padding

        # Welcome card ──────────────────────────────────────────────────────
        sh, wc = _make_card(page)
        sh.pack(fill="x", padx=p, pady=(p, 0))

        row = ctk.CTkFrame(wc, fg_color=CARD)
        row.pack(fill="both", padx=24, pady=24)

        ctk.CTkFrame(row, width=5, fg_color=PRIMARY, corner_radius=3).pack(
            side="left", fill="y", padx=(0, 18)
        )
        txt = ctk.CTkFrame(row, fg_color=CARD)
        txt.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(txt, text="Welcome to the SCC Compliance Tool",
                     font=ctk.CTkFont(size=20, weight="bold"), text_color=TXT
                     ).pack(anchor="w")
        _label(txt,
               "Analyse third-party contracts against approved rules derived from\n"
               "legislation and internal policies. Findings are factual — no severity "
               "judgements.",
               size=13, colour=TXT2).pack(anchor="w", pady=(6, 0))

        # Stat cards ─────────────────────────────────────────────────────────
        stats_outer = ctk.CTkFrame(page, fg_color=BG)
        stats_outer.pack(fill="x", padx=p, pady=(20, 0))
        for i in range(2):
            stats_outer.columnconfigure(i, weight=1)

        stat_defs = [
            ("📋", "Total Reports Run", "—", TXT),
            ("🗓",  "Last Analysis",     "—", TEAL),
        ]
        self._dash_lbl = {}
        for col, (icon, lbl, val, colour) in enumerate(stat_defs):
            sh2, sc = _make_card(stats_outer)
            sh2.grid(row=0, column=col, sticky="ew",
                     padx=(0, 16) if col < 1 else 0)
            inner = ctk.CTkFrame(sc, fg_color=CARD)
            inner.pack(fill="both", padx=20, pady=20)
            _label(inner, icon, size=30).pack(anchor="w")
            _label(inner, lbl, size=12).pack(anchor="w", pady=(4, 2))
            vl = ctk.CTkLabel(inner, text=val,
                              font=ctk.CTkFont(size=28, weight="bold"),
                              text_color=colour)
            vl.pack(anchor="w")
            self._dash_lbl[lbl] = vl

        # Quick actions ───────────────────────────────────────────────────────
        sh3, ac = _make_card(page)
        sh3.pack(fill="x", padx=p, pady=(20, p))

        inner3 = ctk.CTkFrame(ac, fg_color=CARD)
        inner3.pack(fill="both", padx=24, pady=24)

        ctk.CTkLabel(inner3, text="Quick Actions",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=TXT).pack(anchor="w", pady=(0, 14))

        qr = ctk.CTkFrame(inner3, fg_color=CARD)
        qr.pack(anchor="w")

        _btn(qr, "Analyse a Contract",
             lambda: self._go("analyse"), height=40).pack(side="left", padx=(0, 12))
        _ghost_btn(qr, "View Reports",
                   lambda: self._go("reports"), height=40).pack(side="left", padx=(0, 12))
        if self._privilege == "ADMIN":
            _ghost_btn(qr, "Legislation Update",
                       lambda: self._go("legislation"), height=40).pack(side="left")

    # ═════════════════════════════════════════════════════════════════════════
    # ANALYSE CONTRACT
    # ═════════════════════════════════════════════════════════════════════════

    def _build_analyse(self):
        page = ctk.CTkScrollableFrame(self._content, fg_color=BG, corner_radius=0)
        self._pages["analyse"] = page

        p = 32

        _section_title(page, "Analyse Contract", pady=(p, 16))
        page._pad = p

        # error banner
        self._a_err, self._a_err_lbl = _err_banner(page)

        # ── Input card
        sh, ic = _make_card(page)
        sh.pack(fill="x", padx=p, pady=(0, 20))
        form = ctk.CTkFrame(ic, fg_color=CARD)
        form.pack(fill="both", padx=24, pady=24)

        ctk.CTkLabel(form, text="Contract Details",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=TXT).pack(anchor="w", pady=(0, 16))

        # ── Vendor autocomplete
        ctk.CTkLabel(form, text="Vendor",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TXT).pack(anchor="w", pady=(0, 6))

        _label(form, "Vendor Name  (type to search existing or enter new)").pack(anchor="w", pady=(0, 4))
        self._a_vendor_entry = _entry(form, "e.g. Zoom", width=360)
        self._a_vendor_entry.pack(anchor="w", pady=(0, 20))
        self._a_vendor_entry.bind("<KeyRelease>", self._on_vendor_type)
        self._a_vendor_entry.bind("<FocusOut>",
                                  lambda _e: self.after(200, self._hide_vendor_dropdown))

        ctk.CTkFrame(form, height=1, fg_color=BORDER, corner_radius=0).pack(
            fill="x", pady=(0, 20)
        )

        # ── File upload (multi-file)
        drop_hint = "Drop files here or click Browse" if _DND_AVAILABLE else "Click Browse to select files"
        self._a_upload_box = ctk.CTkFrame(form, fg_color="#F8FAFC", corner_radius=8,
                                          border_width=2, border_color=BORDER)
        self._a_upload_box.pack(fill="x", pady=(0, 8))
        _ub_inner = ctk.CTkFrame(self._a_upload_box, fg_color="transparent")
        _ub_inner.pack(padx=24, pady=20)
        _label(_ub_inner, "📂", size=32).pack()
        _label(_ub_inner, drop_hint).pack(pady=(4, 0))
        _label(_ub_inner, "PDF, DOC, DOCX supported", size=11).pack()
        _btn(_ub_inner, "Browse Files", self._browse_contract,
             height=36, width=140, font=ctk.CTkFont(size=13)).pack(pady=(8, 0))
        if _DND_AVAILABLE:
            self._a_upload_box.drop_target_register(DND_FILES)
            self._a_upload_box.dnd_bind("<<Drop>>", self._on_contract_drop)

        # file list — one row per file, shown below the drop box
        self._a_file_list_frame = ctk.CTkFrame(form, fg_color=CARD)
        self._a_file_list_frame.pack(fill="x", pady=(0, 8))

        # ── URL input
        _label(form, "Or add document URLs", size=13).pack(anchor="w", pady=(0, 4))
        _label(form,
               "Paste one URL per line — the backend will fetch and extract text from each",
               size=11, colour=TXT2).pack(anchor="w", pady=(0, 6))
        self._a_urls_box = ctk.CTkTextbox(
            form, height=80, corner_radius=8,
            fg_color="white", border_width=1, border_color=BORDER,
            text_color=TXT, font=ctk.CTkFont(size=12),
        )
        self._a_urls_box.pack(fill="x", pady=(0, 20))
        self._a_urls_box.bind("<KeyRelease>", lambda _e: self._update_doc_count())

        ctk.CTkFrame(form, height=1, fg_color=BORDER, corner_radius=0).pack(
            fill="x", pady=(0, 20)
        )

        # ── Doc-count-conditional fields
        _doc_fields = ctk.CTkFrame(form, fg_color=CARD)
        _doc_fields.pack(fill="x")
        self._a_doc_fields_container = _doc_fields

        self._a_multi_doc_notice = ctk.CTkLabel(
            _doc_fields,
            text="Multi-document analysis — this will be saved as a vendor group report",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEAL, fg_color="#EFF9FB", corner_radius=8,
        )

        self._a_single_doc_frame = ctk.CTkFrame(_doc_fields, fg_color=CARD)
        self._a_single_doc_frame.pack(fill="x")   # shown by default

        _label(self._a_single_doc_frame, "Contract Name  *").pack(anchor="w", pady=(0, 4))
        self._a_contract_name = _entry(self._a_single_doc_frame,
                                       "e.g. Zoom Privacy Policy 2025", width=420)
        self._a_contract_name.pack(anchor="w", pady=(0, 16))

        dates_row = ctk.CTkFrame(self._a_single_doc_frame, fg_color=CARD)
        dates_row.pack(fill="x", pady=(0, 16))
        dates_row.columnconfigure(0, weight=1)
        dates_row.columnconfigure(1, weight=1)

        _label(dates_row, "Start Date  (optional, YYYY-MM-DD)").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        self._a_start_date = _entry(dates_row, "2025-01-01")
        self._a_start_date.grid(row=1, column=0, sticky="ew", padx=(0, 12))

        _label(dates_row, "End Date  (optional, YYYY-MM-DD)").grid(
            row=0, column=1, sticky="w", pady=(0, 4))
        self._a_end_date = _entry(dates_row, "2025-12-31")
        self._a_end_date.grid(row=1, column=1, sticky="ew")

        # ── Compare with previous report checkbox
        self._a_compare_var = ctk.BooleanVar(value=False)
        cmp_row = ctk.CTkFrame(form, fg_color=CARD)
        cmp_row.pack(anchor="w", pady=(0, 20))
        ctk.CTkCheckBox(
            cmp_row,
            text="Compare with previous report",
            variable=self._a_compare_var,
            checkbox_width=20, checkbox_height=20,
            corner_radius=4,
            fg_color=PRIMARY, hover_color=TEAL,
            font=ctk.CTkFont(size=13), text_color=TXT,
        ).pack(side="left")
        _label(cmp_row,
               "  — automatically finds the most recent report for this vendor",
               size=11, colour=TXT2).pack(side="left")

        # ── Run button
        br = ctk.CTkFrame(form, fg_color=CARD)
        br.pack(anchor="w")

        self._a_btn = _btn(br, "🔍  Run Analysis", self._run_analysis,
                           height=44, width=190)
        self._a_btn.pack(side="left")

        self._a_spin = _label(br, "  Analysing…", colour=TXT2)

        # ── Results section (hidden until analysis runs)
        self._a_results = ctk.CTkFrame(page, fg_color=BG, corner_radius=0)
        self._a_res_title = ctk.CTkLabel(
            self._a_results, text="",
            font=ctk.CTkFont(size=17, weight="bold"), text_color=TXT,
        )
        self._a_res_title.pack(anchor="w", padx=p, pady=(20, 12))
        self._a_warn_frame = ctk.CTkFrame(self._a_results, fg_color="#FEF3C7", corner_radius=8)
        self._a_findings = ctk.CTkFrame(self._a_results, fg_color=BG)
        self._a_findings.pack(fill="x", padx=p)

    def _browse_contract(self):
        paths = filedialog.askopenfilenames(
            title="Select contract files",
            filetypes=[("Documents", "*.pdf *.doc *.docx")],
        )
        if paths:
            self._add_contract_files(list(paths))

    def _on_contract_drop(self, event):
        paths = self._parse_dnd_paths(event.data)
        allowed = {".pdf", ".doc", ".docx"}
        paths = [p for p in paths if os.path.splitext(p)[1].lower() in allowed]
        if paths:
            self._add_contract_files(paths)

    @staticmethod
    def _parse_dnd_paths(data):
        """Parse tkdnd path string — handles brace-quoted paths with spaces."""
        result = []
        for token in re.findall(r'\{[^}]*\}|\S+', data):
            if token.startswith('{') and token.endswith('}'):
                result.append(token[1:-1])
            else:
                result.append(token)
        return result

    def _add_contract_files(self, paths):
        for p in paths:
            if p not in self._analyse_files:
                self._analyse_files.append(p)
        self._refresh_file_list_ui()
        self._update_doc_count()

    def _remove_contract_file(self, path):
        if path in self._analyse_files:
            self._analyse_files.remove(path)
        self._refresh_file_list_ui()
        self._update_doc_count()

    def _refresh_file_list_ui(self):
        for w in self._a_file_list_frame.winfo_children():
            w.destroy()
        for path in self._analyse_files:
            row = ctk.CTkFrame(self._a_file_list_frame, fg_color="#F0F4F8", corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)
            _label(row, os.path.basename(path), size=12, colour=TXT).pack(
                side="left", padx=(10, 4), pady=6, fill="x", expand=True)
            ctk.CTkButton(
                row, text="×", width=26, height=26, corner_radius=6,
                fg_color="transparent", hover_color=ERROR,
                text_color=TXT2, font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda p=path: self._remove_contract_file(p),
            ).pack(side="right", padx=(0, 4), pady=4)

    def _load_vendors(self):
        def _ok(data):
            self._a_vendors_data = data
        self._api("GET", "/vendors", _ok, lambda _: None)

    def _on_vendor_type(self, event=None):
        text = self._a_vendor_entry.get().strip()
        self._a_selected_group_id = None
        if len(text) < 2:
            self._hide_vendor_dropdown()
            return
        matches = [v["group_name"] for v in self._a_vendors_data
                   if text.lower() in v["group_name"].lower()]
        self._show_vendor_dropdown(matches)

    def _show_vendor_dropdown(self, matches):
        self._hide_vendor_dropdown()
        if not matches:
            return
        n   = min(len(matches), 6)
        e   = self._a_vendor_entry
        x   = e.winfo_rootx()
        y   = e.winfo_rooty() + e.winfo_height()
        w   = e.winfo_width()
        win = tk.Toplevel(self)
        win.overrideredirect(True)
        win.geometry(f"{w}x{n * 32}+{x}+{y}")
        win.configure(bg=CARD)
        win.lift()
        win.wm_attributes("-topmost", True)
        lb = tk.Listbox(
            win, bg=CARD, fg=TXT, font=("Helvetica", 13),
            selectbackground=PRIMARY, selectforeground="white",
            borderwidth=1, highlightthickness=0,
            activestyle="dotbox", relief="flat",
        )
        lb.pack(fill="both", expand=True)
        for name in matches[:6]:
            lb.insert("end", name)
        def _pick(evt=None):
            sel = lb.curselection()
            if not sel:
                return
            name = lb.get(sel[0])
            self._a_vendor_entry.delete(0, "end")
            self._a_vendor_entry.insert(0, name)
            for v in self._a_vendors_data:
                if v["group_name"] == name:
                    self._a_selected_group_id = v["group_id"]
                    break
            self._hide_vendor_dropdown()
        lb.bind("<ButtonRelease-1>", _pick)
        lb.bind("<Return>", _pick)
        self._a_dropdown_win = win

    def _hide_vendor_dropdown(self):
        if self._a_dropdown_win is not None:
            try:
                self._a_dropdown_win.destroy()
            except Exception:
                pass
            self._a_dropdown_win = None

    def _update_doc_count(self):
        file_count = len(self._analyse_files)
        urls_text  = self._a_urls_box.get("0.0", "end-1c").strip()
        url_count  = len([u for u in urls_text.splitlines() if u.strip()])
        self._a_doc_count = file_count + url_count
        if self._a_doc_count > 1:
            self._a_single_doc_frame.pack_forget()
            self._a_multi_doc_notice.pack(fill="x", pady=(0, 16))
        else:
            self._a_multi_doc_notice.pack_forget()
            self._a_single_doc_frame.pack(fill="x")

    def _run_analysis(self):
        urls_text = self._a_urls_box.get("0.0", "end-1c").strip()
        urls      = [u.strip() for u in urls_text.splitlines() if u.strip()]

        is_multi      = self._a_doc_count > 1
        contract_name = ""
        if not is_multi:
            contract_name = self._a_contract_name.get().strip()
            if not contract_name:
                self._show_err(self._a_err, self._a_err_lbl, "Please enter a Contract Name.")
                return

        if not self._analyse_files and not urls:
            self._show_err(self._a_err, self._a_err_lbl,
                           "Please select a contract file or enter at least one URL.")
            return

        self._a_err.pack_forget()
        self._a_btn.configure(state="disabled")
        self._a_spin.pack(side="left", padx=12)
        self._a_results.pack_forget()

        def _ok(data):
            self._a_btn.configure(state="normal")
            self._a_spin.pack_forget()
            findings     = data.get("findings", [])
            report_id    = data.get("report_id")
            failed_urls  = data.get("failed_urls") or []
            self._a_res_title.configure(
                text=f"Results — Report #{report_id}  ·  {len(findings)} findings"
            )

            # Rebuild amber warning banner
            for w in self._a_warn_frame.winfo_children():
                w.destroy()
            self._a_findings.pack_forget()
            if failed_urls:
                hdr_row = ctk.CTkFrame(self._a_warn_frame, fg_color="#FEF3C7")
                hdr_row.pack(fill="x", padx=12, pady=(10, 4))
                ctk.CTkLabel(
                    hdr_row,
                    text="\u26a0  Documents Not Retrieved — findings for these sources may be incomplete",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#92400E", anchor="w",
                ).pack(side="left", fill="x", expand=True)
                ctk.CTkButton(
                    hdr_row, text="\u00d7", width=28, height=28,
                    fg_color="#FEF3C7", text_color="#92400E", hover_color="#FDE68A",
                    command=self._a_warn_frame.pack_forget,
                ).pack(side="right")
                ctk.CTkLabel(
                    self._a_warn_frame,
                    text="\n".join(f"  \u2022 {u}" for u in failed_urls),
                    font=ctk.CTkFont(size=12), text_color="#92400E",
                    anchor="w", justify="left",
                ).pack(fill="x", padx=12, pady=(0, 4))
                ctk.CTkLabel(
                    self._a_warn_frame,
                    text=(
                        "Save as PDF: Chrome/Edge \u2014 File \u2192 Print \u2192 Save as PDF."
                        "  Safari \u2014 File \u2192 Export as PDF."
                    ),
                    font=ctk.CTkFont(size=11), text_color="#92400E",
                    anchor="w", wraplength=700, justify="left",
                ).pack(fill="x", padx=12, pady=(0, 10))
                self._a_warn_frame.pack(fill="x", padx=32, pady=(0, 12))
            else:
                self._a_warn_frame.pack_forget()
            self._a_findings.pack(fill="x", padx=32)

            for w in self._a_findings.winfo_children():
                w.destroy()
            for f in findings:
                self._finding_card(self._a_findings, f)
            self._a_results.pack(fill="x")
            from datetime import date
            self._dash_lbl.get("Last Analysis", ctk.CTkLabel(self, text="")
                               ).configure(text=date.today().strftime("%d %b %Y"))

        def _err(msg):
            self._a_btn.configure(state="normal")
            self._a_spin.pack_forget()
            self._show_err(self._a_err, self._a_err_lbl, msg)

        vendor_name_text = self._a_vendor_entry.get().strip()
        start_date       = self._a_start_date.get().strip() if not is_multi else ""
        end_date         = self._a_end_date.get().strip()   if not is_multi else ""
        compare          = self._a_compare_var.get()

        def _thread():
            try:
                api_url   = self._settings.get("api_url", "http://localhost:8000") + "/analyse"
                form_data: Dict[str, str] = {}
                if contract_name:
                    form_data["contract_name"] = contract_name
                if self._a_selected_group_id is not None:
                    form_data["group_id"] = str(self._a_selected_group_id)
                elif vendor_name_text:
                    form_data["vendor_name"] = vendor_name_text
                if start_date:
                    form_data["period_start"] = start_date
                if end_date:
                    form_data["period_end"] = end_date
                if compare:
                    form_data["compare_prior"] = "true"
                if urls:
                    form_data["urls"] = "\n".join(urls)

                if self._analyse_files:
                    files = [
                        ("file", (os.path.basename(p), open(p, "rb").read()))
                        for p in self._analyse_files
                    ]
                    resp = requests.post(api_url, files=files, data=form_data, timeout=180)
                else:
                    resp = requests.post(api_url, data=form_data, timeout=180)

                resp.raise_for_status()
                self.after(0, lambda: _ok(resp.json()))
            except Exception as e:
                self.after(0, lambda: _err(str(e)))

        threading.Thread(target=_thread, daemon=True).start()

    # ── Shared finding card ───────────────────────────────────────────────────

    def _finding_card(self, parent, f):
        raw = (f.get("outcome") or "").lower().replace(" ", "_")
        if raw in ("comply",):
            col, bg, badge = SUCCESS, "#F0FDF4", "COMPLY"
        elif raw in ("not_comply", "not comply"):
            col, bg, badge = ERROR,   "#FEF2F2", "NOT COMPLY"
        elif raw == "missing":
            col, bg, badge = ERROR,   "#FEF2F2", "MISSING"
        else:
            col, bg, badge = WARNING, "#FFFBEB", "PAY ATTENTION"

        sh = ctk.CTkFrame(parent, fg_color=SHADOW, corner_radius=14)
        sh.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(sh, fg_color=CARD, corner_radius=12)
        inner.pack(fill="both", expand=True, padx=(2, 3), pady=(2, 3))

        row = ctk.CTkFrame(inner, fg_color=CARD)
        row.pack(fill="both")

        # colour border
        ctk.CTkFrame(row, width=5, fg_color=col, corner_radius=4).pack(
            side="left", fill="y", padx=(10, 0), pady=14
        )

        c = ctk.CTkFrame(row, fg_color=CARD)
        c.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        # header: rule id / title / badge
        hdr = ctk.CTkFrame(c, fg_color=CARD)
        hdr.pack(fill="x", pady=(0, 8))

        rule_id    = f.get("rule_id", "—")
        rule_title = f.get("rule_title", "")
        ctk.CTkLabel(hdr, text=rule_id,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=PRIMARY).pack(side="left")
        if rule_title:
            _label(hdr, f"  —  {rule_title}", size=13, colour=TXT).pack(side="left")

        _badge(hdr, badge, col, bg).pack(side="right")

        # clause quoted
        clause = (f.get("clause_quoted") or "").strip()
        if clause:
            _label(c, f'"{clause}"', size=12, colour=TXT2,
                   wraplength=720, justify="left").pack(anchor="w", pady=(0, 6))

        # reason
        reason = (f.get("reason") or "").strip()
        if reason:
            _label(c, reason, size=13, colour=TXT,
                   wraplength=720, justify="left").pack(anchor="w")

    # ═════════════════════════════════════════════════════════════════════════
    # REPORTS
    # ═════════════════════════════════════════════════════════════════════════

    def _build_reports(self):
        page = ctk.CTkFrame(self._content, fg_color=BG, corner_radius=0)
        self._pages["reports"] = page

        p = 32
        _section_title(page, "Reports", pady=(p, 16))

        # error banner
        self._r_err, self._r_err_lbl = _err_banner(page)

        # search card
        sh, sc_f = _make_card(page)
        sh.pack(fill="x", padx=p, pady=(0, 20))
        sr = ctk.CTkFrame(sc_f, fg_color=CARD)
        sr.pack(fill="x", padx=20, pady=16)

        # live-filter text input
        self._r_vendor_filter = _entry(sr, "Search by vendor name…", width=220)
        self._r_vendor_filter.pack(side="left")
        self._r_vendor_filter.bind("<KeyRelease>", lambda _e: self._r_filter_vendors())

        # vendor dropdown — populated on page load
        self._r_vendor_combo = ctk.CTkComboBox(
            sr, values=[], width=260, height=40,
            corner_radius=8, fg_color="white", border_color=BORDER,
            text_color=TXT, button_color=PRIMARY, button_hover_color=TEAL,
            command=self._on_report_vendor_selected,
        )
        self._r_vendor_combo.set("Select vendor…")
        self._r_vendor_combo.pack(side="left", padx=(8, 0))

        _btn(sr, "Search", self._search_reports,
             height=40, width=100).pack(side="left", padx=(12, 0))
        _ghost_btn(sr, "Show All", self._r_show_all,
                   height=40).pack(side="left", padx=(8, 0))

        self._r_spin = _label(sr, "  Loading…", colour=TXT2)

        # results list
        self._r_list = ctk.CTkScrollableFrame(page, fg_color=BG, corner_radius=0)
        self._r_list.pack(fill="both", expand=True, padx=p, pady=(0, p))

    def _load_report_vendors(self):
        def _ok(data):
            self._r_vendors_data     = data
            names = [v["group_name"] for v in data]
            self._r_all_vendor_names = names
            self._r_vendor_combo.configure(values=names)
        self._api("GET", "/vendors/list", _ok, lambda _: None)

    def _r_filter_vendors(self):
        q = self._r_vendor_filter.get().strip().lower()
        if not q:
            filtered = self._r_all_vendor_names
        else:
            filtered = [n for n in self._r_all_vendor_names if q in n.lower()]
        self._r_vendor_combo.configure(values=filtered)
        if filtered:
            self._r_vendor_combo.set(filtered[0])
        else:
            self._r_vendor_combo.set("")

    def _on_report_vendor_selected(self, choice):
        for v in self._r_vendors_data:
            if v["group_name"] == choice:
                self._r_selected_group_id = v["group_id"]
                self._search_reports()
                return
        self._r_selected_group_id = None

    def _r_show_all(self):
        self._r_vendor_filter.delete(0, "end")
        self._r_vendor_combo.configure(values=self._r_all_vendor_names)
        self._r_vendor_combo.set("Select vendor…")
        self._r_selected_group_id = None
        for w in self._r_list.winfo_children():
            w.destroy()
        self._r_err.pack_forget()

    def _search_reports(self):
        gid = self._r_selected_group_id
        if gid is None:
            choice = self._r_vendor_combo.get().strip()
            for v in self._r_vendors_data:
                if v["group_name"] == choice:
                    gid = v["group_id"]
                    self._r_selected_group_id = gid
                    break
        if gid is None:
            self._show_err(self._r_err, self._r_err_lbl, "Please select a vendor.")
            return
        self._r_err.pack_forget()
        self._r_spin.pack(side="left", padx=12)

        def _ok(data):
            self._r_spin.pack_forget()
            for w in self._r_list.winfo_children():
                w.destroy()
            reports = data.get("reports", [])
            if not reports:
                _label(self._r_list, "No reports found for this vendor.",
                       size=14, colour=TXT2).pack(pady=32)
                return
            for r in reports:
                self._report_card(self._r_list, r)

        def _err(msg):
            self._r_spin.pack_forget()
            self._show_err(self._r_err, self._r_err_lbl, msg)

        self._api("GET", f"/vendors/{gid}/reports", _ok, _err)

    def _report_card(self, parent, r):
        sh = ctk.CTkFrame(parent, fg_color=SHADOW, corner_radius=14)
        sh.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(sh, fg_color=CARD, corner_radius=12)
        inner.pack(fill="both", expand=True, padx=(2, 3), pady=(2, 3))

        c = ctk.CTkFrame(inner, fg_color=CARD)
        c.pack(fill="both", padx=20, pady=16)

        # top row — vendor name as primary title
        top = ctk.CTkFrame(c, fg_color=CARD)
        top.pack(fill="x")
        vendor_title = r.get("group_name") or r.get("contract_name") or "Unknown Vendor"
        ctk.CTkLabel(top, text=vendor_title,
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=TXT).pack(side="left")

        # details — formatted date · report id · analysis type
        dt = ctk.CTkFrame(c, fg_color=CARD)
        dt.pack(fill="x", pady=(6, 12))
        raw_date = str(r.get("created_at", ""))[:10]
        try:
            from datetime import datetime as _dt
            _d = _dt.strptime(raw_date, "%Y-%m-%d")
            formatted_date = _d.strftime("%-d %B %Y")
        except Exception:
            formatted_date = raw_date
        contract_name = r.get("contract_name") or ""
        analysis_type = "Group Analysis" if "Group Analysis" in contract_name else "Single Document"
        detail = f"{formatted_date}  ·  Report #{r.get('report_id', '?')}  ·  {analysis_type}"
        _label(dt, detail, size=12, colour=TXT2).pack(side="left")

        rid = r.get("report_id")
        btn_row = ctk.CTkFrame(c, fg_color=CARD)
        btn_row.pack(anchor="w")
        _ghost_btn(btn_row, "View Details →",
                   lambda r=rid: self._report_detail(r),
                   height=32).pack(side="left", padx=(0, 8))
        _btn(btn_row, "⬇  Download .docx",
             lambda r=rid: self._download_docx(r),
             height=32, width=170).pack(side="left")

    def _report_detail(self, report_id):
        win = ctk.CTkToplevel(self)
        win.title(f"Report  #{report_id}")
        win.geometry("860x640")
        win.configure(fg_color=BG)
        win.grab_set()

        scroll = ctk.CTkScrollableFrame(win, fg_color=BG)
        scroll.pack(fill="both", expand=True, padx=28, pady=28)

        loading = _label(scroll, "Loading…", size=14, colour=TXT2)
        loading.pack(pady=40)

        def _ok(data):
            loading.destroy()
            report = data.get("report", {})
            risks  = data.get("risks", [])

            ctk.CTkLabel(scroll, text=f"Report  #{report.get('report_id')}",
                         font=ctk.CTkFont(size=22, weight="bold"),
                         text_color=TXT).pack(anchor="w")
            _label(scroll,
                   f"Created: {str(report.get('created_at',''))[:10]}  ·  "
                   f"Contract #{report.get('contract_id','?')}",
                   size=13).pack(anchor="w", pady=(4, 20))

            for risk in risks:
                self._finding_card(scroll, {
                    "rule_id":      risk.get("rule_name", "?"),
                    "rule_title":   risk.get("rule_title", ""),
                    "outcome":      risk.get("risk_name", ""),
                    "clause_quoted": risk.get("finding_text", ""),
                    "reason":       risk.get("description", ""),
                })

        def _err(msg):
            loading.configure(text=f"Error: {msg}", text_color=ERROR)

        self._api("GET", f"/reports/{report_id}", _ok, _err)

    # ═════════════════════════════════════════════════════════════════════════
    # LEGISLATION UPDATE
    # ═════════════════════════════════════════════════════════════════════════

    def _build_legislation(self):
        page = ctk.CTkScrollableFrame(self._content, fg_color=BG, corner_radius=0)
        self._pages["legislation"] = page

        p = 32
        _section_title(page, "Legislation", pady=(p, 12))

        # ── Subtab bar ────────────────────────────────────────────────────────
        tab_bar = ctk.CTkFrame(page, fg_color=BG)
        tab_bar.pack(fill="x", padx=p, pady=(0, 20))

        self._leg_tab_btns = {}
        for key, label in [("upload", "Legislation Update"), ("rules", "Rules Library")]:
            b = ctk.CTkButton(
                tab_bar, text=label, height=38, corner_radius=8,
                fg_color=PRIMARY if key == "upload" else "transparent",
                hover_color=TEAL,
                text_color="white" if key == "upload" else PRIMARY,
                font=ctk.CTkFont(size=13, weight="bold"),
                border_width=2, border_color=PRIMARY,
                command=lambda k=key: self._leg_show_tab(k),
            )
            b.pack(side="left", padx=(0, 8))
            self._leg_tab_btns[key] = b

        # ── Panes (one per subtab) ────────────────────────────────────────────
        self._leg_upload_pane = ctk.CTkFrame(page, fg_color=BG, corner_radius=0)
        self._leg_rules_pane  = ctk.CTkFrame(page, fg_color=BG, corner_radius=0)

        self._build_leg_upload(self._leg_upload_pane, p)
        self._build_leg_rules(self._leg_rules_pane, p)

        # Show upload tab by default
        self._leg_upload_pane.pack(fill="both", expand=True)

    def _leg_show_tab(self, key):
        for k, btn in self._leg_tab_btns.items():
            if k == key:
                btn.configure(fg_color=PRIMARY, text_color="white", hover_color=TEAL)
            else:
                btn.configure(fg_color="transparent", text_color=PRIMARY, hover_color=TEAL)
        self._leg_upload_pane.pack_forget()
        self._leg_rules_pane.pack_forget()
        if key == "upload":
            self._leg_upload_pane.pack(fill="both", expand=True)
        else:
            self._leg_rules_pane.pack(fill="both", expand=True)
            self._rl_load_rules()

    # ── Legislation Upload pane ───────────────────────────────────────────────

    def _build_leg_upload(self, pane, p):
        self._l_err, self._l_err_lbl = _err_banner(pane)

        sh, uc = _make_card(pane)
        sh.pack(fill="x", padx=p, pady=(0, 20))
        form = ctk.CTkFrame(uc, fg_color=CARD)
        form.pack(fill="both", padx=24, pady=24)

        ctk.CTkLabel(form, text="Upload Legislation Document",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=TXT).pack(anchor="w", pady=(0, 16))

        self._l_file_lbl = _upload_box(
            form,
            "Select updated legislation document",
            self._browse_leg,
        )

        _label(form, "Document Version ID  *").pack(anchor="w", pady=(0, 4))
        self._l_vid = _entry(form, "e.g. 3", width=260)
        self._l_vid.pack(anchor="w", pady=(0, 20))

        br = ctk.CTkFrame(form, fg_color=CARD)
        br.pack(anchor="w")

        self._l_btn = _btn(br, "📤  Analyse Legislation",
                           self._upload_legislation,
                           height=44, width=230)
        self._l_btn.pack(side="left")
        self._l_spin = _label(br, "  Analysing…", colour=TXT2)

        self._l_changes = ctk.CTkFrame(pane, fg_color=BG, corner_radius=0)
        self._l_ch_title = ctk.CTkLabel(
            self._l_changes, text="Proposed Changes",
            font=ctk.CTkFont(size=18, weight="bold"), text_color=TXT,
        )
        self._l_ch_title.pack(anchor="w", padx=p, pady=(8, 16))

        self._l_ch_list = ctk.CTkFrame(self._l_changes, fg_color=BG)
        self._l_ch_list.pack(fill="x", padx=p)

        self._l_submit = _btn(
            self._l_changes,
            "✅  Submit All Decisions",
            self._submit_decisions,
            fg=SUCCESS, hover="#16A34A", height=44, width=250,
        )

    # ── Rules Library pane ────────────────────────────────────────────────────

    def _build_leg_rules(self, pane, p):
        self._rl_all_rules = []

        top = ctk.CTkFrame(pane, fg_color=BG)
        top.pack(fill="x", padx=p, pady=(0, 16))

        self._rl_search = _entry(top, "Search rules…", width=350)
        self._rl_search.pack(side="left")
        self._rl_search.bind("<KeyRelease>", lambda _e: self._rl_filter())

        if self._privilege == "ADMIN":
            _btn(top, "＋  Add Rule", self._rl_open_add,
                 height=40, width=150).pack(side="right")

        self._rl_err, self._rl_err_lbl = _err_banner(pane)

        self._rl_spin = _label(pane, "Loading rules…", size=14, colour=TXT2)

        self._rl_list = ctk.CTkFrame(pane, fg_color=BG, corner_radius=0)
        self._rl_list.pack(fill="both", expand=True, padx=p, pady=(0, p))

    def _rl_load_rules(self):
        for w in self._rl_list.winfo_children():
            w.destroy()
        self._rl_err.pack_forget()
        self._rl_spin.pack(pady=16)

        def _ok(data):
            self._rl_spin.pack_forget()
            self._rl_all_rules = data.get("rules", [])
            self._rl_filter()

        def _err(msg):
            self._rl_spin.pack_forget()
            self._show_err(self._rl_err, self._rl_err_lbl, msg)

        def _load():
            try:
                with open(_ARTIFACT_B_PATH, encoding="utf-8") as fh:
                    data = json.load(fh)
                self.after(0, lambda: _ok(data))
            except Exception as e:
                self.after(0, lambda: _err(str(e)))

        threading.Thread(target=_load, daemon=True).start()

    def _rl_filter(self):
        q = self._rl_search.get().strip().lower()
        if not q:
            filtered = self._rl_all_rules
        else:
            filtered = [
                r for r in self._rl_all_rules
                if q in (r.get("id") or "").lower()
                or q in (r.get("title") or "").lower()
                or q in (r.get("check") or "").lower()
                or q in (r.get("citation") or "").lower()
                or q in (r.get("comply_requires") or "").lower()
            ]
        self._rl_render(filtered)

    def _rl_render(self, rules):
        for w in self._rl_list.winfo_children():
            w.destroy()

        if not rules:
            _label(self._rl_list, "No rules found.", size=14, colour=TXT2).pack(pady=24)
            return

        from collections import defaultdict
        groups = defaultdict(list)
        for r in rules:
            groups[r.get("category", "CAT1")].append(r)

        for cat_code, cat_label in _RULE_CATS:
            cat_rules = groups.get(cat_code, [])
            if not cat_rules:
                continue
            self._rl_cat_section(self._rl_list, cat_label, cat_rules)

    def _rl_cat_section(self, parent, cat_label, rules):
        sect = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        sect.pack(fill="x", pady=(0, 12))

        body = ctk.CTkFrame(sect, fg_color=BG, corner_radius=0)

        toggle_state = [True]

        def _toggle():
            if toggle_state[0]:
                body.pack_forget()
                toggle_state[0] = False
                hdr.configure(text=f"▶  {cat_label}  ({len(rules)})")
            else:
                body.pack(fill="x", pady=(4, 0))
                toggle_state[0] = True
                hdr.configure(text=f"▼  {cat_label}  ({len(rules)})")

        hdr = ctk.CTkButton(
            sect,
            text=f"▼  {cat_label}  ({len(rules)})",
            anchor="w",
            fg_color="#EBF5FB",
            hover_color="#D4E6F1",
            text_color=TXT,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=46,
            corner_radius=8,
            command=_toggle,
        )
        hdr.pack(fill="x")
        body.pack(fill="x", pady=(6, 0))

        for rule in rules:
            self._rl_rule_card(body, rule)

    def _rl_rule_card(self, parent, rule):
        sh = ctk.CTkFrame(parent, fg_color=SHADOW, corner_radius=12)
        sh.pack(fill="x", pady=(0, 8))
        inner = ctk.CTkFrame(sh, fg_color=CARD, corner_radius=10)
        inner.pack(fill="both", expand=True, padx=(2, 3), pady=(2, 3))

        c = ctk.CTkFrame(inner, fg_color=CARD)
        c.pack(fill="both", padx=20, pady=14)

        hdr = ctk.CTkFrame(c, fg_color=CARD)
        hdr.pack(fill="x", pady=(0, 8))

        rule_id = rule.get("id", "?")
        title   = rule.get("title", "")

        ctk.CTkLabel(hdr, text=rule_id,
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=PRIMARY).pack(side="left")
        if title:
            _label(hdr, f"  —  {title}", size=13, colour=TXT).pack(side="left")
        if rule.get("critical"):
            _badge(hdr, "CRITICAL", "white", ERROR).pack(side="left", padx=(10, 0))

        if self._privilege == "ADMIN":
            _ghost_btn(hdr, "Remove",
                       lambda r=rule: self._rl_confirm_remove(r),
                       height=30).pack(side="right")
            _btn(hdr, "Edit",
                 lambda r=rule: self._rl_open_edit(r),
                 height=30, width=70).pack(side="right", padx=(0, 8))

        if rule.get("check"):
            _label(c, "What it checks:", size=12, colour=TXT2).pack(anchor="w")
            _label(c, rule["check"], size=13, colour=TXT,
                   wraplength=680, justify="left").pack(anchor="w", pady=(2, 6))

        if rule.get("citation"):
            _label(c, "Citation:", size=12, colour=TXT2).pack(anchor="w")
            _label(c, rule["citation"], size=12, colour=TXT2,
                   wraplength=680, justify="left").pack(anchor="w", pady=(2, 6))

        if rule.get("comply_requires"):
            _label(c, "Comply requires:", size=12, colour=TXT2).pack(anchor="w")
            _label(c, rule["comply_requires"], size=13, colour=TXT,
                   wraplength=680, justify="left").pack(anchor="w", pady=(2, 0))

    # ── Rules CRUD forms ─────────────────────────────────────────────────────

    def _rl_open_add(self):
        self._rl_rule_form(None)

    def _rl_open_edit(self, rule):
        self._rl_rule_form(rule)

    def _rl_rule_form(self, existing):
        is_edit = existing is not None
        r = existing or {}

        win = ctk.CTkToplevel(self)
        win.title("Edit Rule" if is_edit else "Add Rule")
        win.geometry("720x760")
        win.configure(fg_color=BG)
        win.grab_set()

        scroll = ctk.CTkScrollableFrame(win, fg_color=BG)
        scroll.pack(fill="both", expand=True, padx=28, pady=28)

        ctk.CTkLabel(scroll,
                     text="Edit Rule" if is_edit else "Add Rule",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=TXT).pack(anchor="w", pady=(0, 20))

        def _entry_row(label, placeholder="", val="", width=460):
            _label(scroll, label, size=12).pack(anchor="w", pady=(10, 2))
            e = _entry(scroll, placeholder, width=width)
            if val:
                e.insert(0, val)
            e.pack(anchor="w")
            return e

        def _text_row(label, val="", height=72):
            _label(scroll, label, size=12).pack(anchor="w", pady=(10, 2))
            tb = ctk.CTkTextbox(scroll, height=height, corner_radius=8,
                                fg_color="white", border_width=1,
                                border_color=BORDER, text_color=TXT, width=660)
            tb.pack(anchor="w", fill="x")
            if val:
                tb.insert("0.0", val)
            return tb

        f_id    = _entry_row("Rule ID  *", "e.g. C2.7", val=r.get("id", ""))
        f_title = _entry_row("Title", "Short descriptive title", val=r.get("title", ""))

        _label(scroll, "Category  *", size=12).pack(anchor="w", pady=(10, 2))
        cat_labels = [lbl for _, lbl in _RULE_CATS]
        cur_lbl    = next((lbl for c, lbl in _RULE_CATS if c == r.get("category", "")),
                          cat_labels[0])
        f_cat = ctk.CTkComboBox(scroll, values=cat_labels, width=460, height=40,
                                corner_radius=8, fg_color="white", border_color=BORDER,
                                text_color=TXT, button_color=PRIMARY,
                                button_hover_color=TEAL)
        f_cat.set(cur_lbl)
        f_cat.pack(anchor="w")

        f_check   = _text_row("Check (what this rule checks)  *", val=r.get("check", ""), height=80)
        f_why     = _text_row("Why", val=r.get("why", ""), height=64)
        f_cite    = _text_row("Citation", val=r.get("citation", ""), height=64)
        f_comply  = _text_row("Comply Requires", val=r.get("comply_requires", ""), height=64)
        f_missing = _text_row("Missing If", val=r.get("missing_if", ""), height=48)

        triggers_val = ", ".join(r.get("ambiguity_triggers") or [])
        f_triggers = _entry_row("Ambiguity Triggers (comma-separated)",
                                "phrase one, phrase two",
                                val=triggers_val, width=660)

        f_notes = _text_row("Notes", val=r.get("notes", ""), height=48)

        _label(scroll, "Critical rule", size=12).pack(anchor="w", pady=(10, 2))
        crit_var = ctk.BooleanVar(value=bool(r.get("critical", False)))
        ctk.CTkSwitch(scroll, text="Mark as critical",
                      variable=crit_var,
                      progress_color=ERROR,
                      button_color=ERROR,
                      button_hover_color="#DC2626").pack(anchor="w")

        form_err, form_err_lbl = _err_banner(scroll)

        def _save():
            rid   = f_id.get().strip()
            check = f_check.get("0.0", "end-1c").strip()
            if not rid or not check:
                form_err_lbl.configure(text="⚠  Rule ID and Check are required.")
                form_err.pack(fill="x", pady=(10, 0))
                return

            cat_code = next((c for c, lbl in _RULE_CATS if lbl == f_cat.get()), "CAT1")
            raw_trig = f_triggers.get().strip()
            triggers = [t.strip() for t in raw_trig.split(",") if t.strip()]

            payload = {
                "id":                rid,
                "category":          cat_code,
                "check":             check,
                "why":               f_why.get("0.0", "end-1c").strip() or None,
                "citation":          f_cite.get("0.0", "end-1c").strip() or None,
                "comply_requires":   f_comply.get("0.0", "end-1c").strip() or None,
                "missing_if":        f_missing.get("0.0", "end-1c").strip() or None,
                "ambiguity_triggers": triggers or None,
                "notes":             f_notes.get("0.0", "end-1c").strip() or None,
                "critical":          True if crit_var.get() else None,
            }
            title_val = f_title.get().strip()
            if title_val:
                payload["title"] = title_val
            payload = {k: v for k, v in payload.items() if v is not None}

            def _ok(_data):
                win.destroy()
                self._rl_load_rules()

            def _api_err(msg):
                form_err_lbl.configure(text=f"⚠  {msg}")
                form_err.pack(fill="x", pady=(10, 0))

            existing_id = r.get("id") if is_edit else None
            self._artifact_save_rule(is_edit, existing_id, payload, _ok, _api_err)

        btn_row = ctk.CTkFrame(scroll, fg_color=BG)
        btn_row.pack(anchor="w", pady=(20, 0))
        _btn(btn_row, "Save Rule", _save, height=44, width=140).pack(side="left")
        _ghost_btn(btn_row, "Cancel", win.destroy, height=44).pack(side="left", padx=(12, 0))

    def _rl_confirm_remove(self, rule):
        rid   = rule.get("id", "?")
        title = rule.get("title") or (rule.get("check") or "")[:60]

        win = ctk.CTkToplevel(self)
        win.title("Remove Rule")
        win.geometry("520x260")
        win.configure(fg_color=BG)
        win.grab_set()

        f = ctk.CTkFrame(win, fg_color=BG)
        f.pack(fill="both", padx=32, pady=32)

        ctk.CTkLabel(f, text="Remove Rule",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TXT).pack(anchor="w", pady=(0, 12))

        _label(f,
               f"Are you sure you want to remove rule {rid} — {title}? "
               "This cannot be undone without restoring a backup.",
               size=13, colour=TXT, wraplength=450,
               justify="left").pack(anchor="w", pady=(0, 20))

        rem_err, rem_err_lbl = _err_banner(f)

        def _confirm():
            def _ok(_data):
                win.destroy()
                self._rl_load_rules()

            def _err(msg):
                rem_err_lbl.configure(text=f"⚠  {msg}")
                rem_err.pack(fill="x", pady=(8, 0))

            self._artifact_delete_rule(rid, _ok, _err)

        br = ctk.CTkFrame(f, fg_color=BG)
        br.pack(anchor="w")
        _btn(br, "Remove", _confirm,
             fg=ERROR, hover="#DC2626", height=40, width=120).pack(side="left")
        _ghost_btn(br, "Cancel", win.destroy, height=40).pack(side="left", padx=(12, 0))

    def _browse_leg(self):
        path = filedialog.askopenfilename(
            title="Select legislation document",
            filetypes=[("Documents", "*.pdf *.doc *.docx")],
        )
        if path:
            self._leg_file = path
            self._l_file_lbl.configure(
                text=os.path.basename(path), text_color=PRIMARY,
            )

    def _upload_legislation(self):
        vid = self._l_vid.get().strip()
        if not vid:
            self._show_err(self._l_err, self._l_err_lbl,
                           "Please enter a Document Version ID.")
            return
        if not self._leg_file:
            self._show_err(self._l_err, self._l_err_lbl,
                           "Please select a legislation file.")
            return

        self._l_err.pack_forget()
        self._l_btn.configure(state="disabled")
        self._l_spin.pack(side="left", padx=12)
        self._l_changes.pack_forget()
        self._leg_decisions = []

        with open(self._leg_file, "rb") as fh:
            file_bytes = fh.read()
        files = {"file": (os.path.basename(self._leg_file), file_bytes)}
        data  = {"document_version_id": vid}

        def _ok(resp_data):
            self._l_btn.configure(state="normal")
            self._l_spin.pack_forget()
            self._leg_review_id = resp_data.get("review_id")
            changes = resp_data.get("proposed_changes") or []
            self._render_changes(changes)

        def _err(msg):
            self._l_btn.configure(state="normal")
            self._l_spin.pack_forget()
            self._show_err(self._l_err, self._l_err_lbl, msg)

        def _thread():
            try:
                url = self._settings.get("api_url", "http://localhost:8000") + "/legislation/upload"
                r = requests.post(url, files=files, data=data, timeout=120)
                r.raise_for_status()
                self.after(0, lambda: _ok(r.json()))
            except Exception as e:
                self.after(0, lambda: _err(str(e)))

        threading.Thread(target=_thread, daemon=True).start()

    def _render_changes(self, changes):
        for w in self._l_ch_list.winfo_children():
            w.destroy()

        self._leg_decisions = [None] * len(changes)
        self._l_ch_title.configure(
            text=f"Proposed Changes  ·  {len(changes)} items"
        )
        for i, ch in enumerate(changes):
            self._change_card(self._l_ch_list, i, ch)

        self._l_changes.pack(fill="x")
        self._l_submit.pack(anchor="w", padx=32, pady=(20, 32))

    def _change_card(self, parent, idx, ch):
        ctype  = (ch.get("change_type") or ch.get("type") or "MODIFY").upper()
        rule   = ch.get("rule_id") or ch.get("rule") or "?"
        what   = ch.get("proposed_text") or ch.get("what") or ch.get("description") or ""
        reason = ch.get("reason") or ch.get("rationale") or ""

        type_map = {
            "MODIFY":   (TEAL,    "#EFF9FB"),
            "NEW":      (SUCCESS, "#F0FDF4"),
            "OBSOLETE": (ERROR,   "#FEF2F2"),
        }
        badge_fg, badge_bg = type_map.get(ctype, (WARNING, "#FFFBEB"))

        sh = ctk.CTkFrame(parent, fg_color=SHADOW, corner_radius=14)
        sh.pack(fill="x", pady=(0, 16))
        inner = ctk.CTkFrame(sh, fg_color=CARD, corner_radius=12)
        inner.pack(fill="both", expand=True, padx=(2, 3), pady=(2, 3))

        c = ctk.CTkFrame(inner, fg_color=CARD)
        c.pack(fill="both", padx=24, pady=20)

        # header
        hdr = ctk.CTkFrame(c, fg_color=CARD)
        hdr.pack(fill="x", pady=(0, 12))
        _badge(hdr, ctype, badge_fg, badge_bg).pack(side="left")
        ctk.CTkLabel(hdr, text=f"  Rule: {rule}",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TXT).pack(side="left")

        if what:
            _label(c, "What changes:", size=12, colour=TXT2).pack(anchor="w")
            _label(c, what, size=13, colour=TXT,
                   wraplength=680, justify="left").pack(anchor="w", pady=(2, 8))

        if reason:
            _label(c, "Reason:", size=12, colour=TXT2).pack(anchor="w")
            _label(c, reason, size=13, colour=TXT,
                   wraplength=680, justify="left").pack(anchor="w", pady=(2, 12))

        # edit area (hidden)
        edit_frame = ctk.CTkFrame(c, fg_color="#F8FAFC", corner_radius=8)
        _label(edit_frame, "Edit proposed text:", size=12).pack(
            anchor="w", padx=12, pady=(10, 0)
        )
        edit_box = ctk.CTkTextbox(edit_frame, height=80, corner_radius=8,
                                  fg_color="white", border_width=1,
                                  border_color=BORDER, text_color=TXT)
        edit_box.pack(fill="x", padx=12, pady=(4, 0))
        edit_box.insert("0.0", what)

        decision_lbl = _label(c, "", size=12, colour=SUCCESS)
        decision_lbl.pack(anchor="w", pady=(8, 0))

        def _decide(d, edited=""):
            self._leg_decisions[idx] = {
                "change_index": idx,
                "decision":     d,
                "edited_text":  edited,
            }
            if d == "accept":
                decision_lbl.configure(text="✅  Accepted", text_color=SUCCESS)
                edit_frame.pack_forget()
            elif d == "decline":
                decision_lbl.configure(text="❌  Declined", text_color=TXT2)
                edit_frame.pack_forget()
            elif d == "edit":
                decision_lbl.configure(text="✏️  Editing…", text_color=WARNING)
                edit_frame.pack(fill="x", pady=(8, 0))

        def _save_edit():
            txt = edit_box.get("0.0", "end-1c").strip()
            _decide("accept_with_edit", edited=txt)
            decision_lbl.configure(text="✅  Accepted with edits", text_color=SUCCESS)

        # save button inside edit_frame
        _btn(edit_frame, "Save Edit", _save_edit,
             height=30, width=100,
             font=ctk.CTkFont(size=12)).pack(
            padx=12, pady=(4, 12), anchor="w"
        )

        # decision buttons
        br = ctk.CTkFrame(c, fg_color=CARD)
        br.pack(anchor="w", pady=(8, 0))

        _btn(br, "✓  Accept",
             lambda: _decide("accept"),
             fg=SUCCESS, hover="#16A34A", height=36, width=110,
             font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            br, text="✕  Decline", corner_radius=8, height=36, width=110,
            fg_color="#F3F4F6", hover_color=BORDER,
            text_color=TXT, font=ctk.CTkFont(size=13),
            command=lambda: _decide("decline"),
        ).pack(side="left", padx=(0, 8))

        _ghost_btn(br, "✎  Accept with Edits",
                   lambda: _decide("edit"),
                   height=36).pack(side="left")

    def _submit_decisions(self):
        if self._leg_review_id is None:
            self._show_err(self._l_err, self._l_err_lbl, "No active review.")
            return
        decisions = [d for d in self._leg_decisions if d is not None]
        if not decisions:
            self._show_err(self._l_err, self._l_err_lbl,
                           "Please make at least one decision.")
            return

        self._l_submit.configure(state="disabled", text="Submitting…")

        def _ok(data):
            self._l_submit.configure(state="normal", text="✅  Submit All Decisions")
            summary = data.get("summary", "")
            ctk.CTkLabel(
                self._l_changes,
                text=f"✅  Decisions submitted.  {summary}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=SUCCESS,
            ).pack(anchor="w", padx=32, pady=(8, 0))

        def _err(msg):
            self._l_submit.configure(state="normal", text="✅  Submit All Decisions")
            self._show_err(self._l_err, self._l_err_lbl, msg)

        self._api(
            "POST", "/legislation/apply", _ok, _err,
            json={
                "review_id":   self._leg_review_id,
                "reviewed_by": self._user,
                "decisions":   decisions,
            },
        )

    # ═════════════════════════════════════════════════════════════════════════
    # SETTINGS
    # ═════════════════════════════════════════════════════════════════════════

    def _build_settings(self):
        page = ctk.CTkScrollableFrame(self._content, fg_color=BG, corner_radius=0)
        self._pages["settings"] = page

        p = 32
        _section_title(page, "Settings", pady=(p, 16))

        # API config card
        sh, api_c = _make_card(page)
        sh.pack(fill="x", padx=p, pady=(0, 24))
        f = ctk.CTkFrame(api_c, fg_color=CARD)
        f.pack(fill="both", padx=24, pady=24)

        ctk.CTkLabel(f, text="API Configuration",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=TXT).pack(anchor="w", pady=(0, 16))

        _label(f, "Backend API URL").pack(anchor="w", pady=(0, 4))
        self._s_api = _entry(f, "http://localhost:8000", width=420)
        self._s_api.insert(0, self._settings.get("api_url", "http://localhost:8000"))
        self._s_api.pack(anchor="w", pady=(0, 16))

        sr = ctk.CTkFrame(f, fg_color=CARD)
        sr.pack(anchor="w")
        _btn(sr, "Save Settings", self._save_settings_ui,
             height=40, width=160).pack(side="left")
        self._s_saved = _label(sr, "", colour=SUCCESS)
        self._s_saved.pack(side="left", padx=12)

        # About card
        sh2, ab_c = _make_card(page)
        sh2.pack(fill="x", padx=p, pady=(0, p))
        about = ctk.CTkFrame(ab_c, fg_color=CARD)
        about.pack(fill="both", padx=24, pady=24)

        ctk.CTkLabel(about, text="About",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=TXT).pack(anchor="w", pady=(0, 14))

        for label, val in [
            ("Application",   "SCC Compliance Tool"),
            ("Version",       "1.0.0"),
            ("Organisation",  "Sunshine Coast Council"),
            ("AI Model",      "claude-sonnet-4-6"),
        ]:
            row = ctk.CTkFrame(about, fg_color=CARD)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"{label}:", width=130, anchor="w",
                         font=ctk.CTkFont(size=13), text_color=TXT2).pack(side="left")
            ctk.CTkLabel(row, text=val,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=TXT).pack(side="left")

    def _save_settings_ui(self):
        url = self._s_api.get().strip()
        self._settings["api_url"] = url
        _save_settings(self._settings)
        self._s_saved.configure(text="✓  Saved")
        self.after(2500, lambda: self._s_saved.configure(text=""))

    # ═════════════════════════════════════════════════════════════════════════
    # CONTRACTS DIRECTORY
    # ═════════════════════════════════════════════════════════════════════════

    def _build_contracts(self):
        page = ctk.CTkScrollableFrame(self._content, fg_color=BG, corner_radius=0)
        self._pages["contracts"] = page

        p = 32
        _section_title(page, "Contracts Directory", pady=(p, 16))

        self._cd_spin = _label(page, "Loading…", size=14, colour=TXT2)
        self._cd_err, self._cd_err_lbl = _err_banner(page)

        self._cd_list = ctk.CTkFrame(page, fg_color=BG, corner_radius=0)
        self._cd_list.pack(fill="both", expand=True, padx=p, pady=(0, p))

    def _load_contracts_directory(self):
        for w in self._cd_list.winfo_children():
            w.destroy()
        self._cd_err.pack_forget()
        self._cd_spin.pack(pady=16)

        def _ok(data):
            self._cd_spin.pack_forget()
            if not data:
                _label(self._cd_list, "No contracts found.", size=14,
                       colour=TXT2).pack(pady=32)
                return
            for group in data:
                self._cd_vendor_card(self._cd_list, group)

        def _err(msg):
            self._cd_spin.pack_forget()
            self._show_err(self._cd_err, self._cd_err_lbl, msg)

        self._api("GET", "/contracts/directory", _ok, _err)

    def _cd_vendor_card(self, parent, group):
        sh = ctk.CTkFrame(parent, fg_color=SHADOW, corner_radius=14)
        sh.pack(fill="x", pady=(0, 16))
        inner = ctk.CTkFrame(sh, fg_color=CARD, corner_radius=12)
        inner.pack(fill="both", expand=True, padx=(2, 3), pady=(2, 3))

        c = ctk.CTkFrame(inner, fg_color=CARD)
        c.pack(fill="both", padx=24, pady=20)

        hdr = ctk.CTkFrame(c, fg_color=CARD)
        hdr.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(hdr, text=group.get("group_name", "—"),
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=TXT).pack(side="left")

        gid   = group.get("group_id")
        gname = group.get("group_name", "")
        _btn(hdr, "Run Analysis",
             lambda g=gid, n=gname: self._go_analyse_vendor(g, n),
             height=36, width=140).pack(side="right")

        contracts = group.get("contracts", [])
        if not contracts:
            _label(c, "No contracts uploaded yet.", size=13, colour=TXT2).pack(anchor="w")
            return

        for ct in contracts:
            row = ctk.CTkFrame(c, fg_color="#F8FAFC", corner_radius=8)
            row.pack(fill="x", pady=(0, 6))

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(fill="x", padx=16, pady=10)

            name       = ct.get("contract_name") or "Unnamed"
            uploaded   = str(ct.get("uploaded_at") or "")[:10]
            ps         = ct.get("period_start")
            pe         = ct.get("period_end")
            period_str = f"  ·  {ps} → {pe}" if ps or pe else ""
            detail     = f"uploaded {uploaded}{period_str}" if uploaded else period_str

            ctk.CTkLabel(info, text=name,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=TXT).pack(side="left")
            if detail:
                _label(info, f"  —  {detail}", size=12, colour=TXT2).pack(side="left")

    def _go_analyse_vendor(self, group_id, group_name):
        self._go("analyse")
        self._a_vendor_entry.delete(0, "end")
        self._a_vendor_entry.insert(0, group_name)
        self._a_selected_group_id = group_id

    # ── Artifact CRUD helpers (try API first, fall back to direct file I/O) ──

    def _artifact_save_rule(self, is_edit, existing_id, payload, on_ok, on_err):
        def _thread():
            api_path = f"/rules/{existing_id}" if is_edit else "/rules"
            method   = "PUT" if is_edit else "POST"
            try:
                url = self._settings.get("api_url", "http://localhost:8000") + api_path
                resp = requests.request(method, url, json=payload, timeout=5)
                resp.raise_for_status()
                self.after(0, lambda: on_ok(resp.json()))
                return
            except Exception:
                pass
            try:
                with open(_ARTIFACT_B_PATH, encoding="utf-8") as fh:
                    data = json.load(fh)
                rules = data.get("rules", [])
                if is_edit:
                    idx = next((i for i, r in enumerate(rules) if r.get("id") == existing_id), None)
                    if idx is None:
                        raise ValueError(f"Rule {existing_id} not found")
                    rules[idx] = payload
                else:
                    if any(r.get("id") == payload.get("id") for r in rules):
                        raise ValueError(f"Rule ID {payload.get('id')} already exists")
                    rules.append(payload)
                data["rules"] = rules
                with open(_ARTIFACT_B_PATH, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2, ensure_ascii=False)
                self.after(0, lambda: on_ok({}))
            except Exception as e:
                self.after(0, lambda: on_err(str(e)))

        threading.Thread(target=_thread, daemon=True).start()

    def _artifact_delete_rule(self, rule_id, on_ok, on_err):
        def _thread():
            try:
                url = self._settings.get("api_url", "http://localhost:8000") + f"/rules/{rule_id}"
                resp = requests.delete(url, timeout=5)
                resp.raise_for_status()
                self.after(0, lambda: on_ok(resp.json()))
                return
            except Exception:
                pass
            try:
                with open(_ARTIFACT_B_PATH, encoding="utf-8") as fh:
                    data = json.load(fh)
                rules = data.get("rules", [])
                before = len(rules)
                rules  = [r for r in rules if r.get("id") != rule_id]
                if len(rules) == before:
                    raise ValueError(f"Rule {rule_id} not found")
                data["rules"] = rules
                with open(_ARTIFACT_B_PATH, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=2, ensure_ascii=False)
                self.after(0, lambda: on_ok({}))
            except Exception as e:
                self.after(0, lambda: on_err(str(e)))

        threading.Thread(target=_thread, daemon=True).start()

    # ── Docx download ─────────────────────────────────────────────────────────

    def _download_docx(self, report_id):
        def _thread():
            try:
                api_url = self._settings.get("api_url", "http://localhost:8000")
                resp = requests.get(
                    f"{api_url}/reports/{report_id}/download-docx", timeout=60
                )
                resp.raise_for_status()
                suggested = f"compliance_report_{report_id}.docx"
                cd = resp.headers.get("content-disposition", "")
                if "filename=" in cd:
                    suggested = cd.split("filename=")[-1].strip().strip('"')
                self.after(0, lambda: self._save_docx(resp.content, suggested))
            except Exception as e:
                self.after(0, lambda: self._show_docx_error(str(e)))

        threading.Thread(target=_thread, daemon=True).start()

    def _save_docx(self, content, suggested_filename):
        path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx")],
            initialfile=suggested_filename,
        )
        if not path:
            return
        try:
            with open(path, "wb") as fh:
                fh.write(content)
            if sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                os.startfile(path)
        except Exception as e:
            self._show_docx_error(str(e))

    def _show_docx_error(self, msg):
        win = ctk.CTkToplevel(self)
        win.title("Download Error")
        win.geometry("440x200")
        win.configure(fg_color=BG)
        win.grab_set()
        f = ctk.CTkFrame(win, fg_color=BG)
        f.pack(fill="both", padx=32, pady=32)
        ctk.CTkLabel(f, text="Download failed",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=ERROR).pack(anchor="w")
        _label(f, msg, size=13, colour=TXT, wraplength=370).pack(anchor="w", pady=(8, 16))
        _btn(f, "Close", win.destroy, height=36, width=100).pack(anchor="w")

    # ── Shared helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _show_err(frame, lbl, msg):
        lbl.configure(text=f"⚠  {msg}")
        frame.pack(fill="x", padx=32, pady=(0, 12))


# ── Entry point ───────────────────────────────────────────────────────────────

def start_app():
    app = SCCApp()
    app.mainloop()
