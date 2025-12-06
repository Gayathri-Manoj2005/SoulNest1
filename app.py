from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Import model functions
from models import (
    get_user_by_email,
    save_contact_message,
    get_users_connection,
    get_pets_connection,
    get_boarding_connection
)

app = Flask(__name__)
app.secret_key = "soulnest_secret"


# HOME
@app.route("/")
def home():
    return render_template("home.html")


# SIGNUP 
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Required fields
        if not username or not email or not password or not confirm_password:
            flash("All fields are required!", "danger")
            return redirect(url_for("signup"))

        # Password match
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("signup"))

        # Strong password
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#._-]).{8,}$"
        if not re.match(pattern, password):
            flash("Password must include uppercase, lowercase, number, special character and be 8+ characters.", "danger")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password)

        # Save user in DB
        try:
            conn = get_users_connection()
            cursor = conn.cursor()

            sql = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
            values = (username, email, hashed_password)
            cursor.execute(sql, values)
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
            return redirect(url_for("login"))

    return render_template("login.html")



# ABOUT
@app.route("/about")
def about():
    return render_template("about.html")



# CONTACT
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")

        save_contact_message(name, email, phone, message)

        flash(f"Thank you, {name}! Our team will get in touch with you soon.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")



# PETS GET
@app.route("/pets", methods=["GET"])
def get_pets():
    conn = get_pets_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM pets")
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("pets.html", pets=results)



# PETS POST
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


@app.route("/adopt")
def adopt():
    pet_type = request.args.get("type")  # dog / cat / small / None

    conn = get_pets_connection()
    cursor = conn.cursor(dictionary=True)

    if pet_type:
        cursor.execute("SELECT * FROM pets WHERE type = %s", (pet_type,))
    else:
        cursor.execute("SELECT * FROM pets")

    pets = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("adopt.html", pets=pets, selected_type=pet_type)



@app.route("/boarding")
def shelters():

    pet_type = request.args.get("type")
    state = request.args.get("state")
    city = request.args.get("city")

    conn = get_boarding_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM boarding WHERE 1=1"
    values = []

    if pet_type:
        query += " AND pet_type = %s"
        values.append(pet_type)

    if state:
        query += " AND state = %s"
        values.append(state)

    if city:
        query += " AND city = %s"
        values.append(city)

    cursor.execute(query, values)
    shelters = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("boarding.html", shelters=shelters)



@app.route("/foods")
def foods():
    return render_template("foods.html")



if __name__ == "__main__":
    app.run(debug=False)