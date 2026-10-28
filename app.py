import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from dotenv import load_dotenv
from db import get_connection, dict_rows

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-local-key")

def list_resumes():
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""SELECT r.resume_id, r.title, p.full_name, p.email, r.updated_at
                       FROM resumes r JOIN profiles p ON p.profile_id=r.profile_id
                       ORDER BY r.updated_at DESC""")
        return dict_rows(cur)

def load_resume(rid):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""SELECT r.resume_id, r.title, r.profile_id, p.full_name, p.email,
                              p.phone, p.city, p.linkedin_url, p.github_url, p.summary
                       FROM resumes r JOIN profiles p ON p.profile_id=r.profile_id
                       WHERE r.resume_id=:rid""", rid=rid)
        row = cur.fetchone()
        if row is None:
            return None
        data = dict(zip([d[0].lower() for d in cur.description], row))
        queries = {
            "education": """SELECT education_id id, institution, degree, field_of_study,
                            TO_CHAR(start_date,'YYYY-MM') start_date,
                            TO_CHAR(end_date,'YYYY-MM') end_date, grade, details
                            FROM education WHERE profile_id=:pid ORDER BY start_date DESC""",
            "experience": """SELECT experience_id id, company, job_title, location,
                             TO_CHAR(start_date,'YYYY-MM') start_date,
                             TO_CHAR(end_date,'YYYY-MM') end_date, is_current, details
                             FROM experience WHERE profile_id=:pid ORDER BY start_date DESC""",
            "skills": """SELECT skill_id id, skill_name, proficiency FROM skills
                         WHERE profile_id=:pid ORDER BY skill_name""",
            "projects": """SELECT project_id id, project_name, tech_stack, project_url, details
                           FROM projects WHERE profile_id=:pid ORDER BY project_id DESC"""
        }
        for key, sql in queries.items():
            cur.execute(sql, pid=data["profile_id"])
            data[key] = dict_rows(cur)
        return data

@app.route("/")
def index():
    try:
        return render_template("index.html", resumes=list_resumes(), db_error=None)
    except Exception as exc:
        app.logger.exception("Oracle connection failed")
        return render_template("index.html", resumes=[], db_error=str(exc))

@app.route("/resume/new", methods=["GET", "POST"])
def new_resume():
    if request.method == "POST":
        name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        if not name or not email:
            flash("Name and email are required.", "error")
            return render_template("editor.html", mode="new", resume=None)
        try:
            with get_connection() as conn, conn.cursor() as cur:
                profile_id, resume_id = cur.var(int), cur.var(int)
                cur.callproc("resume_pkg.create_resume", [
                    name, email, request.form.get("phone", "").strip() or None,
                    request.form.get("city", "").strip() or None,
                    request.form.get("linkedin_url", "").strip() or None,
                    request.form.get("github_url", "").strip() or None,
                    request.form.get("summary", "").strip() or None,
                    request.form.get("title", "").strip() or "Professional Resume",
                    profile_id, resume_id
                ])
                conn.commit()
                rid = int(resume_id.getvalue())
            flash("Profile created. Add your resume sections below.", "success")
            return redirect(url_for("edit_resume", resume_id=rid))
        except Exception:
            app.logger.exception("Resume creation failed")
            flash("Could not save. Check Oracle setup and make sure this email is not already registered.", "error")
    return render_template("editor.html", mode="new", resume=None)

@app.route("/resume/<int:resume_id>/edit", methods=["GET", "POST"])
def edit_resume(resume_id):
    resume = load_resume(resume_id)
    if resume is None:
        abort(404)
    if request.method == "POST":
        section = request.form.get("section")
        f = request.form
        try:
            with get_connection() as conn, conn.cursor() as cur:
                if section == "education":
                    cur.callproc("resume_pkg.add_education", [
                        resume["profile_id"], f["institution"].strip(), f["degree"].strip(),
                        f.get("field_of_study","").strip() or None, f.get("start_date") or None,
                        f.get("end_date") or None, f.get("grade","").strip() or None,
                        f.get("details","").strip() or None])
                elif section == "experience":
                    cur.callproc("resume_pkg.add_experience", [
                        resume["profile_id"], f["company"].strip(), f["job_title"].strip(),
                        f.get("location","").strip() or None, f.get("start_date") or None,
                        f.get("end_date") or None, 1 if f.get("is_current") else 0,
                        f.get("details","").strip() or None])
                elif section == "skill":
                    cur.callproc("resume_pkg.add_skill", [
                        resume["profile_id"], f["skill_name"].strip(), f.get("proficiency","Intermediate")])
                elif section == "project":
                    cur.callproc("resume_pkg.add_project", [
                        resume["profile_id"], f["project_name"].strip(),
                        f.get("tech_stack","").strip() or None, f.get("project_url","").strip() or None,
                        f.get("details","").strip() or None])
                else:
                    flash("Unknown section.", "error")
                    return redirect(url_for("edit_resume", resume_id=resume_id))
                conn.commit()
            flash("Section saved.", "success")
        except Exception:
            app.logger.exception("Section save failed")
            flash("Could not save this section. Check the values and date format (YYYY-MM).", "error")
        return redirect(url_for("edit_resume", resume_id=resume_id))
    return render_template("editor.html", mode="edit", resume=resume)

@app.route("/resume/<int:resume_id>")
def preview_resume(resume_id):
    resume = load_resume(resume_id)
    if resume is None:
        abort(404)
    return render_template("resume.html", resume=resume)

@app.errorhandler(404)
def not_found(_error):
    return render_template("base.html", standalone_message="That resume could not be found."), 404

if __name__ == "__main__":
    app.run(debug=True)
