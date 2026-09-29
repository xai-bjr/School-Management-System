# 🎓 EduDash - Student Management System

A modern desktop app for managing student records, built with Python and [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter). All data is stored in plain CSV files, so there is no database to set up, and it works with Excel.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

<!-- Add a screenshot after you take one:
![Dashboard](screenshots/dashboard.png)
-->

## ✨ Features

- **Login and Sign Up**: accounts are stored in `users.csv` with salted, hashed passwords (never plain text)
- **Roles**: `admin` has full access; `staff` can add, edit and export
- **Dashboard**: total students, average marks, pass rate, top performer, grade distribution and average marks per course
- **Student management**: add, edit and delete records, with search, course filter and click-to-sort columns
- **CSV import**: validates every row, reports what was added, updated or rejected, and backs up your data first
- **CSV export**: exports the current filtered view and opens cleanly in Excel
- **Import template**: one click gives you a correctly formatted sample file
- **Activity log**: admins can see who logged in, edited, imported or deleted, and when
- **Dark, Light and System themes**

## 📦 Installation

### Requirements
- Python **3.10 or newer** ([download](https://www.python.org/downloads/))
- On Windows, make sure **tcl/tk and IDLE** is ticked in the Python installer (it is by default)
- On Linux you may also need Tk: `sudo apt install python3-tk`

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# 2. (Recommended) create a virtual environment
python -m venv .venv

# Activate it:
#   Windows (PowerShell):  .\.venv\Scripts\Activate.ps1
#   macOS / Linux:         source .venv/bin/activate

# 3. Install dependencies
python -m pip install -r requirements.txt

# 4. Run the app
python student_management.py
```

> **Tip:** Use `python -m pip` instead of plain `pip`. It guarantees the package is installed into the same Python that will run the app.

## 🚀 Usage

### First login

| Username | Password |
|---|---|
| `admin` | `Admin@123` |

> ⚠️ **Change this immediately.** Sign up with your own account, log in as `admin`, promote your account on the **Users** page, log in as yourself, then delete the default `admin` user.

### Creating an account
1. Open the **Sign Up** tab.
2. Enter your full name, a username (3-20 letters, digits or `_`) and a password (8+ characters with at least one letter and one digit).
3. New accounts are created as **staff**. An admin can promote them later.

### Managing students
- **＋ Add**: register a new student
- **✏️ Edit**: select a row and click Edit (or double-click the row)
- **🗑️ Delete**: admin only
- Click any **column heading** to sort. Use the search box and course dropdown to filter.

### Importing from CSV (admin only)
1. Click **📄 Template** to save a sample file, then fill it in (or use your own file).
2. Click **📥 Import CSV** and choose the file.
3. Choose what happens when a roll number already exists:
   - **Yes**: overwrite the existing record
   - **No**: keep the existing record (skip)
   - **Cancel**: abort
4. Read the summary. Invalid rows are listed with their line numbers.

**Required columns:**

```csv
roll_no,name,course,marks
201,Example Student,Computer Science,88.5
```

Some alternative header names are accepted, such as `Roll No`, `Student Name`, `Subject` and `Score`.

**Validation rules:** `roll_no` must be a positive whole number, `name` and `course` cannot be empty, and `marks` must be between 0 and 100.

### Exporting
Click **📤 Export CSV** to save the currently visible students (respecting your search and filter) with their grade and pass/fail status.

## 📊 Grading scale

| Marks | Grade |
|---|---|
| 90-100 | A+ |
| 80-89 | A |
| 70-79 | B |
| 60-69 | C |
| 50-59 | D |
| below 50 | F (Fail) |

## 🗂️ Data files

Created automatically in a `data/` folder next to the script:

| File | Contents |
|---|---|
| `users.csv` | Accounts (username, role, salt, password hash) |
| `students.csv` | Student records, saved after every change |
| `activity_log.csv` | Audit trail of actions |
| `backups/` | Automatic copy of `students.csv` made before each import |

## 🔒 Security notes

- Passwords are hashed with **PBKDF2-HMAC-SHA256** (200,000 rounds) and a unique random salt per user
- Login is locked for 30 seconds after 5 failed attempts
- Exports neutralise cells starting with `=`, `+`, `-` or `@` to prevent CSV/Excel formula injection
- Files are written atomically (temp file, then replace), so a crash mid-save cannot corrupt your data
- **Never commit the `data/` folder to GitHub.** It contains user accounts. The included `.gitignore` already excludes it.

This is a learning and small-office project. For production use, consider a real database, HTTPS-backed authentication and per-user password reset.

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'customtkinter'` | Run `python -m pip install -r requirements.txt` with the **same** Python you use to run the app |
| `No module named 'tkinter'` | Reinstall Python and tick *tcl/tk and IDLE* (Windows), or `sudo apt install python3-tk` (Linux) |
| Table looks wrong after switching theme | Switch the theme once more, or restart the app |
| Excel shows odd characters | Open the file via *Data → From Text/CSV* and choose UTF-8 |

## 🗺️ Roadmap ideas

- Password change and reset
- Attendance tracking
- PDF report cards
- Charts with matplotlib
- Multiple subjects per student

## 🤝 Contributing

Pull requests are welcome.

1. Fork the repo
2. Create a branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

## 📄 License

Released under the [MIT License](LICENSE).
