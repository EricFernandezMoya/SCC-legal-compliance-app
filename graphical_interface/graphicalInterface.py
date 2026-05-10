"""
SCC Compliance Tool — CustomTkinter UI
Sunshine Coast Council branding: primary blue #005B8E, teal #00B5CC.
"""

import json
import os
import threading
from tkinter import filedialog

import customtkinter as ctk
import requests

try:
    import pillow_avif  # noqa: F401  registers avif decoder
except ImportError:
    pass

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

# ── Paths ────────────────────────────────────────────────────────────────────
_BASE         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOGO_PATH    = os.path.join(_BASE, "logo (1).avif")
_SETTINGS_FILE = os.path.join(_BASE, ".scc_settings.json")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_logo(w=176, h=65):
    try:
        from PIL import Image
        img = Image.open(_LOGO_PATH)
        return ctk.CTkImage(img, size=(w, h))
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


def _section_title(parent, text, pady=(0, 20)):
    ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(size=24, weight="bold"),
        text_color=TXT,
    ).pack(anchor="w", pady=pady)


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
    return ctk.CTkButton(parent, **kwargs, **kw)


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
        self.title("SCC Compliance Tool")
        self.geometry("1280x820")
        self.minsize(960, 640)
        self.configure(fg_color=BG)

        self._settings  = _load_settings()
        self._logo_img  = _load_logo()
        self._user      = "User"

        # per-page state
        self._analyse_file  = None
        self._leg_file      = None
        self._leg_review_id = None
        self._leg_decisions = []

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

        # logo or wordmark
        if self._logo_img:
            ctk.CTkLabel(wrap, image=self._logo_img, text="").pack(pady=(0, 28))
        else:
            ctk.CTkLabel(wrap, text="SCC Compliance Tool",
                         font=ctk.CTkFont(size=26, weight="bold"),
                         text_color=PRIMARY).pack(pady=(0, 28))

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

        self._user = u
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

        self._build_sidebar()

        self._content = ctk.CTkFrame(self._root_frame, fg_color=BG, corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        self._pages    = {}
        self._nav_btns = {}

        self._build_dashboard()
        self._build_analyse()
        self._build_reports()
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
            ctk.CTkLabel(logo_area, image=self._logo_img, text="").pack(anchor="w")
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

        items = [
            ("dashboard",   "🏠  Dashboard"),
            ("analyse",     "📄  Analyse Contract"),
            ("reports",     "📊  Reports"),
            ("legislation", "⚖️  Legislation Update"),
            ("settings",    "⚙️  Settings"),
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
        for i in range(3):
            stats_outer.columnconfigure(i, weight=1)

        stat_defs = [
            ("📋", "Total Reports Run", "—",  TXT),
            ("📏", "Rules Monitored",   "31", PRIMARY),
            ("🗓",  "Last Analysis",     "—",  TEAL),
        ]
        self._dash_lbl = {}
        for col, (icon, lbl, val, colour) in enumerate(stat_defs):
            sh2, sc = _make_card(stats_outer)
            sh2.grid(row=0, column=col, sticky="ew",
                     padx=(0, 16) if col < 2 else 0)
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

        _btn(qr, "📄  Analyse a Contract",
             lambda: self._go("analyse"), height=40).pack(side="left", padx=(0, 12))
        _ghost_btn(qr, "📊  View Reports",
                   lambda: self._go("reports"), height=40).pack(side="left", padx=(0, 12))
        _ghost_btn(qr, "⚖️  Legislation Update",
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

        # file upload
        self._a_file_lbl = _upload_box(
            form,
            "Click to browse or drag and drop",
            self._browse_contract,
        )

        # fields
        fr = ctk.CTkFrame(form, fg_color=CARD)
        fr.pack(fill="x", pady=(0, 20))
        fr.columnconfigure(0, weight=1)
        fr.columnconfigure(1, weight=1)

        _label(fr, "Contract ID  *").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._a_cid = _entry(fr, "e.g. 42")
        self._a_cid.grid(row=1, column=0, sticky="ew", padx=(0, 12))

        _label(fr, "Prior Report ID  (optional)").grid(row=0, column=1, sticky="w", pady=(0, 4))
        self._a_prior = _entry(fr, "For year-on-year comparison")
        self._a_prior.grid(row=1, column=1, sticky="ew")

        # run button
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
        self._a_findings = ctk.CTkFrame(self._a_results, fg_color=BG)
        self._a_findings.pack(fill="x", padx=p)

    def _browse_contract(self):
        path = filedialog.askopenfilename(
            title="Select contract file",
            filetypes=[("Documents", "*.pdf *.doc *.docx")],
        )
        if path:
            self._analyse_file = path
            self._a_file_lbl.configure(
                text=os.path.basename(path), text_color=PRIMARY,
            )

    def _run_analysis(self):
        cid = self._a_cid.get().strip()
        if not cid:
            self._show_err(self._a_err, self._a_err_lbl,
                           "Please enter a Contract ID.")
            return
        if not self._analyse_file:
            self._show_err(self._a_err, self._a_err_lbl,
                           "Please select a contract file.")
            return

        prior = self._a_prior.get().strip()
        self._a_err.pack_forget()
        self._a_btn.configure(state="disabled")
        self._a_spin.pack(side="left", padx=12)
        self._a_results.pack_forget()

        def _ok(data):
            self._a_btn.configure(state="normal")
            self._a_spin.pack_forget()
            findings  = data.get("findings", [])
            report_id = data.get("report_id")

            self._a_res_title.configure(
                text=f"Results — Report #{report_id}  ·  {len(findings)} findings"
            )
            for w in self._a_findings.winfo_children():
                w.destroy()
            for f in findings:
                self._finding_card(self._a_findings, f)
            self._a_results.pack(fill="x")

            # update dashboard last-analysis date
            from datetime import date
            self._dash_lbl.get("Last Analysis", ctk.CTkLabel(self, text="")
                               ).configure(text=date.today().strftime("%d %b %Y"))

        def _err(msg):
            self._a_btn.configure(state="normal")
            self._a_spin.pack_forget()
            self._show_err(self._a_err, self._a_err_lbl, msg)

        with open(self._analyse_file, "rb") as fh:
            data = {"contract_id": cid}
            if prior:
                data["prior_report_id"] = prior
            files = {"file": (os.path.basename(self._analyse_file), fh.read())}

        def _thread():
            try:
                url = self._settings.get("api_url", "http://localhost:8000") + "/analyse"
                r = requests.post(url, files=files, data=data, timeout=120)
                r.raise_for_status()
                self.after(0, lambda: _ok(r.json()))
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

        self._r_search = _entry(sr, "Search by Contract ID…", width=280)
        self._r_search.pack(side="left")
        self._r_search.bind("<Return>", lambda _e: self._search_reports())

        _btn(sr, "Search", self._search_reports,
             height=40, width=100).pack(side="left", padx=(12, 0))

        self._r_spin = _label(sr, "  Loading…", colour=TXT2)

        # results list
        self._r_list = ctk.CTkScrollableFrame(page, fg_color=BG, corner_radius=0)
        self._r_list.pack(fill="both", expand=True, padx=p, pady=(0, p))

    def _search_reports(self):
        cid = self._r_search.get().strip()
        if not cid:
            self._show_err(self._r_err, self._r_err_lbl, "Enter a Contract ID.")
            return
        self._r_err.pack_forget()
        self._r_spin.pack(side="left", padx=12)

        def _ok(data):
            self._r_spin.pack_forget()
            for w in self._r_list.winfo_children():
                w.destroy()
            reports = data.get("reports", [])
            if not reports:
                _label(self._r_list, "No reports found for this contract.",
                       size=14, colour=TXT2).pack(pady=32)
                return
            for r in reports:
                self._report_card(self._r_list, r)

        def _err(msg):
            self._r_spin.pack_forget()
            self._show_err(self._r_err, self._r_err_lbl, msg)

        self._api("GET", f"/reports/contract/{cid}", _ok, _err)

    def _report_card(self, parent, r):
        sh = ctk.CTkFrame(parent, fg_color=SHADOW, corner_radius=14)
        sh.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(sh, fg_color=CARD, corner_radius=12)
        inner.pack(fill="both", expand=True, padx=(2, 3), pady=(2, 3))

        c = ctk.CTkFrame(inner, fg_color=CARD)
        c.pack(fill="both", padx=20, pady=16)

        # top row
        top = ctk.CTkFrame(c, fg_color=CARD)
        top.pack(fill="x")
        ctk.CTkLabel(top, text=f"Report  #{r.get('report_id', '?')}",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=TXT).pack(side="left")

        status = (r.get("compliance_status") or "pending_review").lower()
        if "compliant" == status:
            sf, sc_fg, st = "#F0FDF4", SUCCESS, "Compliant"
        elif "non" in status:
            sf, sc_fg, st = "#FEF2F2", ERROR, "Non-compliant"
        else:
            sf, sc_fg, st = "#FFFBEB", WARNING, "Pending Review"

        _badge(top, st, sc_fg, sf).pack(side="right")

        # details
        dt = ctk.CTkFrame(c, fg_color=CARD)
        dt.pack(fill="x", pady=(6, 12))
        created = str(r.get("created_at", ""))[:10]
        _label(dt, f"🗓  {created}  ·  Contract #{r.get('contract_id','?')}",
               size=12).pack(side="left")

        rid = r.get("report_id")
        _ghost_btn(c, "View Details →",
                   lambda r=rid: self._report_detail(r),
                   height=32).pack(anchor="w")

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
                    "rule_title":   risk.get("rule_description", ""),
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
        _section_title(page, "Legislation Update", pady=(p, 16))

        self._l_err, self._l_err_lbl = _err_banner(page)

        # ── Upload card
        sh, uc = _make_card(page)
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

        # ── Proposed changes section (hidden until upload)
        self._l_changes = ctk.CTkFrame(page, fg_color=BG, corner_radius=0)
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
            ("Vector DB",     "ChromaDB  (local)"),
            ("Embeddings",    "voyage-law-2"),
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

    # ── Shared helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _show_err(frame, lbl, msg):
        lbl.configure(text=f"⚠  {msg}")
        frame.pack(fill="x", padx=32, pady=(0, 12))


# ── Entry point ───────────────────────────────────────────────────────────────

def start_app():
    app = SCCApp()
    app.mainloop()
