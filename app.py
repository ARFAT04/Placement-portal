from flask import Flask,render_template,request,redirect,url_for
from flask import session,flash
from werkzeug.utils import secure_filename
import os 
import sqlite3

app=Flask(__name__)
app.secret_key="secret123"

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register",methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form.get("name")
        email=request.form.get("email")
        password=request.form.get("password")

        if not email or not name or not password:
            flash("ALL fields are required")
            return redirect(url_for("register"))
        
        conn=sqlite3.connect("database.db")
        cur=conn.cursor()

        try:
            cur.execute("INSERT INTO students(name,email,password,role) VALUES(?,?,?,?)",
                (name,email,password,"student"))
            conn.commit()
            flash("Registered Successful")

        except sqlite3.IntegrityError:
            flash("Email already exists")
        
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")
   


@app.route("/login",methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form.get("email")
        password=request.form.get("password")

        if not email or not password:
            flash("Fill all fields")
            return redirect(url_for("login"))
        
        conn=sqlite3.connect("database.db")
        cur=conn.cursor()

        cur.execute("SELECT * FROM students WHERE email=? AND password=?",
            (email,password))
        
        user=cur.fetchone()
        conn.close()

        if user:
            if user[8]=="blacklisted":
                flash("You are blacklisted")
                return redirect(url_for("login"))
            
            session['user']=email
            session['role']=user[4]

            flash("Login successful")
            return redirect(url_for("dashboard"))
        
        else:

            flash("Invalid credentials")
            return redirect(url_for("login"))

    return render_template('login.html')

@app.route("/profile",methods=['GET','POST'])
def profile():
    if 'user' not in session or session.get('role')!='student':
        return redirect(url_for("login"))
    
    email=session['user']

    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    if request.method=="POST":
        skills=request.form.get('skills')
        education=request.form.get('education')

        resume_file=request.files.get('resume')

        resume_filename=None

        if resume_file and resume_file.filename!="":
            filename=secure_filename(resume_file.filename)

            os.makedirs("static/resumes",exist_ok=True)

            filepath=os.path.join("static/resumes",filename)
            resume_file.save(filepath) 
            
            resume_filename=filename

        if resume_filename is None:
            cur.execute("SELECT resume FROM students WHERE email=?",(email,))
            result=cur.fetchone()
            resume_filename=result[0] if result else None 

            
        cur.execute(
            "UPDATE students SET skills=?,education=?,resume=? WHERE email=?",
            (skills,education,resume_filename,email)
        )

        conn.commit()
        flash("Profile updated successfully")
        return redirect(url_for("profile"))
    cur.execute(
        "SELECT name,email,skills,education,resume FROM students WHERE email=?",
        (email,)        
    )

    student=cur.fetchone()

    conn.close()

    return render_template("profile.html",student=student)

    

@app.route("/dashboard")
def dashboard():
    if 'user' not in session:
        return redirect(url_for("login"))
    
    role=session.get('role')

    if role=="student":
        conn=sqlite3.connect("database.db")
        cur=conn.cursor()

        student_email=session['user']

        cur.execute(
            """SELECT drive_id,title,company_email,salary
            FROM drives
            WHERE approval_status='approved' AND drive_status='ACTIVE'
            """
        )

        drives=cur.fetchall()

        cur.execute(
            """SELECT drives.title,applications.status
            From applications 
            JOIN drives ON applications.drive_id=drives.drive_id
            WHERE applications.student_email=?""",
            (student_email,)
        )

        applications=cur.fetchall()
        conn.close()

        return render_template("student_dashboard.html",drives=drives,applications=applications)
    
    elif role=="admin":
        conn=sqlite3.connect("database.db")
        cur=conn.cursor()

        

        search=request.args.get("search")
        if search:
            cur.execute(
                "SELECT * FROM students WHERE role='student' AND LOWER(name) LIKE LOWER(?)",
                ('%' + search + '%',)
            )
        else:
            cur.execute("SELECT * FROM students WHERE role='student'")
        students=cur.fetchall()

        if search:
            cur.execute(
                "SELECT * FROM companies WHERE LOWER(name) LIKE LOWER(?)",
                ('%'+search+'%',)
            )
        else:
            cur.execute("SELECT * FROM companies")
        companies=cur.fetchall()

        cur.execute(
            """SELECT students.name,companies.name,drives.title,applications.status
            FROM applications 
            JOIN students ON applications.student_email=students.email
            JOIN drives ON applications.drive_id=drives.drive_id
            JOIN companies ON drives.company_email=companies.email """
        )

        applications=cur.fetchall()



        cur.execute("SELECT drive_id, title, company_email, approval_status FROM drives")
        drives = cur.fetchall()

        cur.execute("SELECT COUNT(*) FROM students WHERE role='student'")
        total_students=cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM companies")
        total_companies=cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM drives")
        total_drives=cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM applications")
        total_applications=cur.fetchone()[0]



        conn.close()


        return render_template("admin_dashboard.html",students=students,
            companies=companies,total_students=total_students,total_companies=total_companies,
            total_drives=total_drives,total_applications=total_applications,search=search,drives=drives,applications=applications)
    


    elif role=="company":

        conn=sqlite3.connect("database.db")
        cur=conn.cursor()
        
        company_email=session['user']

        cur.execute(
            "SELECT name,email,approval_status FROM companies WHERE email=?",
            (company_email,)
        )
        company=cur.fetchone()

        cur.execute(
            """ SELECT drives.drive_id,drives.title,drives.drive_status,COUNT(applications.application_id)
            FROM drives
            LEFT JOIN applications ON drives.drive_id=applications.drive_id
            WHERE drives.company_email=?
            GROUP BY drives.drive_id """,
            (company_email,)
        )

        drives=cur.fetchall()

        conn.close()

        return render_template("company_dashboard.html",company=company,drives=drives)
    
    # return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.pop('user',None)
    session.pop('role',None)
    flash("Logged out successfully")
    return redirect(url_for("login"))

@app.route("/delete_student/<int:student_id>",methods=['POST'])
def delete_student(student_id):
    if 'user' not in session or session.get('role')!='admin':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()
    
    cur.execute("DELETE FROM applications WHERE student_email IN (SELECT email FROM students WHERE student_id=?)", 
        (student_id,))
    cur.execute("DELETE FROM students WHERE student_id=?",
        (student_id,)   )
    
    conn.commit()
    conn.close()

    flash("Student deleted")
    return redirect(url_for("dashboard"))

@app.route("/delete_company/<int:company_id>",methods=['POST'])
def delete_company(company_id):
    if 'user' not in session or session.get('role')!='admin':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        """ DELETE FROM applications
        WHERE drive_id IN(
        SELECT drive_id FROM drives WHERE company_email IN(
        SELECT email FROM companies WHERE company_id=?))""",
        (company_id,)
    )
    
    cur.execute(
        """ DELETE FROM drives 
        WHERE company_email IN(
        SELECT email FROM companies WHERE company_id=?)""",
        (company_id,)
    )
    
    cur.execute(
        "DELETE FROM companies WHERE company_id=?",
        (company_id,)
    )

    conn.commit()
    conn.close()

    flash("Company deleted")
    return redirect(url_for("dashboard"))



@app.route("/company_register",methods=['GET','POST'])
def company_register():
    if request.method=='POST':
        name=request.form.get("name")
        email=request.form.get("email")
        password=request.form.get("password")

        if not name or not email or not password:
            flash("All fields required")
            return redirect(url_for("company_register"))
        
        conn=sqlite3.connect("database.db")
        cur=conn.cursor()

        try:
            cur.execute(
                "INSERT INTO companies(name,email,password,approval_status) Values(?,?,?,?)",
                (name,email,password,"pending")
            )
            conn.commit()
            flash("Request sent for approval")

        except sqlite3.IntegrityError:
            flash("Company already exists")
        finally:
            conn.close()

        return redirect(url_for("company_login"))
    
    return render_template("company_register.html")



@app.route("/company_login",methods=['GET','POST'])
def company_login():
    if request.method=='POST':
        email=request.form.get("email")
        password=request.form.get("password")

        conn=sqlite3.connect("database.db")
        cur=conn.cursor()

        cur.execute(
            "SELECT * FROM companies WHERE email=? AND password=?",
            (email,password)
        )

        company=cur.fetchone()
        conn.close()

        if company:
            status=company[4]

            if status=="approved":
                session['user']=email
                session['role']="company"
                flash("Login successful")
                return redirect(url_for("dashboard"))
            
            elif status=="pending":
                flash("Waiting for admin approval")

            elif status=="blacklisted":
                flash("You are blacklisted")

            else:
                flash("Rejected by admin")
            return redirect(url_for("company_login"))
        
        flash("Invalid credentials")
        return redirect(url_for("company_login"))
    
    return render_template("company_login.html")


@app.route("/approve_company/<int:company_id>",methods=['POST'])
def approve_company(company_id):
    if 'user' not in session or session.get('role')!='admin':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "UPDATE companies SET approval_status='approved' WHERE company_id=?",
        (company_id,)
    )

    conn.commit()
    conn.close()
    
    flash("company approved")
    return redirect(url_for("dashboard"))



@app.route("/reject_company/<int:company_id>",methods=['POST'])
def reject_company(company_id):
    if 'user' not in session or session.get('role')!='admin':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "UPDATE companies SET approval_status='rejected' WHERE company_id=?",
        (company_id,)
    )
    conn.commit()
    conn.close()
    
    flash("Company rejected")
    return redirect(url_for("dashboard"))
 

@app.route("/create_drive",methods=['POST','GET'])
def create_drive():
    if 'user' not in session or session.get('role')!='company':
        return redirect(url_for("login"))
    
    if request.method=='POST':
        title=request.form.get("title")
        description=request.form.get("description")
        company_email=session['user']
        skills=request.form.get("skills")
        experience=request.form.get("experience")
        salary=request.form.get("salary")


        if not title or not description or not skills or not experience or not salary:
            flash("fill all fields")
            return redirect(url_for("create_drive"))
        
        conn=sqlite3.connect("database.db")
        cur=conn.cursor()

        cur.execute(
            "SELECT approval_status FROM companies WHERE email=?",(session['user'],)
        )
        
        result=cur.fetchone()
        if not result:
            conn.close()
            flash("Company not found")
            return redirect(url_for("dashboard"))
        
        status=result[0]

        if status!="approved":
            conn.close()
            flash("You are not approved")
            return redirect(url_for("dashboard"))

        cur.execute( 
            "INSERT INTO drives(company_email,title,description,skills,experience,salary) VALUES(?,?,?,?,?,?)",
            (company_email,title,description,skills,experience,salary)
        )

        conn.commit()
        conn.close()

        flash("Drive created successfully")
        return redirect(url_for("dashboard"))
    
    return render_template("create_drive.html")


@app.route("/view_drives")
def view_drives():
    if 'user' not in session or session.get('role')!='student':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute("""
    SELECT drives.drive_id,companies.name,drives.title,drives.description
    FROM drives
    JOIN companies ON drives.company_email=companies.email
    WHERE drives.approval_status='approved' AND drives.drive_status='ACTIVE'
    """)

    drives=cur.fetchall()

    conn.close()

    return render_template("view_drives.html",drives=drives)

@app.route("/approve_drive/<int:drive_id>",methods=['POST'])
def approve_drive(drive_id):
    if 'user' not in session or session.get('role')!='admin':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "UPDATE drives SET approval_status='approved' WHERE drive_id=?",
        (drive_id,)
    )

    conn.commit()
    conn.close()

    flash("Drive approved")
    return redirect(url_for("dashboard"))

@app.route("/reject_drive/<int:drive_id>",methods=['POST'])
def reject_drive(drive_id):
    if 'user' not in session or session.get('role')!='admin':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "UPDATE drives SET approval_status='rejected' WHERE drive_id=?",
        (drive_id,)
    )

    conn.commit()
    conn.close()

    flash("Drive rejected")
    return redirect(url_for("dashboard"))

@app.route("/apply/<int:drive_id>",methods=['POST'])
def apply(drive_id):
    if 'user' not in session or session.get('role')!='student':
        return redirect(url_for("login"))
    
    student_email=session['user']
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "SELECT * FROM applications WHERE student_email=? and drive_id=?",
        (student_email,drive_id)
    )

    already=cur.fetchone()

    if already:
        conn.close()
        flash("Already applied")
        return redirect(url_for("view_drives"))
    
    cur.execute(
        "INSERT INTO applications(student_email,drive_id) VALUES(?,?)",
        (student_email,drive_id)
    )

    conn.commit()
    conn.close()

    flash("Applied successfully")
    return redirect(url_for("view_drives"))


@app.route("/view_applicants")
def view_applicants():
    if 'user' not in session or session.get('role')!='company':
        return redirect(url_for("login"))
    
    company_email=session['user']

    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute("""
        SELECT applications.application_id,students.name,students.email,drives.title,applications.status
        FROM applications
        JOIN students ON applications.student_email=students.email
        JOIN drives ON applications.drive_id=drives.drive_id
        WHERE drives.company_email=?""",
        (company_email,)
    )

    applicants=cur.fetchall()
    conn.close()

    return render_template("view_applicants.html",applicants=applicants)

@app.route("/shortlist/<int:application_id>",methods=['POST'])
def shortlist(application_id):
    if 'user' not in session or session.get('role')!='company':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "UPDATE applications SET status='shortlisted' WHERE application_id=?",
        (application_id,)
    )

    conn.commit()
    conn.close()

    flash("Student Shortlisted")
    return redirect(url_for("view_applicants"))

@app.route("/reject_application/<int:application_id>",methods=['POST'])
def reject_application(application_id):
    if 'user' not in session or session.get('role')!='company':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "UPDATE applications SET status='rejected' WHERE application_id=?",
        (application_id,)
    )
    
    conn.commit()
    conn.close()
    
    flash("Student rejected")
    return redirect(url_for("view_applicants"))


@app.route("/update_status/<int:application_id>/<status>",methods=['POST'])
def update_status(application_id,status):
    if 'user' not in session or session.get('role')!='company':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "UPDATE applications SET status=? WHERE application_id=?",
        (status,application_id)
    )
    
    conn.commit()
    conn.close()

    return redirect(url_for("view_applicants"))


@app.route("/my_applications")
def my_applications():

    if 'user' not in session or session.get('role')!='student':
        return redirect(url_for("login"))
    
    student_email=session['user']

    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute("""
        SELECT companies.name,drives.title,applications.status
        FROM applications
        JOIN drives ON applications.drive_id=drives.drive_id
        JOIN companies ON drives.company_email=companies.email
        WHERE applications.student_email=?
    """,(student_email,))

    data=cur.fetchall()
    conn.close()

    return render_template("my_applications.html",applications=data)


@app.route("/blacklist_company/<int:company_id>",methods=['POST'])
def blacklist_company(company_id):
    if 'user' not in session or session.get('role')!='admin':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "UPDATE companies SET approval_status='blacklisted' WHERE company_id=?",
        (company_id,)
    )

    conn.commit()
    conn.close()

    flash("company blacklisted")
    return redirect(url_for("dashboard"))

@app.route("/unblacklist_company/<int:company_id>",methods=["POST"])
def unblacklist_company(company_id):
    if 'user' not in session or session.get('role')!='admin':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "UPDATE companies SET approval_status='approved' WHERE company_id=?",
        (company_id,)
    )
    
    conn.commit()
    conn.close()
    
    flash("company unblacklisted")
    return redirect(url_for("dashboard"))

     
@app.route("/blacklist_student/<int:student_id>",methods=["POST"])
def blacklist_student(student_id):
    if 'user' not in session or session.get('role')!='admin':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "UPDATE students SET status='blacklisted' WHERE student_id=?",
        (student_id,)
    )

    conn.commit()
    conn.close()

    flash("student blacklisted")
    return redirect(url_for("dashboard"))
    

@app.route("/unblacklist_student/<int:student_id>",methods=["POST"])
def unblacklist_student(student_id):
    if 'user' not in session or session.get('role')!='admin':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "UPDATE students SET status='active' WHERE student_id=?",
        (student_id,)
    )

    conn.commit()
    conn.close()
    
    flash("student unblacklisted")
    return redirect(url_for("dashboard"))


@app.route("/view_student/<int:student_id>")
def view_student(student_id):
    if 'user' not in session or session.get('role')!='admin':
        return redirect(url_for("login"))

    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "SELECT * FROM students WHERE student_id=?",(student_id,)
    ) 

    student=cur.fetchone()
    conn.close()

    if not student:
        flash("Student not found")
        return redirect(url_for('dashboard'))
    return render_template("student_detail.html",student=student)


@app.route("/view_company/<int:company_id>")
def view_company(company_id):
    if 'user' not in session or session.get('role')!='admin':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "SELECT * FROM companies WHERE company_id=?",(company_id,)
    )
    company=cur.fetchone()
    conn.close()

    if not company:
        flash("Company not found")
        return redirect(url_for("dashboard"))
    return render_template("company_detail.html",company=company)

@app.route("/select_application/<int:application_id>",methods=["POST"])
def selection_application(application_id):
    if 'user' not in session or session.get('role')!='company':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "UPDATE applications SET status='selected' WHERE application_id=?",
        (application_id,) 
    )

    conn.commit()
    conn.close()

    flash("student selected")
    return redirect(url_for("view_applicants"))

@app.route("/delete_drive/<int:drive_id>",methods=['POST'])
def delete_drive(drive_id):
    if 'user' not in session or session.get('role')!='company':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "DELETE FROM applications WHERE drive_id=?",
        (drive_id,)
    )

    cur.execute(
        "DELETE FROM drives WHERE drive_id=?",
        (drive_id,)
    )

    conn.commit()
    conn.close()

    flash("Drive Deleted")
    return redirect(url_for("dashboard"))

@app.route("/close_drive/<int:drive_id>",methods=['POST'])
def close_drive(drive_id):
    if 'user' not in session or session.get('role')!='company':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute(
        "UPDATE drives SET drive_status='CLOSED' WHERE drive_id=?",
        (drive_id,)
    )

    conn.commit()
    conn.close()

    flash("Drive Closed")
    return redirect(url_for("dashboard"))


@app.route("/edit_drive/<int:drive_id>",methods=["GET","POST"])
def edit_drive(drive_id):
    if 'user' not in session or session.get('role')!='company':
        return redirect(url_for("login"))
    
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    if request.method=="POST":
        title=request.form.get("title")
        description=request.form.get("description")
        skills=request.form.get("skills")
        experience=request.form.get("experience")
        salary=request.form.get("salary")

        cur.execute(
            """UPDATE drives SET title=?,description=?,skills=?,experience=?,salary=?
            WHERE drive_id=?""",
            (title,description,skills,experience,salary,drive_id)
        )

        conn.commit()
        conn.close()

        flash("Drive updated successfully ")
        return redirect(url_for("dashboard"))
    
    cur.execute(
        "SELECT * FROM drives WHERE drive_id=?",
        (drive_id,)
    )
    drive=cur.fetchone()

    

    if not drive:
        conn.close()
        flash("Drive not found")
        return redirect(url_for("dashboard"))
    
    conn.close()

    return render_template("edit_drive.html",drive=drive)






def init_db():
    conn=sqlite3.connect("database.db")
    cur=conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students(
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE NOT NULL,
        password TEXT,
        role TEXT,
        skills TEXT,
        education TEXT,
        resume TEXT,
        status TEXT DEFAULT 'active'     )
    """)

    cur.execute(""" 
        INSERT OR IGNORE INTO students(name,email,password,role)
        VALUES('admin','admin@gmail.com','admin123','admin')""")
    

    cur.execute(""" 
        CREATE TABLE IF NOT EXISTS companies(
            company_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE NOT NULL,
            password TEXT,
            approval_status TEXT DEFAULT 'pending'  )""")

    cur.execute(""" 
        CREATE TABLE IF NOT EXISTS drives(
            drive_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_email TEXT  NOT NULL,
            title TEXT,
            description TEXT,
            skills TEXT,
            experience TEXT,
            salary TEXT,
            drive_status TEXT DEFAULT 'ACTIVE',
            approval_status TEXT DEFAULT 'pending')""")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications(
            application_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT NOT NULL,
            drive_id INTEGER,
            status TEXT DEFAULT 'applied',
            UNIQUE(student_email,drive_id) )""")


    conn.commit()
    conn.close()

init_db()

if __name__ == "__main__":
    app.run(debug=True)

