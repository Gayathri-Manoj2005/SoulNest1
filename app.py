from flask import Flask, render_template, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = "soulnest_secret"

# HOME
@app.route("/")
def home():
    return render_template("home.html")

# LOGIN (single clean version)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # process login form here
        return redirect(url_for("home"))
    return render_template("login.html")

# SIGNUP (single clean version)
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # process signup form here
        return redirect(url_for("login"))
    return render_template("signup.html")

# ABOUT
@app.route('/account')
def account():
    return render_template('account.html')


@app.route('/about')
def about():
    return render_template('about.html')

# CONTACT
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")

        flash(f"Thank you, {name}! Our team will get in touch with you soon.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True)

@app.route('/adopt')
def adopt():
    return render_template('adopt.html')

@app.route('/boarding')
def shelters():
    return render_template('boarding.html')

@app.route('/foods')
def foods():
    return render_template('foods.html')

@app.route('/mates')
def mates():
    return render_template('mates.html')

