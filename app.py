from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, io, csv
from functools import wraps

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "placement.db")
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-for-production")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        registration_no TEXT,
        course TEXT DEFAULT 'B.Tech CSE AI/ML',
        year INTEGER DEFAULT 2,
        cgpa REAL DEFAULT 0,
        skills TEXT DEFAULT '',
        resume_link TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT NOT NULL,
        role_title TEXT NOT NULL,
        description TEXT NOT NULL,
        package_lpa REAL DEFAULT 0,
        min_cgpa REAL DEFAULT 0,
        eligible_years TEXT DEFAULT '2,3,4',
        skills_required TEXT DEFAULT '',
        deadline TEXT DEFAULT '',
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(created_by) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Applied',
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_id, job_id),
        FOREIGN KEY(student_id) REFERENCES users(id),
        FOREIGN KEY(job_id) REFERENCES jobs(id)
    );
    """)
    # Seed demo users only when the database is empty.
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.execute("INSERT INTO users(name,email,password_hash,role,registration_no,course,year,cgpa,skills) VALUES(?,?,?,?,?,?,?,?,?)",
                     ("Placement Admin", "admin@sgtu.demo", generate_password_hash("Admin@123"), "admin", "", "SGTU Placement Cell", 4, 10, "Administration"))
        conn.execute("INSERT INTO users(name,email,password_hash,role,registration_no,course,year,cgpa,skills) VALUES(?,?,?,?,?,?,?,?,?)",
                     ("Aarav Sharma", "student@sgtu.demo", generate_password_hash("Student@123"), "student", "251302220", "B.Tech CSE AI/ML", 2, 8.8, "Python, SQL, HTML, CSS, Machine Learning"))
    if conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0:
        jobs = [
            ("TechNova Solutions", "Python Developer Intern", "Build and test Python APIs, write clean code, and collaborate with the engineering team.", 4.5, 7.0, "2,3,4", "Python, SQL, Git", "2027-01-15"),
            ("DataBridge Analytics", "Data Analyst Intern", "Support data cleaning, dashboard creation, and reporting using spreadsheets and SQL.", 5.0, 7.5, "2,3,4", "SQL, Excel, Power BI", "2027-01-20"),
            ("CloudSprint", "Frontend Developer Intern", "Create responsive interfaces and work with designers to improve user experience.", 3.6, 6.5, "2,3,4", "HTML, CSS, JavaScript", "2027-01-25"),
            ("AI Works Lab", "Machine Learning Intern", "Assist with dataset preparation, baseline ML models, and model evaluation.", 6.0, 8.0, "3,4", "Python, NumPy, ML", "2027-02-01"),
        ]
        conn.executemany("INSERT INTO jobs(company,role_title,description,package_lpa,min_cgpa,eligible_years,skills_required,deadline) VALUES(?,?,?,?,?,?,?,?)", jobs)
    conn.commit()
    conn.close()

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Admin access is required for that page.", "danger")
            return redirect(url_for("dashboard"))
        return fn(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_user():
    if session.get("user_id"):
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
        conn.close()
        return {"current_user": user}
    return {"current_user": None}

@app.route("/")
def index():
    conn = db()
    job_count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    student_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
    application_count = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    latest_jobs = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 3").fetchall()
    conn.close()
    return render_template("index.html", job_count=job_count, student_count=student_count,
                           application_count=application_count, latest_jobs=latest_jobs)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        reg_no = request.form.get("registration_no", "").strip()
        course = request.form.get("course", "B.Tech CSE AI/ML").strip()
        year = request.form.get("year", "2")
        cgpa = request.form.get("cgpa", "0")
        skills = request.form.get("skills", "").strip()
        if not name or not email or len(password) < 8:
            flash("Enter your name/email and a password of at least 8 characters.", "danger")
            return render_template("register.html")
        try:
            conn = db()
            conn.execute("""INSERT INTO users(name,email,password_hash,role,registration_no,course,year,cgpa,skills)
                            VALUES(?,?,?,?,?,?,?,?,?)""",
                         (name, email, generate_password_hash(password), "student", reg_no, course,
                          max(1, min(4, int(year))), max(0, min(10, float(cgpa))), skills))
            conn.commit()
            conn.close()
            flash("Account created. You can now sign in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["name"] = user["name"]
            flash(f"Welcome back, {user['name'].split()[0]}!", "success")
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have signed out.", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    if user["role"] == "admin":
        stats = {
            "students": conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0],
            "jobs": conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
            "applications": conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0],
            "shortlisted": conn.execute("SELECT COUNT(*) FROM applications WHERE status='Shortlisted'").fetchone()[0],
        }
        recent = conn.execute("""SELECT a.id, u.name, u.registration_no, j.company, j.role_title, a.status, a.applied_at
                                 FROM applications a JOIN users u ON a.student_id=u.id
                                 JOIN jobs j ON a.job_id=j.id ORDER BY a.id DESC LIMIT 8""").fetchall()
        conn.close()
        return render_template("admin_dashboard.html", stats=stats, recent=recent)
    applications = conn.execute("""SELECT a.id, a.status, a.applied_at, j.company, j.role_title, j.package_lpa
                                   FROM applications a JOIN jobs j ON a.job_id=j.id
                                   WHERE a.student_id=? ORDER BY a.id DESC""", (user["id"],)).fetchall()
    jobs = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 4").fetchall()
    conn.close()
    return render_template("student_dashboard.html", user=user, applications=applications, jobs=jobs)

@app.route("/jobs")
def jobs():
    search = request.args.get("q", "").strip()
    conn = db()
    if search:
        rows = conn.execute("""SELECT * FROM jobs WHERE company LIKE ? OR role_title LIKE ? OR skills_required LIKE ?
                               ORDER BY id DESC""", (f"%{search}%", f"%{search}%", f"%{search}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
    applied = set()
    if session.get("user_id"):
        applied = {r["job_id"] for r in conn.execute("SELECT job_id FROM applications WHERE student_id=?", (session["user_id"],)).fetchall()}
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone() if session.get("user_id") else None
    conn.close()
    return render_template("jobs.html", jobs=rows, applied=applied, search=search, user=user)

@app.route("/jobs/<int:job_id>/apply", methods=["POST"])
@login_required
def apply(job_id):
    if session.get("role") != "student":
        flash("Only student accounts can apply to jobs.", "warning")
        return redirect(url_for("jobs"))
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        conn.close()
        flash("Job not found.", "danger")
        return redirect(url_for("jobs"))
    eligible_years = [int(x) for x in job["eligible_years"].split(",") if x.strip().isdigit()]
    if user["cgpa"] < job["min_cgpa"] or user["year"] not in eligible_years:
        conn.close()
        flash(f"Not eligible yet. Required CGPA: {job['min_cgpa']:.1f}; eligible years: {job['eligible_years']}.", "warning")
        return redirect(url_for("jobs"))
    try:
        conn.execute("INSERT INTO applications(student_id,job_id) VALUES(?,?)", (user["id"], job_id))
        conn.commit()
        flash("Application submitted successfully.", "success")
    except sqlite3.IntegrityError:
        flash("You have already applied for this role.", "info")
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    conn = db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        course = request.form.get("course", "").strip()
        year = max(1, min(4, int(request.form.get("year", "2"))))
        cgpa = max(0, min(10, float(request.form.get("cgpa", "0"))))
        skills = request.form.get("skills", "").strip()
        resume_link = request.form.get("resume_link", "").strip()
        conn.execute("UPDATE users SET name=?,course=?,year=?,cgpa=?,skills=?,resume_link=? WHERE id=?",
                     (name, course, year, cgpa, skills, resume_link, session["user_id"]))
        conn.commit()
        session["name"] = name
        flash("Profile updated.", "success")
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("profile.html", user=user)

@app.route("/admin/jobs/new", methods=["GET", "POST"])
@admin_required
def new_job():
    if request.method == "POST":
        fields = [request.form.get(k, "").strip() for k in
                  ("company", "role_title", "description", "package_lpa", "min_cgpa", "eligible_years", "skills_required", "deadline")]
        if not fields[0] or not fields[1] or not fields[2]:
            flash("Company, role and description are required.", "danger")
        else:
            conn = db()
            conn.execute("""INSERT INTO jobs(company,role_title,description,package_lpa,min_cgpa,eligible_years,skills_required,deadline,created_by)
                            VALUES(?,?,?,?,?,?,?,?,?)""",
                         (fields[0], fields[1], fields[2], float(fields[3] or 0), float(fields[4] or 0),
                          fields[5] or "2,3,4", fields[6], fields[7], session["user_id"]))
            conn.commit()
            conn.close()
            flash("Job opening published.", "success")
            return redirect(url_for("jobs"))
    return render_template("new_job.html")

@app.route("/admin/applications")
@admin_required
def admin_applications():
    conn = db()
    rows = conn.execute("""SELECT a.id, a.status, a.applied_at, u.name, u.email, u.registration_no, u.course,
                                  u.year, u.cgpa, u.skills, j.company, j.role_title
                           FROM applications a JOIN users u ON a.student_id=u.id
                           JOIN jobs j ON a.job_id=j.id ORDER BY a.id DESC""").fetchall()
    conn.close()
    return render_template("admin_applications.html", applications=rows)

@app.route("/admin/applications/<int:application_id>/status", methods=["POST"])
@admin_required
def update_status(application_id):
    status = request.form.get("status", "Applied")
    allowed = {"Applied", "Under Review", "Shortlisted", "Interview", "Selected", "Rejected"}
    if status not in allowed:
        flash("Invalid application status.", "danger")
    else:
        conn = db()
        conn.execute("UPDATE applications SET status=? WHERE id=?", (status, application_id))
        conn.commit()
        conn.close()
        flash("Application status updated.", "success")
    return redirect(url_for("admin_applications"))

@app.route("/admin/export.csv")
@admin_required
def export_csv():
    conn = db()
    rows = conn.execute("""SELECT u.name,u.email,u.registration_no,u.course,u.year,u.cgpa,u.skills,
                                  j.company,j.role_title,j.package_lpa,a.status,a.applied_at
                           FROM applications a JOIN users u ON a.student_id=u.id
                           JOIN jobs j ON a.job_id=j.id ORDER BY a.id DESC""").fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Name", "Email", "Registration No", "Course", "Year", "CGPA", "Skills",
                     "Company", "Role", "Package LPA", "Status", "Applied At"])
    for row in rows:
        writer.writerow(list(row))
    return send_file(io.BytesIO(output.getvalue().encode("utf-8-sig")), mimetype="text/csv",
                     as_attachment=True, download_name="sgtu_placement_applications.csv")

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

init_db()
if __name__ == "__main__":
    app.run(debug=True)
