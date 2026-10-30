# SGTU Student Placement System — Hackathon Starter

A working Flask + SQLite web application with responsive frontend and backend features for a student placement portal. It is a demo/prototype and is **not an official SGT University system**.

## Features
- Responsive landing page and placement statistics
- Student registration and login (hashed passwords)
- Student dashboard and editable profile
- Job listings with search
- Eligibility checks based on CGPA and year
- Apply to jobs and track application status
- Admin dashboard
- Admin can add jobs, update application status, and export applications as CSV
- SQLite database created automatically with demo records

## Requirements
- Python 3.10 or newer
- Internet is not required after dependencies are installed

## Run on Windows
1. Extract the ZIP.
2. Open the extracted folder in VS Code.
3. Open Terminal in that folder.
4. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
5. Activate it:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt:
   ```bat
   .venv\Scripts\activate.bat
   ```
6. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
7. Start the app:
   ```bash
   python app.py
   ```
8. Open `http://127.0.0.1:5000` in your browser.

## Demo accounts
- **Admin:** `admin@sgtu.demo` / `Admin@123`
- **Student:** `student@sgtu.demo` / `Student@123`

Change demo passwords and `SECRET_KEY` before any real deployment. These are demo credentials only.

## Quick demo flow
1. Sign in as admin.
2. Open **Post a Job** and add a role.
3. Open **Applications** to review submissions and change status.
4. Sign out and sign in as the student.
5. Browse jobs, apply to an eligible role, and see the status on the dashboard.
6. Sign back in as admin and download the CSV export.

## Project structure
```
SGTU_Student_Placement_System/
├── app.py
├── requirements.txt
├── README.md
├── placement.db          # created automatically on first run
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── student_dashboard.html
│   ├── admin_dashboard.html
│   ├── jobs.html
│   ├── profile.html
│   ├── new_job.html
│   ├── admin_applications.html
│   └── 404.html
└── static/
    ├── css/style.css
    └── js/main.js
```

## Before presenting at a hackathon
- Replace the demo branding/records with approved university data.
- Add email verification, password reset, CSRF protection, rate limiting, audit logs, and secure production hosting before real use.
- Do not upload real student personal data without permission.
- The placement packages, companies, eligibility criteria, and student records included here are illustrative demo data, not verified SGTU placement information.
