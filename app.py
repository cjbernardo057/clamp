from flask import Flask, render_template, send_from_directory, request, jsonify, session
from database import init_db, get_db


app = Flask(__name__)

# =========================
# SESSION SECRET KEY
# =========================

app.secret_key = "pc-management-secret-key"


init_db()

from datetime import datetime

def log_activity(username, action, computer_name="", comlab=""):
    connection = get_db()
    try:
        connection.execute("""
            INSERT INTO activity_logs (username, action, computer_name, comlab, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (username, action, computer_name, comlab, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        connection.commit()
    except Exception as e:
        print("Log Activity Error:", e)
    finally:
        connection.close()


# =========================
# PAGES
# =========================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create")
def create():
    return render_template("create.html")


@app.route("/forgot")
def forgot():
    return render_template("Forgot.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/report")
def report():
    return render_template("report.html")


@app.route("/images.png")
def images():
    return send_from_directory(".", "images.png")


# =========================
# CREATE ACCOUNT
# =========================

@app.route("/create-account", methods=["POST"])
def create_account():

    data = request.get_json()

    firstname = data.get("firstname")
    lastname = data.get("lastname")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not firstname or not lastname or not username or not email or not password:

        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        })

    connection = get_db()

    try:

        connection.execute("""
            INSERT INTO accounts
            (firstname, lastname, username, email, password)
            VALUES (?, ?, ?, ?, ?)
        """, (
            firstname,
            lastname,
            username,
            email,
            password
        ))

        connection.commit()

        return jsonify({
            "success": True
        })

    except Exception as e:

        if "UNIQUE constraint failed" in str(e):

            return jsonify({
                "success": False,
                "message": "Username or email already exists."
            })

        print("Database Error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to create account."
        })

    finally:

        connection.close()


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:

        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        })

    connection = get_db()

    try:

        account = connection.execute("""
            SELECT *
            FROM accounts
            WHERE username = ?
            AND password = ?
        """, (
            username,
            password
        )).fetchone()

        if account:

            # Save the logged-in username
            # inside the Flask session.
            session["username"] = username

            return jsonify({
                "success": True
            })

        else:

            return jsonify({
                "success": False,
                "message": "Invalid username or password."
            })

    except Exception as e:

        print("Login Error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to login."
        })

    finally:

        connection.close()


# =========================
# GET COMPUTERS
# =========================

@app.route("/api/computers", methods=["GET"])
def get_computers():

    connection = get_db()

    try:

        computers = connection.execute("""
            SELECT *
            FROM computers
            ORDER BY id ASC
        """).fetchall()

        return jsonify([
            dict(computer)
            for computer in computers
        ])

    except Exception as e:

        print("Computer Loading Error:", e)

        return jsonify([]), 500

    finally:

        connection.close()


# =========================
# ADD COMPUTER
# =========================

@app.route("/api/computers", methods=["POST"])
def add_computer():

    data = request.get_json()

    computer_name = data.get("computer_name")
    comlab = data.get("comlab")
    status = data.get("status")

    processor = data.get("processor")
    motherboard = data.get("motherboard")
    ram = data.get("ram")

    # Dashboard currently sends ram_slots.
    # This keeps that naming compatible.
    ram_slots = data.get("ram_slots", 1)

    storage = data.get("storage")
    gpu = data.get("gpu")
    psu = data.get("psu")
    cooling = data.get("cooling")
    computer_case = data.get("computer_case")
    monitor = data.get("monitor")
    keyboard = data.get("keyboard")
    mouse = data.get("mouse")

    if not computer_name or not comlab or not status:

        return jsonify({
            "success": False,
            "message": "Computer name, computer lab, and status are required."
        })

    connection = get_db()

    try:

                # Check if a computer with the same name already exists in that room
        existing = connection.execute("""
            SELECT id
            FROM computers
            WHERE computer_name = ?
            AND comlab = ?
        """, (
            computer_name,
            comlab
        )).fetchone()

        if existing:

            return jsonify({
                "success": False,
                "message": f"{computer_name} already exists in {comlab}."
            })


        connection.execute("""
            INSERT INTO computers (
                computer_name,
                comlab,
                status,
                processor,
                motherboard,
                ram,
                ram_slots,
                storage,
                gpu,
                psu,
                cooling,
                computer_case,
                monitor,
                keyboard,
                mouse
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            computer_name,
            comlab,
            status,
            processor,
            motherboard,
            ram,
            ram_slots,
            storage,
            gpu,
            psu,
            cooling,
            computer_case,
            monitor,
            keyboard,
            mouse
        ))

        connection.commit()

        log_activity(session.get("username", "Unknown"), "Added Computer", computer_name, comlab)
        return jsonify({
            "success": True,
            "message": "Computer successfully added."
        })

    except Exception as e:

        connection.rollback()

        print("Add Computer Error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to add computer."
        })

    finally:

        connection.close()


# =========================
# GET ISSUE REPORTS
# =========================

@app.route("/api/issue-reports", methods=["GET"])
def get_issue_reports():

    connection = get_db()

    try:

        reports = connection.execute("""
            SELECT *
            FROM issue_reports
            WHERE status != 'Resolved'
            ORDER BY id DESC
        """).fetchall()

        return jsonify([
            dict(report)
            for report in reports
        ])

    except Exception as e:

        print("Issue Report Error:", e)

        return jsonify([]), 500

    finally:

        connection.close()


# =========================
# SUBMIT ISSUE REPORT
# =========================

@app.route("/api/report-issue", methods=["POST"])
def report_issue():

    data = request.get_json()

    reported_by = data.get("reported_by")
    comlab = data.get("comlab")
    computer_name = data.get("computer_name")
    description = data.get("description")

    # Check if fields are complete.

    if not reported_by or not comlab or not computer_name or not description:

        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        })

    connection = get_db()

    try:

        # Check whether the selected computer
        # belongs to the selected computer lab.

        computer = connection.execute("""
            SELECT *
            FROM computers
            WHERE computer_name = ?
            AND comlab = ?
        """, (
            computer_name,
            comlab
        )).fetchone()

        if not computer:

            return jsonify({
                "success": False,
                "message": "Computer not found in the selected room."
            })

        # Add the issue report.
        from datetime import datetime

        connection.execute("""
            INSERT INTO issue_reports (
                reported_by,
                comlab,
                computer_name,
                description,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, 'Pending', ?)
        """, (
            reported_by,
            comlab,
            computer_name,
            description,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        # Change the computer status.

        connection.execute("""
            UPDATE computers
            SET status = 'Under Maintenance'
            WHERE computer_name = ?
            AND comlab = ?
        """, (
            computer_name,
            comlab
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Issue successfully reported."
        })

    except Exception as e:

        connection.rollback()

        print("Report Error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to submit report."
        })

    finally:

        connection.close()



# =========================
# RESOLVE ISSUE
# =========================

@app.route("/api/issue-reports/<int:report_id>/resolve", methods=["POST"])
def resolve_issue(report_id):

    from datetime import datetime

    data = request.get_json() or {}

    action_taken = data.get("action_taken", "").strip()
    status_changed_to = data.get("status_changed_to", "").strip()

    resolved_by = session.get("username", "Unknown")

    if not action_taken:
        return jsonify({
            "success": False,
            "message": "Action taken is required."
        })

    allowed_statuses = ["Available", "Under Maintenance", "Out of Service"]

    if status_changed_to and status_changed_to not in allowed_statuses:
        return jsonify({
            "success": False,
            "message": "Invalid status."
        })

    connection = get_db()

    try:

        report = connection.execute("""
            SELECT *
            FROM issue_reports
            WHERE id = ?
        """, (report_id,)).fetchone()

        if not report:
            return jsonify({
                "success": False,
                "message": "Report not found."
            })

        connection.execute("""
            INSERT INTO issue_resolutions (
                report_id,
                action_taken,
                status_changed_to,
                resolved_by,
                resolved_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            report_id,
            action_taken,
            status_changed_to,
            resolved_by,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        connection.execute("""
            UPDATE issue_reports
            SET status = 'Resolved'
            WHERE id = ?
        """, (report_id,))

        if status_changed_to:
            connection.execute("""
                UPDATE computers
                SET status = ?
                WHERE computer_name = ?
                AND comlab = ?
            """, (
                status_changed_to,
                report["computer_name"],
                report["comlab"]
            ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Issue resolved."
        })

    except Exception as e:

        connection.rollback()
        print("Resolve Issue Error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to resolve the issue."
        })

    finally:
        connection.close()


# =========================
# GET RESOLUTION LOGS
# =========================

@app.route("/api/resolution-logs", methods=["GET"])
def get_resolution_logs():

    connection = get_db()

    try:

        logs = connection.execute("""
            SELECT
                rs.id,
                rs.report_id,
                rs.action_taken,
                rs.status_changed_to,
                rs.resolved_by,
                rs.resolved_at,
                ir.computer_name,
                ir.comlab,
                ir.reported_by,
                ir.description
            FROM issue_resolutions rs
            LEFT JOIN issue_reports ir
                ON ir.id = rs.report_id
            ORDER BY rs.id DESC
        """).fetchall()

        return jsonify([
            dict(log)
            for log in logs
        ])

    except Exception as e:

        print("Resolution Logs Error:", e)

        return jsonify([]), 500

    finally:

        connection.close()

# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return jsonify({
        "success": True
    })

# =========================
# GET USERS
# =========================

@app.route("/api/users", methods=["GET"])
def get_users():

    connection = get_db()

    try:

        users = connection.execute("""
            SELECT id, username, email
            FROM accounts
            WHERE username != 'DEVacc'
            ORDER BY id ASC
        """).fetchall()

        return jsonify([dict(u) for u in users])

    except Exception as e:

        print("Get Users Error:", e)
        return jsonify([]), 500

    finally:
        connection.close()


# =========================
# RESET USER PASSWORD
# =========================

@app.route("/api/users/<int:user_id>/reset-password", methods=["POST"])
def reset_user_password(user_id):

    data = request.get_json() or {}
    new_password = data.get("password", "").strip()

    if not new_password:
        return jsonify({
            "success": False,
            "message": "Password is required."
        })
      
    # Block password reset for the super admin
    connection = get_db()
    user = connection.execute("SELECT username FROM accounts WHERE id = ?", (user_id,)).fetchone()
    
    if user and user["username"] == "DEVacc":
        connection.close()
        return jsonify({
            "success": False,
            "message": "This account's password cannot be reset."
        })

    try:

        connection.execute("""
            UPDATE accounts
            SET password = ?
            WHERE id = ?
        """, (new_password, user_id))

        connection.commit()

        return jsonify({"success": True})

    except Exception as e:

        connection.rollback()
        print("Reset Password Error:", e)
        return jsonify({
            "success": False,
            "message": "Unable to reset password."
        })

    finally:
        connection.close()


# =========================
# DELETE USER
# =========================

@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):

    connection = get_db()

    try:

        # Don't let the admin delete their own account
        current_user = session.get("username")

        # Block deletion of the super admin
        user_to_delete = connection.execute("""
            SELECT username FROM accounts WHERE id = ?
        """, (user_id,)).fetchone()

        if user_to_delete and user_to_delete["username"] == "DEVacc":
            return jsonify({
                "success": False,
                "message": "This account is protected and cannot be deleted."
            })

        user = connection.execute("""
            SELECT username
            FROM accounts
            WHERE id = ?
        """, (user_id,)).fetchone()

        if user and user["username"] == current_user:
            return jsonify({
                "success": False,
                "message": "You cannot delete your own account."
            })

        connection.execute("""
            DELETE FROM accounts
            WHERE id = ?
        """, (user_id,))

        connection.commit()

        return jsonify({"success": True})

    except Exception as e:

        connection.rollback()
        print("Delete User Error:", e)
        return jsonify({
            "success": False,
            "message": "Unable to delete user."
        })

    finally:
        connection.close()

# =========================
# UPDATE COMPUTER
# =========================

@app.route("/api/computers/<int:computer_id>", methods=["PUT"])
def update_computer(computer_id):

    data = request.get_json()
    connection = get_db()

    try:
        connection.execute("""
            UPDATE computers SET
                computer_name = ?, comlab = ?, status = ?,
                processor = ?, motherboard = ?, ram = ?, ram_slots = ?,
                storage = ?, gpu = ?, psu = ?, cooling = ?,
                computer_case = ?, monitor = ?, keyboard = ?, mouse = ?
            WHERE id = ?
        """, (
            data.get("computer_name"), data.get("comlab"), data.get("status"),
            data.get("processor"), data.get("motherboard"), data.get("ram"), data.get("ram_slots"),
            data.get("storage"), data.get("gpu"), data.get("psu"), data.get("cooling"),
            data.get("computer_case"), data.get("monitor"), data.get("keyboard"), data.get("mouse"),
            computer_id
        ))

        connection.commit()
        log_activity(session.get("username", "Unknown"), "Edited Computer", data.get("computer_name"), data.get("comlab"))
        return jsonify({"success": True, "message": "Computer updated."})

    except Exception as e:
        connection.rollback()
        print("Update Computer Error:", e)
        return jsonify({"success": False, "message": "Unable to update computer."})
    finally:
        connection.close()


# =========================
# DELETE COMPUTER
# =========================

@app.route("/api/computers/<int:computer_id>", methods=["DELETE"])
def delete_computer(computer_id):

    connection = get_db()

    try:
        # 1. GET THE COMPUTER INFO FIRST (Before we delete it!)
        pc = connection.execute("""
            SELECT computer_name, comlab 
            FROM computers 
            WHERE id = ?
        """, (computer_id,)).fetchone()

        # 2. DELETE THE COMPUTER
        connection.execute("DELETE FROM computers WHERE id = ?", (computer_id,))
        connection.commit()

        # 3. SAVE THE LOG
        if pc:
            log_activity(
                session.get("username", "Unknown"), 
                "Deleted Computer", 
                pc["computer_name"], 
                pc["comlab"]
            )

        return jsonify({"success": True, "message": "Computer deleted."})

    except Exception as e:
        connection.rollback()
        print("Delete Computer Error:", e)
        return jsonify({"success": False, "message": "Unable to delete computer."})
    finally:
        connection.close()


# =========================
# ACTIVITY LOGS
# =========================

@app.route("/api/activity-logs", methods=["GET"])
def get_activity_logs():
    connection = get_db()
    try:
        logs = connection.execute("""
            SELECT * FROM activity_logs
            ORDER BY id DESC
        """).fetchall()
        return jsonify([dict(log) for log in logs])
    except Exception as e:
        print("Activity Logs Error:", e)
        return jsonify([]), 500
    finally:
        connection.close()
        
# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
    app.run(debug=True)