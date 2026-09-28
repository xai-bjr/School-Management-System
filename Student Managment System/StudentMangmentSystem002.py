"""
EduDash - Student Management System (CSV-backed)
------------------------------------------------
Files created automatically inside ./data/
    users.csv         -> accounts (passwords are salted + hashed, never plain text)
    students.csv      -> student records (auto-saved on every change)
    activity_log.csv  -> audit trail (who did what, when)
    backups/          -> automatic backup copy before every import

Default admin on first run:  username: admin   password: Admin@123
(Change it: create your own account, promote it to admin, delete the default.)
"""

import csv
import hashlib
import hmac
import os
import re
import secrets
import shutil
import time
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

# ======================================================================
#  PATHS & CONSTANTS
# ======================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
USERS_CSV = os.path.join(DATA_DIR, "users.csv")
STUDENTS_CSV = os.path.join(DATA_DIR, "students.csv")
LOG_CSV = os.path.join(DATA_DIR, "activity_log.csv")

USER_FIELDS = ["username", "full_name", "role", "salt", "password_hash", "created"]
STUDENT_FIELDS = ["roll_no", "name", "course", "marks"]
LOG_FIELDS = ["timestamp", "user", "action", "detail"]

PBKDF2_ROUNDS = 200_000
GRADES = ["A+", "A", "B", "C", "D", "F"]
PASS_MARK = 50

ACCENT = "#6366F1"
ACCENT_HOVER = "#4F46E5"
DANGER = "#EF4444"
DANGER_HOVER = "#DC2626"
SUCCESS = "#10B981"


# ======================================================================
#  LOW-LEVEL CSV HELPERS
# ======================================================================
def ensure_dirs():
    os.makedirs(BACKUP_DIR, exist_ok=True)


def read_rows(path):
    """Read a CSV into a list of dicts. Returns [] if file is missing."""
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_rows(path, fields, rows):
    """Atomic write: write to a temp file, then swap it in.
    If the app crashes mid-write, the old file stays intact."""
    ensure_dirs()
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)


def safe_cell(value):
    """Stop CSV/Excel formula injection when exporting (=, +, -, @ prefixes)."""
    text = str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def log_action(user, action, detail=""):
    ensure_dirs()
    new_file = not os.path.exists(LOG_CSV)
    with open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(LOG_FIELDS)
        w.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user, action, detail])


# ======================================================================
#  USERS (login / sign up)
# ======================================================================
class UserStore:
    def __init__(self):
        ensure_dirs()
        if not os.path.exists(USERS_CSV) or not read_rows(USERS_CSV):
            self._create_default_admin()

    @staticmethod
    def _hash(password, salt_hex=None):
        salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
        return salt.hex(), digest.hex()

    def _create_default_admin(self):
        salt, h = self._hash("Admin@123")
        write_rows(USERS_CSV, USER_FIELDS, [{
            "username": "admin", "full_name": "Administrator", "role": "admin",
            "salt": salt, "password_hash": h,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }])

    def all(self):
        return read_rows(USERS_CSV)

    def find(self, username):
        for u in self.all():
            if u["username"].lower() == username.lower():
                return u
        return None

    def signup(self, full_name, username, password, confirm):
        full_name, username = full_name.strip(), username.strip()
        if not full_name:
            return False, "Full name is required."
        if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", username):
            return False, "Username: 3-20 letters, digits or underscore."
        if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            return False, "Password needs 8+ characters with a letter and a digit."
        if password != confirm:
            return False, "Passwords do not match."
        if self.find(username):
            return False, "That username is already taken."
        salt, h = self._hash(password)
        rows = self.all()
        rows.append({
            "username": username, "full_name": full_name, "role": "staff",
            "salt": salt, "password_hash": h,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        write_rows(USERS_CSV, USER_FIELDS, rows)
        log_action(username, "SIGNUP", "New staff account created")
        return True, "Account created! You can log in now."

    def authenticate(self, username, password):
        user = self.find(username.strip())
        if not user:
            self._hash(password)  # burn same time so timing doesn't reveal valid usernames
            return None
        _, h = self._hash(password, user["salt"])
        return user if hmac.compare_digest(h, user["password_hash"]) else None

    def admin_count(self):
        return sum(1 for u in self.all() if u["role"] == "admin")

    def set_role(self, username, role):
        rows = self.all()
        for u in rows:
            if u["username"] == username:
                u["role"] = role
        write_rows(USERS_CSV, USER_FIELDS, rows)

    def delete(self, username):
        rows = [u for u in self.all() if u["username"] != username]
        write_rows(USERS_CSV, USER_FIELDS, rows)


# ======================================================================
#  STUDENTS
# ======================================================================
class Student:
    def __init__(self, roll_no, name, course, marks):
        self.roll_no = int(roll_no)
        self.name = name
        self.course = course
        self.marks = float(marks)

    @property
    def grade(self):
        for limit, g in ((90, "A+"), (80, "A"), (70, "B"), (60, "C"), (50, "D")):
            if self.marks >= limit:
                return g
        return "F"

    @property
    def status(self):
        return "Pass" if self.marks >= PASS_MARK else "Fail"

    def as_row(self):
        return {"roll_no": self.roll_no, "name": self.name,
                "course": self.course, "marks": self.marks}


def parse_student(row):
    """Validate one CSV row -> Student. Raises ValueError with a readable message."""
    try:
        roll = int(str(row.get("roll_no", "")).strip())
    except ValueError:
        raise ValueError("roll_no must be a whole number")
    if roll <= 0:
        raise ValueError("roll_no must be positive")
    name = str(row.get("name", "")).strip()
    course = str(row.get("course", "")).strip()
    if not name or not course:
        raise ValueError("name and course cannot be empty")
    try:
        marks = float(str(row.get("marks", "")).strip())
    except ValueError:
        raise ValueError("marks must be a number")
    if not 0 <= marks <= 100:
        raise ValueError("marks must be between 0 and 100")
    return Student(roll, name, course, marks)


HEADER_ALIASES = {
    "roll_no": "roll_no", "roll": "roll_no", "rollno": "roll_no", "roll_number": "roll_no", "id": "roll_no",
    "name": "name", "full_name": "name", "student_name": "name",
    "course": "course", "subject": "course", "program": "course",
    "marks": "marks", "score": "marks", "grade_points": "marks",
}


class StudentStore:
    def __init__(self):
        ensure_dirs()
        self.students = {}
        if os.path.exists(STUDENTS_CSV):
            self.load()
        else:
            for s in (Student(101, "Alice Smith", "Computer Science", 92.5),
                      Student(102, "Bob Jones", "Electrical Eng.", 78.0),
                      Student(103, "Charlie Brown", "Business Admin", 85.4),
                      Student(104, "Diana Prince", "Computer Science", 96.0)):
                self.students[s.roll_no] = s
            self.save()

    def load(self):
        self.students.clear()
        for row in read_rows(STUDENTS_CSV):
            try:
                s = parse_student(row)
                self.students[s.roll_no] = s
            except ValueError:
                continue  # skip corrupt rows instead of crashing

    def save(self):
        write_rows(STUDENTS_CSV, STUDENT_FIELDS,
                   [s.as_row() for s in sorted(self.students.values(), key=lambda s: s.roll_no)])

    def courses(self):
        return sorted({s.course for s in self.students.values()})

    def backup(self):
        if os.path.exists(STUDENTS_CSV):
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(BACKUP_DIR, f"students_{stamp}.csv")
            shutil.copy2(STUDENTS_CSV, dest)
            return dest

    def import_file(self, path, overwrite):
        """Returns dict(added, updated, skipped, errors[list of str])."""
        result = {"added": 0, "updated": 0, "skipped": 0, "errors": []}
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("The file is empty.")
            mapping = {}
            for h in reader.fieldnames:
                key = HEADER_ALIASES.get(h.strip().lower().replace(" ", "_"))
                if key:
                    mapping[h] = key
            missing = set(STUDENT_FIELDS) - set(mapping.values())
            if missing:
                raise ValueError("Missing column(s): " + ", ".join(sorted(missing))
                                 + "\nExpected: roll_no, name, course, marks")
            for line_no, raw in enumerate(reader, start=2):
                row = {mapping[k]: v for k, v in raw.items() if k in mapping}
                try:
                    s = parse_student(row)
                except ValueError as e:
                    result["errors"].append(f"Line {line_no}: {e}")
                    continue
                if s.roll_no in self.students:
                    if overwrite:
                        self.students[s.roll_no] = s
                        result["updated"] += 1
                    else:
                        result["skipped"] += 1
                else:
                    self.students[s.roll_no] = s
                    result["added"] += 1
        self.save()
        return result

    def export_file(self, path, students):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:  # BOM so Excel opens it cleanly
            w = csv.writer(f)
            w.writerow(["roll_no", "name", "course", "marks", "grade", "status"])
            for s in students:
                w.writerow([s.roll_no, safe_cell(s.name), safe_cell(s.course),
                            s.marks, s.grade, s.status])

    @staticmethod
    def write_template(path):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(STUDENT_FIELDS)
            w.writerow([201, "Example Student", "Computer Science", 88.5])


# ======================================================================
#  TREEVIEW STYLING (follows dark / light mode)
# ======================================================================
def style_tree():
    dark = ctk.get_appearance_mode() == "Dark"
    bg = "#1E1E2E" if dark else "#FFFFFF"
    fg = "#E5E7EB" if dark else "#111827"
    head = "#2A2A3C" if dark else "#E5E7EB"
    s = ttk.Style()
    s.theme_use("clam")
    s.configure("Edu.Treeview", background=bg, foreground=fg, fieldbackground=bg,
                rowheight=36, borderwidth=0, font=("Segoe UI", 10))
    s.configure("Edu.Treeview.Heading", background=head, foreground=fg,
                font=("Segoe UI", 10, "bold"), borderwidth=0, relief="flat", padding=8)
    s.map("Edu.Treeview", background=[("selected", ACCENT)], foreground=[("selected", "#FFFFFF")])
    s.map("Edu.Treeview.Heading", background=[("active", head)])


def make_tree(parent, columns, widths, anchors=None):
    """Build a styled Treeview + scrollbar inside `parent`. Returns the tree."""
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)
    tree = ttk.Treeview(parent, columns=[c[0] for c in columns], show="headings",
                        selectmode="browse", style="Edu.Treeview")
    for i, (key, title) in enumerate(columns):
        tree.heading(key, text=title)
        tree.column(key, width=widths[i], anchor=(anchors or {}).get(key, "w"))
    sb = ctk.CTkScrollbar(parent, command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
    sb.grid(row=0, column=1, sticky="ns", pady=10, padx=(0, 4))
    return tree


# ======================================================================
#  LOGIN / SIGN UP SCREEN
# ======================================================================
class AuthFrame(ctk.CTkFrame):
    def __init__(self, app):
        super().__init__(app, fg_color="transparent")
        self.app = app
        self.fails = 0
        self.locked_until = 0

        card = ctk.CTkFrame(self, corner_radius=24, width=430)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="🎓", font=ctk.CTkFont(size=46)).grid(row=0, column=0, pady=(30, 0))
        ctk.CTkLabel(card, text="EduDash", font=ctk.CTkFont(size=28, weight="bold")).grid(row=1, column=0)
        self.subtitle = ctk.CTkLabel(card, text="Welcome back! Please sign in.",
                                     text_color=("gray40", "gray65"))
        self.subtitle.grid(row=2, column=0, pady=(0, 14))

        self.switch = ctk.CTkSegmentedButton(card, values=["Login", "Sign Up"], command=self._switch,
                                             selected_color=ACCENT, selected_hover_color=ACCENT_HOVER)
        self.switch.set("Login")
        self.switch.grid(row=3, column=0, padx=40, pady=(0, 14), sticky="ew")

        self.ent_name = ctk.CTkEntry(card, placeholder_text="👤  Full name", height=42, corner_radius=10)
        self.ent_name.grid(row=4, column=0, padx=40, pady=6, sticky="ew")
        self.ent_user = ctk.CTkEntry(card, placeholder_text="📧  Username", height=42, corner_radius=10)
        self.ent_user.grid(row=5, column=0, padx=40, pady=6, sticky="ew")
        self.ent_pass = ctk.CTkEntry(card, placeholder_text="🔒  Password", show="•",
                                     height=42, corner_radius=10)
        self.ent_pass.grid(row=6, column=0, padx=40, pady=6, sticky="ew")
        self.ent_conf = ctk.CTkEntry(card, placeholder_text="🔒  Confirm password", show="•",
                                     height=42, corner_radius=10)
        self.ent_conf.grid(row=7, column=0, padx=40, pady=6, sticky="ew")

        self.show_pw = ctk.CTkCheckBox(card, text="Show password", command=self._toggle_pw,
                                       fg_color=ACCENT, hover_color=ACCENT_HOVER)
        self.show_pw.grid(row=8, column=0, padx=42, pady=(6, 0), sticky="w")

        self.msg = ctk.CTkLabel(card, text="", wraplength=340, text_color=DANGER)
        self.msg.grid(row=9, column=0, padx=40, pady=(8, 0))

        self.btn = ctk.CTkButton(card, text="Login", height=44, corner_radius=10,
                                 font=ctk.CTkFont(size=15, weight="bold"),
                                 fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self._submit)
        self.btn.grid(row=10, column=0, padx=40, pady=(10, 30), sticky="ew")

        for e in (self.ent_name, self.ent_user, self.ent_pass, self.ent_conf):
            e.bind("<Return>", lambda _e: self._submit())
        self._switch("Login")

    def _switch(self, mode):
        signup = mode == "Sign Up"
        if signup:
            self.ent_name.grid()
            self.ent_conf.grid()
        else:
            self.ent_name.grid_remove()
            self.ent_conf.grid_remove()
        self.btn.configure(text="Create Account" if signup else "Login")
        self.subtitle.configure(text="Create your staff account." if signup else "Welcome back! Please sign in.")
        self.msg.configure(text="")

    def _toggle_pw(self):
        ch = "" if self.show_pw.get() else "•"
        self.ent_pass.configure(show=ch)
        self.ent_conf.configure(show=ch)

    def _say(self, text, ok=False):
        self.msg.configure(text=text, text_color=SUCCESS if ok else DANGER)

    def _submit(self):
        if self.switch.get() == "Sign Up":
            ok, text = self.app.users.signup(self.ent_name.get(), self.ent_user.get(),
                                             self.ent_pass.get(), self.ent_conf.get())
            if ok:
                name = self.ent_user.get()
                for e in (self.ent_name, self.ent_pass, self.ent_conf):
                    e.delete(0, "end")
                self.switch.set("Login")
                self._switch("Login")
                self.ent_user.delete(0, "end")
                self.ent_user.insert(0, name)
            self._say(text, ok)
            return

        wait = int(self.locked_until - time.time())
        if wait > 0:
            self._say(f"Too many attempts. Try again in {wait}s.")
            return
        user = self.app.users.authenticate(self.ent_user.get(), self.ent_pass.get())
        if user:
            self.app.on_login(user)
        else:
            self.fails += 1
            log_action(self.ent_user.get().strip() or "?", "LOGIN_FAILED", f"attempt {self.fails}")
            if self.fails >= 5:
                self.locked_until = time.time() + 30
                self.fails = 0
                self._say("Too many failed attempts. Locked for 30 seconds.")
            else:
                self._say("Invalid username or password.")


# ======================================================================
#  ADD / EDIT DIALOG
# ======================================================================
class StudentDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, on_save, student=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x460")
        self.resizable(False, False)
        self.on_save = on_save
        self.after(50, self.grab_set)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=25, pady=(25, 10), sticky="w")

        self.ent_roll = ctk.CTkEntry(self, placeholder_text="Roll number", height=40)
        self.ent_name = ctk.CTkEntry(self, placeholder_text="Full name", height=40)
        self.ent_course = ctk.CTkEntry(self, placeholder_text="Course", height=40)
        self.ent_marks = ctk.CTkEntry(self, placeholder_text="Marks (0 - 100)", height=40)
        for i, e in enumerate((self.ent_roll, self.ent_name, self.ent_course, self.ent_marks), start=1):
            e.grid(row=i, column=0, padx=25, pady=8, sticky="ew")

        if student:
            self.ent_roll.insert(0, str(student.roll_no))
            self.ent_roll.configure(state="disabled")
            self.ent_name.insert(0, student.name)
            self.ent_course.insert(0, student.course)
            self.ent_marks.insert(0, str(student.marks))

        ctk.CTkButton(self, text="Save Record", height=42, fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      font=ctk.CTkFont(weight="bold"), command=self._save).grid(
            row=5, column=0, padx=25, pady=(20, 8), sticky="ew")
        ctk.CTkButton(self, text="Cancel", height=38, fg_color="transparent", border_width=1,
                      text_color=("gray20", "gray80"), command=self.destroy).grid(
            row=6, column=0, padx=25, sticky="ew")

    def _save(self):
        try:
            s = parse_student({"roll_no": self.ent_roll.get(), "name": self.ent_name.get(),
                               "course": self.ent_course.get(), "marks": self.ent_marks.get()})
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e), parent=self)
            return
        if self.on_save(s):
            self.destroy()


# ======================================================================
#  MAIN DASHBOARD
# ======================================================================
class MainView(ctk.CTkFrame):
    def __init__(self, app):
        super().__init__(app, fg_color="transparent")
        self.app = app
        self.store = app.students
        self.user = app.current_user
        self.is_admin = self.user["role"] == "admin"
        self.sort_col, self.sort_rev = "roll_no", False

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=25, pady=20)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.pages = {
            "dashboard": self._build_dashboard(),
            "students": self._build_students(),
        }
        if self.is_admin:
            self.pages["users"] = self._build_users()
            self.pages["log"] = self._build_log()

        self.show_page("dashboard")
        self.refresh_all()

    # ---------------- sidebar ----------------
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=230, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_rowconfigure(20, weight=1)

        ctk.CTkLabel(sb, text="🎓 EduDash", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, padx=22, pady=(28, 4), sticky="w")
        ctk.CTkLabel(sb, text=f"{self.user['full_name']}\n({self.user['role']})",
                     justify="left", text_color=("gray40", "gray65")).grid(
            row=1, column=0, padx=22, pady=(0, 22), sticky="w")

        self.nav = {}
        items = [("dashboard", "📊  Dashboard"), ("students", "👥  Students")]
        if self.is_admin:
            items += [("users", "🔑  Users"), ("log", "📜  Activity Log")]
        for i, (key, text) in enumerate(items, start=2):
            b = ctk.CTkButton(sb, text=text, anchor="w", height=42, corner_radius=10,
                              fg_color="transparent", text_color=("gray10", "gray90"),
                              hover_color=("gray80", "gray25"),
                              command=lambda k=key: self.show_page(k))
            b.grid(row=i, column=0, padx=14, pady=3, sticky="ew")
            self.nav[key] = b

        ctk.CTkLabel(sb, text="Appearance", font=ctk.CTkFont(size=12)).grid(
            row=21, column=0, padx=22, sticky="w")
        menu = ctk.CTkOptionMenu(sb, values=["Dark", "Light", "System"], command=self._set_mode,
                                 fg_color=ACCENT, button_color=ACCENT_HOVER)
        menu.set(ctk.get_appearance_mode())
        menu.grid(row=22, column=0, padx=20, pady=(4, 10), sticky="ew")

        ctk.CTkButton(sb, text="⏻  Logout", height=40, fg_color=DANGER, hover_color=DANGER_HOVER,
                      command=self.app.logout).grid(row=23, column=0, padx=20, pady=(0, 22), sticky="ew")

    def _set_mode(self, mode):
        ctk.set_appearance_mode(mode)
        style_tree()

    def show_page(self, key):
        for k, page in self.pages.items():
            page.grid_remove()
            self.nav[k].configure(fg_color="transparent")
        self.pages[key].grid(row=0, column=0, sticky="nsew")
        self.nav[key].configure(fg_color=ACCENT, text_color="white")
        if key == "users":
            self.refresh_users()
        elif key == "log":
            self.refresh_log()

    # ---------------- dashboard page ----------------
    def _stat_card(self, parent, title, col, icon):
        card = ctk.CTkFrame(parent, corner_radius=16)
        card.grid(row=0, column=col, padx=6, sticky="ew")
        ctk.CTkLabel(card, text=f"{icon}  {title}", text_color=("gray40", "gray65"),
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=18, pady=(16, 0))
        val = ctk.CTkLabel(card, text="-", font=ctk.CTkFont(size=24, weight="bold"))
        val.pack(anchor="w", padx=18, pady=(2, 16))
        return val

    def _build_dashboard(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(page, text=f"Hello, {self.user['full_name'].split()[0]} 👋",
                     font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, sticky="w", pady=(0, 14))

        cards = ctk.CTkFrame(page, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        cards.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="c")
        self.c_total = self._stat_card(cards, "Total Students", 0, "👥")
        self.c_avg = self._stat_card(cards, "Average Marks", 1, "📈")
        self.c_pass = self._stat_card(cards, "Pass Rate", 2, "✅")
        self.c_top = self._stat_card(cards, "Top Performer", 3, "🏆")

        lower = ctk.CTkFrame(page, fg_color="transparent")
        lower.grid(row=2, column=0, sticky="nsew")
        lower.grid_columnconfigure((0, 1), weight=1, uniform="l")
        lower.grid_rowconfigure(0, weight=1)

        gbox = ctk.CTkFrame(lower, corner_radius=16)
        gbox.grid(row=0, column=0, sticky="nsew", padx=(6, 6))
        ctk.CTkLabel(gbox, text="Grade Distribution", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", padx=20, pady=(18, 10))
        self.grade_bars = {}
        for g in GRADES:
            row = ctk.CTkFrame(gbox, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(row, text=g, width=34, anchor="w").pack(side="left")
            bar = ctk.CTkProgressBar(row, progress_color=DANGER if g == "F" else ACCENT, height=12)
            bar.set(0)
            bar.pack(side="left", fill="x", expand=True, padx=8)
            cnt = ctk.CTkLabel(row, text="0", width=30, anchor="e")
            cnt.pack(side="left")
            self.grade_bars[g] = (bar, cnt)

        self.course_box = ctk.CTkScrollableFrame(lower, corner_radius=16, label_text="Average by Course",
                                                 label_font=ctk.CTkFont(size=16, weight="bold"))
        self.course_box.grid(row=0, column=1, sticky="nsew", padx=(6, 6))
        return page

    def refresh_dashboard(self):
        studs = list(self.store.students.values())
        total = len(studs)
        self.c_total.configure(text=str(total))
        if total:
            avg = sum(s.marks for s in studs) / total
            passed = sum(1 for s in studs if s.marks >= PASS_MARK)
            top = max(studs, key=lambda s: s.marks)
            self.c_avg.configure(text=f"{avg:.1f}")
            self.c_pass.configure(text=f"{passed / total * 100:.0f}%")
            self.c_top.configure(text=f"{top.name.split()[0]} ({top.marks:g})")
        else:
            self.c_avg.configure(text="0.0")
            self.c_pass.configure(text="0%")
            self.c_top.configure(text="N/A")

        for g, (bar, cnt) in self.grade_bars.items():
            n = sum(1 for s in studs if s.grade == g)
            bar.set(n / total if total else 0)
            cnt.configure(text=str(n))

        for w in self.course_box.winfo_children():
            w.destroy()
        by_course = {}
        for s in studs:
            by_course.setdefault(s.course, []).append(s.marks)
        for course, marks in sorted(by_course.items()):
            avg = sum(marks) / len(marks)
            ctk.CTkLabel(self.course_box, text=f"{course}  ({len(marks)} students)",
                         anchor="w").pack(fill="x", padx=8, pady=(8, 0))
            bar = ctk.CTkProgressBar(self.course_box, progress_color=SUCCESS, height=10)
            bar.set(avg / 100)
            bar.pack(fill="x", padx=8, pady=(2, 0))
            ctk.CTkLabel(self.course_box, text=f"avg {avg:.1f}", anchor="w",
                         text_color=("gray40", "gray65"), font=ctk.CTkFont(size=11)).pack(fill="x", padx=8)

    # ---------------- students page ----------------
    def _build_students(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(page, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.grid_columnconfigure(0, weight=1)
        self.search = ctk.CTkEntry(top, placeholder_text="🔍  Search name, course or roll no...",
                                   height=40, corner_radius=10)
        self.search.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search.bind("<KeyRelease>", lambda _e: self.refresh_students())
        self.course_filter = ctk.CTkOptionMenu(top, values=["All courses"], height=40, width=170,
                                               command=lambda _v: self.refresh_students(),
                                               fg_color=ACCENT, button_color=ACCENT_HOVER)
        self.course_filter.grid(row=0, column=1)

        btns = ctk.CTkFrame(page, fg_color="transparent")
        btns.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        def mk(text, cmd, color=ACCENT, hover=ACCENT_HOVER, enabled=True):
            b = ctk.CTkButton(btns, text=text, height=36, corner_radius=8, width=110,
                              fg_color=color, hover_color=hover, command=cmd,
                              state="normal" if enabled else "disabled")
            b.pack(side="left", padx=(0, 8))
            return b

        mk("＋ Add", self.open_add)
        mk("✏️ Edit", self.open_edit, "#3B82F6", "#2563EB")
        mk("🗑️ Delete", self.delete_student, DANGER, DANGER_HOVER, self.is_admin)
        mk("📥 Import CSV", self.import_csv, SUCCESS, "#059669", self.is_admin)
        mk("📤 Export CSV", self.export_csv, "#8B5CF6", "#7C3AED")
        mk("📄 Template", self.save_template, "#64748B", "#475569")

        box = ctk.CTkFrame(page, corner_radius=16)
        box.grid(row=2, column=0, sticky="nsew")
        cols = [("roll_no", "Roll No"), ("name", "Full Name"), ("course", "Course"),
                ("marks", "Marks"), ("grade", "Grade"), ("status", "Status")]
        self.tree = make_tree(box, cols, [90, 230, 190, 90, 80, 90],
                              {"roll_no": "center", "marks": "center", "grade": "center", "status": "center"})
        self.tree.tag_configure("fail", foreground="#F87171")
        for key, title in cols:
            self.tree.heading(key, text=title, command=lambda k=key: self.sort_by(k))
        self.tree.bind("<Double-1>", lambda _e: self.open_edit())
        self.col_titles = dict(cols)

        self.status = ctk.CTkLabel(page, text="", anchor="w", text_color=("gray40", "gray65"))
        self.status.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        return page

    def sort_by(self, col):
        self.sort_rev = (not self.sort_rev) if self.sort_col == col else False
        self.sort_col = col
        self.refresh_students()

    def refresh_students(self):
        q = self.search.get().strip().lower()
        course = self.course_filter.get()
        studs = [s for s in self.store.students.values()
                 if (course == "All courses" or s.course == course)
                 and (not q or q in str(s.roll_no) or q in s.name.lower() or q in s.course.lower())]

        key_fn = {"roll_no": lambda s: s.roll_no, "marks": lambda s: s.marks,
                  "name": lambda s: s.name.lower(), "course": lambda s: s.course.lower(),
                  "grade": lambda s: -s.marks, "status": lambda s: s.status}[self.sort_col]
        studs.sort(key=key_fn, reverse=self.sort_rev)
        self.visible = studs

        for col, title in self.col_titles.items():
            arrow = (" ▼" if self.sort_rev else " ▲") if col == self.sort_col else ""
            self.tree.heading(col, text=title + arrow)

        self.tree.delete(*self.tree.get_children())
        for s in studs:
            self.tree.insert("", "end", iid=str(s.roll_no),
                             values=(s.roll_no, s.name, s.course, f"{s.marks:.1f}", s.grade, s.status),
                             tags=("fail",) if s.status == "Fail" else ())
        self.status.configure(text=f"Showing {len(studs)} of {len(self.store.students)} students")

    def refresh_all(self):
        courses = ["All courses"] + self.store.courses()
        self.course_filter.configure(values=courses)
        if self.course_filter.get() not in courses:
            self.course_filter.set("All courses")
        self.refresh_students()
        self.refresh_dashboard()

    def _selected(self, action):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", f"Select a student to {action} first.")
            return None
        return self.store.students[int(sel[0])]

    def _flash(self, text):
        self.status.configure(text="✔ " + text, text_color=SUCCESS)
        self.after(3500, lambda: self.status.configure(text_color=("gray40", "gray65")))

    # ---------------- CRUD ----------------
    def open_add(self):
        StudentDialog(self.app, "Add New Student", self._add)

    def _add(self, s):
        if s.roll_no in self.store.students:
            messagebox.showerror("Duplicate", f"Roll No {s.roll_no} is already registered!")
            return False
        self.store.students[s.roll_no] = s
        self.store.save()
        log_action(self.user["username"], "ADD_STUDENT", f"{s.roll_no} {s.name}")
        self.refresh_all()
        self._flash(f"Added {s.name}")
        return True

    def open_edit(self):
        s = self._selected("edit")
        if s:
            StudentDialog(self.app, "Edit Student", self._update, student=s)

    def _update(self, s):
        self.store.students[s.roll_no] = s
        self.store.save()
        log_action(self.user["username"], "EDIT_STUDENT", f"{s.roll_no} {s.name}")
        self.refresh_all()
        self._flash(f"Updated {s.name}")
        return True

    def delete_student(self):
        s = self._selected("delete")
        if s and messagebox.askyesno("Confirm Delete", f"Delete {s.name} (Roll No {s.roll_no})?"):
            del self.store.students[s.roll_no]
            self.store.save()
            log_action(self.user["username"], "DELETE_STUDENT", f"{s.roll_no} {s.name}")
            self.refresh_all()
            self._flash(f"Deleted {s.name}")

    # ---------------- CSV import / export ----------------
    def import_csv(self):
        path = filedialog.askopenfilename(title="Import students", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        choice = messagebox.askyesnocancel(
            "Import mode",
            "If a roll number already exists:\n\nYES  = overwrite it with the file's data\n"
            "NO   = keep the existing record (skip)\nCANCEL = abort import")
        if choice is None:
            return
        backup = self.store.backup()
        try:
            res = self.store.import_file(path, overwrite=choice)
        except (ValueError, OSError, csv.Error) as e:
            messagebox.showerror("Import failed", str(e))
            return
        log_action(self.user["username"], "IMPORT_CSV",
                   f"{os.path.basename(path)} +{res['added']} ~{res['updated']} skip{res['skipped']} err{len(res['errors'])}")
        self.refresh_all()
        report = (f"Added: {res['added']}\nUpdated: {res['updated']}\n"
                  f"Skipped (duplicates): {res['skipped']}\nRejected rows: {len(res['errors'])}")
        if res["errors"]:
            report += "\n\n" + "\n".join(res["errors"][:10])
            if len(res["errors"]) > 10:
                report += f"\n...and {len(res['errors']) - 10} more"
        if backup:
            report += f"\n\nBackup saved: {os.path.basename(backup)}"
        messagebox.showinfo("Import complete", report)

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Export students", defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
            initialfile=f"students_{datetime.now():%Y%m%d}.csv")
        if not path:
            return
        try:
            self.store.export_file(path, getattr(self, "visible", list(self.store.students.values())))
        except OSError as e:
            messagebox.showerror("Export failed", str(e))
            return
        log_action(self.user["username"], "EXPORT_CSV", os.path.basename(path))
        self._flash(f"Exported {len(self.visible)} rows (current filter) to {os.path.basename(path)}")

    def save_template(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="import_template.csv",
                                            filetypes=[("CSV files", "*.csv")])
        if path:
            self.store.write_template(path)
            self._flash("Template saved - fill it in and use Import CSV")

    # ---------------- users page (admin) ----------------
    def _build_users(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(page, text="User Accounts", font=ctk.CTkFont(size=26, weight="bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 12))
        bar = ctk.CTkFrame(page, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkButton(bar, text="⇅ Toggle Admin/Staff", fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self.toggle_role).pack(side="left", padx=(0, 8))
        ctk.CTkButton(bar, text="🗑️ Delete User", fg_color=DANGER, hover_color=DANGER_HOVER,
                      command=self.delete_user).pack(side="left")
        box = ctk.CTkFrame(page, corner_radius=16)
        box.grid(row=2, column=0, sticky="nsew")
        self.user_tree = make_tree(
            box, [("username", "Username"), ("full_name", "Full Name"), ("role", "Role"), ("created", "Created")],
            [150, 230, 100, 160])
        return page

    def refresh_users(self):
        self.user_tree.delete(*self.user_tree.get_children())
        for u in self.app.users.all():
            self.user_tree.insert("", "end", iid=u["username"],
                                  values=(u["username"], u["full_name"], u["role"], u["created"]))

    def _sel_user(self):
        sel = self.user_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Select a user first.")
            return None
        return sel[0]

    def toggle_role(self):
        name = self._sel_user()
        if not name:
            return
        user = self.app.users.find(name)
        new = "staff" if user["role"] == "admin" else "admin"
        if user["role"] == "admin" and self.app.users.admin_count() <= 1:
            messagebox.showerror("Blocked", "You cannot demote the last admin.")
            return
        self.app.users.set_role(name, new)
        log_action(self.user["username"], "ROLE_CHANGE", f"{name} -> {new}")
        self.refresh_users()

    def delete_user(self):
        name = self._sel_user()
        if not name:
            return
        if name == self.user["username"]:
            messagebox.showerror("Blocked", "You cannot delete the account you're logged in with.")
            return
        target = self.app.users.find(name)
        if target["role"] == "admin" and self.app.users.admin_count() <= 1:
            messagebox.showerror("Blocked", "You cannot delete the last admin.")
            return
        if messagebox.askyesno("Confirm", f"Delete user '{name}'?"):
            self.app.users.delete(name)
            log_action(self.user["username"], "DELETE_USER", name)
            self.refresh_users()

    # ---------------- log page (admin) ----------------
    def _build_log(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(page, text="Activity Log", font=ctk.CTkFont(size=26, weight="bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 12))
        ctk.CTkButton(page, text="⟳ Refresh", width=100, fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self.refresh_log).grid(row=1, column=0, sticky="w", pady=(0, 10))
        box = ctk.CTkFrame(page, corner_radius=16)
        box.grid(row=2, column=0, sticky="nsew")
        self.log_tree = make_tree(
            box, [("timestamp", "Time"), ("user", "User"), ("action", "Action"), ("detail", "Detail")],
            [160, 110, 140, 320])
        return page

    def refresh_log(self):
        self.log_tree.delete(*self.log_tree.get_children())
        for r in reversed(read_rows(LOG_CSV)[-300:]):
            self.log_tree.insert("", "end", values=(r["timestamp"], r["user"], r["action"], r["detail"]))


# ======================================================================
#  APP ROOT
# ======================================================================
class EduDashApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("EduDash - Student Management")
        self.geometry("1180x740")
        self.minsize(1000, 650)
        self.users = UserStore()
        self.students = StudentStore()
        self.current_user = None
        style_tree()
        self.show_auth()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def show_auth(self):
        self._clear()
        AuthFrame(self).pack(fill="both", expand=True)

    def on_login(self, user):
        self.current_user = user
        log_action(user["username"], "LOGIN", user["role"])
        self._clear()
        MainView(self).pack(fill="both", expand=True)

    def logout(self):
        if messagebox.askyesno("Logout", "Log out of EduDash?"):
            log_action(self.current_user["username"], "LOGOUT", "")
            self.current_user = None
            self.show_auth()


if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    EduDashApp().mainloop()