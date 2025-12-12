from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import re
import os
from dotenv import load_dotenv
from flask_mail import Mail, Message

# load variables from .env into environment
load_dotenv()

# Import your DB helper functions
from models import (
    get_user_by_email,
    save_contact_message,
    get_users_connection,
    get_pets_connection,
    get_boarding_connection
)

app = Flask(__name__)
app.secret_key = "soulnest_secret"

# Mail configuration (reads credentials from .env)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

# ----------------------------------------------------------------------
# HOME
# ----------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("home.html")


# ----------------------------------------------------------------------
# SIGNUP
# ----------------------------------------------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not username or not email or not password or not confirm_password:
            flash("All fields are required!", "danger")
            return redirect(url_for("signup"))

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("signup"))

        # strong password rule
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#._-]).{8,}$"
        if not re.match(pattern, password):
            flash("Password must include uppercase, lowercase, number, special character and be 8+ characters.", "danger")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)

        try:
            conn = get_users_connection()
            cursor = conn.cursor()
            sql = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
            cursor.execute(sql, (username, email, hashed_password))
            conn.commit()
            cursor.close()
            conn.close()

            flash("Account created successfully! Please login.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            flash(f"Error: {e}", "danger")
            return redirect(url_for("signup"))

    return render_template("signup.html")


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = get_user_by_email(email)

        if user and check_password_hash(user["password"], password):
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Incorrect email or password!", "danger")
            return redirect(url_for("home"))

    return render_template("login.html")


# ----------------------------------------------------------------------
# ABOUT
# ----------------------------------------------------------------------
@app.route("/about")
def about():
    return render_template("about.html")


# ----------------------------------------------------------------------
# CONTACT
# ----------------------------------------------------------------------
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")

        # 1) Save message to DB
        try:
            save_contact_message(name, email, phone, message)
        except Exception:
            app.logger.exception("Failed to save contact message")
            flash("There was an error saving your message. Please try again.", "danger")
            return redirect(url_for("contact"))

        # 2) Prepare email notification to admin
        subject = "📩 New Contact Message - SoulNest"
        recipients = [os.getenv('MAIL_USERNAME')]  # admin receives notification

        # Include user info in the body
        body = f"""
New contact message received.

Name: {name}
Email: {email}
Phone: {phone}

Message:
{message}

-- SoulNest website
"""

        # 3) Send email with reply-to set to user
        try:
            msg = Message(
                subject=subject,
                sender=os.getenv('MAIL_USERNAME'),          # your Gmail account
                recipients=recipients,
                reply_to=f"{name} <{email}>",             # user name + email for replies
                body=body
            )
            mail.send(msg)
        except Exception:
            app.logger.exception("Failed to send contact notification email")
            flash("Your message was saved, but we couldn't send an email notification. We'll still contact you.", "warning")
            return redirect(url_for("contact"))

        # 4) Success
        flash(f"Thank you, {name}! Our team will get in touch with you soon.", "success")
        return redirect(url_for("contact"))

    # GET request
    return render_template("contact.html")

# ----------------------------------------------------------------------
# PETS (Admin listing)
# ----------------------------------------------------------------------
@app.route("/pets", methods=["GET"])
def get_pets():
    conn = get_pets_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM pets")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("pets.html", pets=results)


# ----------------------------------------------------------------------
# PETS (Add new pet)
# ----------------------------------------------------------------------
@app.route("/pets", methods=["POST"])
def add_pet():
    name = request.form.get("name")
    pet_type = request.form.get("type")
    age = request.form.get("age")

    if not name or not pet_type or not age:
        flash("All pet fields are required!", "danger")
        return redirect(url_for("get_pets"))

    conn = get_pets_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO pets (name, type, age) VALUES (%s, %s, %s)"
    cursor.execute(sql, (name, pet_type, age))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Pet added successfully!", "success")
    return redirect(url_for("get_pets"))


# ----------------------------------------------------------------------
# ADOPT — CATEGORY SELECTION
# ----------------------------------------------------------------------
@app.route("/adopt")
def adopt():
    # Support old URLs using ?type=dog
    pet_type = request.args.get("type")

    if pet_type:
        pet_type = pet_type.lower()
        if pet_type in ("dog", "cat", "small"):
            return redirect(url_for("adopt_by_type", pet_type=pet_type))

    return render_template("adopt.html")


# ----------------------------------------------------------------------
# ADOPT — RESULTS PAGE
# ----------------------------------------------------------------------
@app.route("/adopt/<pet_type>")
def adopt_by_type(pet_type):
    allowed = ("dog", "cat", "small")
    pet_type = pet_type.strip().lower()

    if pet_type not in allowed:
        return redirect(url_for("adopt"))

    pets = []
    conn = None

    try:
        conn = get_pets_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pets WHERE type = %s", (pet_type,))
        pets = cursor.fetchall()
        cursor.close()
    except Exception:
        app.logger.exception("Error fetching pets")
    finally:
        if conn:
            conn.close()

    return render_template("adopt_results.html", pets=pets, pet_type=pet_type)


@app.route("/boarding")
def shelters():
    # Option lists used by the template
    pet_type_options = ["", "dog", "cat", "small"]   # "" means Any
    state_options = [
        "", "Kerala", "Tamil Nadu", "Karnataka", "Andhra Pradesh", "Goa", "Maharashtra"
    ]
    city_options = [
        "", "Thiruvananthapuram", "Kochi", "Bangalore", "Hyderabad", "Goa", "Mumbai", "Chennai", "Visakhapatnam", "Pune", "Surat"
    ]

    # Read query arguments (defaults to empty string)
    pet_type = (request.args.get("type") or "").strip()
    state = (request.args.get("state") or "").strip()
    city = (request.args.get("city") or "").strip()

    # Build query using case-insensitive & trimmed comparisons
    query = "SELECT * FROM boarding WHERE 1=1"
    values = []

    if pet_type:
        query += " AND LOWER(TRIM(pet_type)) = %s"
        values.append(pet_type.lower())

    if state:
        query += " AND LOWER(TRIM(state)) = %s"
        values.append(state.lower())

    if city:
        query += " AND LOWER(TRIM(city)) = %s"
        values.append(city.lower())

    app.logger.debug("Boarding query: %s | values=%s", query, values)

    shelters = []
    conn = None
    try:
        conn = get_boarding_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, values)
        shelters = cursor.fetchall() or []
        cursor.close()
    except Exception:
        app.logger.exception("Error fetching boarding results")
        shelters = []
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

    # Build a public image URL (either absolute URL or static/<image path>)
    from flask import url_for
    for s in shelters:
        img = (s.get("image_url") or "").strip()
        if not img:
            s["image_src"] = url_for('static', filename='images/default_boarding.jpg')
        elif img.lower().startswith("http://") or img.lower().startswith("https://"):
            s["image_src"] = img
        else:
            s["image_src"] = url_for('static', filename=img.lstrip("/"))

    return render_template(
        "boarding.html",
        shelters=shelters,
        pet_type_options=pet_type_options,
        state_options=state_options,
        city_options=city_options,
        selected_pet_type=pet_type or "",
        selected_state=state or "",
        selected_city=city or ""
    )
# ----------------------------------------------------------------------
# FOODS
# ----------------------------------------------------------------------
@app.route("/foods")
def foods():
    return render_template("foods.html")


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=False)
