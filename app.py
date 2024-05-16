from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from bson.json_util import dumps
import os
import certifi
from datetime import datetime
from flask import jsonify
from functools import wraps


load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(16)
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
# mongo = PyMongo(app)
mongo = PyMongo(app, tlsCAFile=certifi.where())

# mongo = PyMongo(app, ssl_cert_reqs="CERT_REQUIRED")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "email" not in session:
            flash("Please log in to access this page.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/home")
@login_required
def home():
    # get all transcations that are created by session["email"]

    myTransactions = mongo.db.transactions.find({"createdby": session["email"]})
    myTransactions = list(myTransactions)

    # get all transcations that have email as session["email"]
    otherTransactions = mongo.db.transactions.find({"email": session["email"]})
    otherTransactions = list(otherTransactions)

    # in the list otherTransactions, change the createdby to email and I paid to They Owe and vice versa
    for transaction in otherTransactions:
        if transaction["sentBy"] == "I Paid":
            transaction["sentBy"] = "Person Paid"
        elif transaction["sentBy"] == "Person Paid":
            transaction["sentBy"] = "I Paid"

        transaction["email"] = transaction["createdby"]

    # combine both the lists
    allTransactions = myTransactions + otherTransactions

    # sort by date most recent first
    allTransactions = sorted(
        allTransactions,
        key=lambda x: datetime.strptime(x["transactiondate"], "%d %b %Y %H:%M:%S"),
        reverse=True,
    )

    return render_template("index.html", transactions=allTransactions)


@app.route("/", methods=["GET", "POST"])
def landing():
    return render_template("landing.html")
    

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return login_process()
    return render_template("login.html")

def login():
    if request.method == "POST":
        return login_process()
    return render_template("login.html")


def login_process():
    email = request.form["email"]
    password = request.form["password"]
    user = mongo.db.users.find_one({"email": email})
    if user and check_password_hash(user["password"], password):
        session["email"] = email
        session["name"] = user.get("name", "")
        return redirect(url_for("home"))
    else:
        flash("Invalid Email or Password")
        return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user_exists = mongo.db.users.find_one({"email": email})
        if user_exists:
            flash("Email Already Exists.")
            return redirect(url_for("signup"))
        hashed_password = generate_password_hash(password)
        mongo.db.users.insert_one(
            {
                "email": email,
                "password": hashed_password,
            }
        )
        flash("User Created Successfully. Please Login.")
        return redirect(url_for("login"))
    return render_template("signup_new.html")


@app.route("/logout")
def logout():
    session.pop("email", None)
    return redirect(url_for("home"))


@app.route("/addperson", methods=["GET", "POST"])
@login_required
def addperson():
    if request.method == "POST":
        print(session["email"])
        email = request.form["email"]
        amount = float(request.form["amount"])
        paid = request.form["paid"]
        description = request.form["description"]
        category = request.form["category"]

        if email == session["email"]:
            flash("Cant Add Yourself")
            return render_template("addPerson.html")

        # existing_person = mongo.db.people.find_one({"email": email})
        # if (existing_person):
        #     a = 5
        # else:
        #     flash('Email does not exist.')
        #     return render_template('addPerson.html')

        existing_person = mongo.db.people.find_one(
            {"email": email, "createdby": session["email"]}
        )
        if existing_person:
            flash("Email Already Exists.")
            return render_template("addPerson.html")
        else:
            proper_user = mongo.db.users.find_one({"email": email})
            if not proper_user:
                flash("Email does not exist.")
                return render_template("addPerson.html")

        whoPaid = ""
        if paid == "They Owe":
            whoPaid = "I Paid"
        elif paid == "I Owe":
            whoPaid = "Person Paid"

        person_data = {
            "email": email,
            "amount": amount,
            "paid": paid,
            "description": description,
            "category": category,
            "datecreated": datetime.now().strftime("%d %b %Y %H:%M:%S"),
            "createdby": session["email"],
            "transactiondate": datetime.now().strftime("%d %b %Y %H:%M:%S"),
            "sentBy": whoPaid,
        }

        if paid == "They Owe":
            otherPaid = "I Owe"
        elif paid == "I Owe":
            otherPaid = "They Owe"
        else:
            otherPaid = "Error"

        other_data = {
            "email": session["email"],
            "amount": amount,
            "paid": otherPaid,
            "description": description,
            "category": category,
            "datecreated": datetime.now().strftime("%d %b %Y %H:%M:%S"),
            "createdby": email,
        }
        mongo.db.people.insert_one(person_data)
        mongo.db.transactions.insert_one(person_data)
        mongo.db.people.insert_one(other_data)
        # return render_template('people.html')
        return redirect(url_for("people"))
    elif request.method == "GET":
        return render_template("addPerson.html")


@app.route("/contactus", methods=["GET", "POST"])
@login_required
def contactus():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        message = request.form["message"]
        admin = request.form["admin"]

        # Assuming you have a MongoDB collection called 'feedback'
        feedback_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "message": message,
            "admin": admin,
        }

        # Insert the feedback data into the 'feedback' collection
        mongo.db.feedback.insert_one(feedback_data)
        flash("Feedback Submitted Successfully.")
    return render_template("contact_us_new.html")


@app.route("/people", methods=["GET", "POST"])
@login_required
def people():
    if request.method == "GET":
        peopleData = mongo.db.people.find({"createdby": session["email"]})
        peopleData = list(peopleData)
        return render_template("people.html", people=peopleData)


@app.route("/stats", methods=["GET"])
@login_required
def stats():
    # Assuming 'mongo' is your PyMongo instance
    transactions = mongo.db.transactions.find({"createdby": session["email"]})

    # Data preparation
    inflow_data = []
    outflow_data = []
    expense_per_person = {}
    paid_unpaid = {"Paid": 0, "Unpaid": 0}

    # Iterate over the transactions to populate data structures
    for transaction in transactions:
        if transaction["sentBy"] == "I Paid":
            outflow_data.append(transaction["amount"])  # Outflow of cash
        else:
            inflow_data.append(transaction["amount"])  # Inflow of cash

        # Aggregate expenses per person
        person = transaction["email"]
        if person not in expense_per_person:
            expense_per_person[person] = 0
        expense_per_person[person] += transaction["amount"]

        # Count paid vs unpaid
        if transaction["paid"] == "They Owe":
            paid_unpaid["Paid"] += transaction["amount"]
        else:
            paid_unpaid["Unpaid"] += transaction["amount"]

    # Convert data for JSON parsing in JavaScript
    data = {
        "inflow_data": dumps(inflow_data),
        "outflow_data": dumps(outflow_data),
        "persons": dumps(list(expense_per_person.keys())),
        "amounts": dumps(list(expense_per_person.values())),
        "paid_unpaid": dumps(paid_unpaid),
    }

    return render_template("stats.html", **data)


@app.route("/update_expense", methods=["GET", "POST"])
@login_required
def update_expense():
    if request.method == "POST":
        email = request.form["email"]
        amount = float(request.form["amount"])
        paid = request.form["paid"]
        description = request.form["description"]
        category = request.form["category"]

        if email == session["email"]:
            flash("Cant Add Yourself")
            return render_template("addPerson.html")

        # Find the user based on the email
        existing_person = mongo.db.people.find_one({"email": email})
        if not existing_person:
            # If the user does not exist, redirect to the same page
            flash("User does not exist.")
            return redirect(url_for("update_expense"))

        existing_person = mongo.db.people.find_one(
            {"email": email, "createdby": session["email"]}
        )
        if not existing_person:
            # If the user does not exist for the specific session email, show an error
            flash(
                "You havent made a transaction with this user before. Add user first."
            )
            return redirect(url_for("update_expense"))

        # Check if they owe or you owe based on the existing data
        existing_paid = existing_person.get("paid", "")
        existing_amount = existing_person.get("amount", 0)

        tempAmount = amount
        whoPaid = ""
        if paid == "They Owe":
            whoPaid = "I Paid"
        elif paid == "I Owe":
            whoPaid = "Person Paid"

        if existing_paid == "They Owe" and paid == "They Owe":
            amount += existing_amount
        elif existing_paid == "I Owe" and paid == "They Owe":
            existing_amount -= amount
            if existing_amount < 0:
                existing_paid = "They Owe"
                existing_amount = existing_amount * (-1)
            amount = existing_amount
        elif existing_paid == "They Owe" and paid == "I Owe":
            existing_amount -= amount
            if existing_amount < 0:
                existing_paid = "I Owe"
                existing_amount = existing_amount * (-1)
            amount = existing_amount
        elif existing_paid == "I Owe" and paid == "I Owe":
            amount += existing_amount

        if existing_paid == "They Owe":
            other_paid = "I Owe"
        elif existing_paid == "I Owe":
            other_paid = "They Owe"
        else:
            other_paid = "Error"

        # Update the person's information
        mongo.db.people.update_one(
            {"email": email, "createdby": session["email"]},
            {
                "$set": {
                    "amount": amount,
                    "paid": existing_paid,
                    "description": description,
                    "category": category,
                }
            },
        )

        mongo.db.people.update_one(
            {"email": session["email"], "createdby": email},
            {
                "$set": {
                    "amount": amount,
                    "paid": other_paid,
                    "description": description,
                    "category": category,
                }
            },
        )

        transaction_data = {
            "email": email,
            "amount": tempAmount,
            "paid": paid,
            "description": description,
            "category": category,
            "datecreated": datetime.now().strftime("%d %b %Y %H:%M:%S"),
            "createdby": session["email"],
            "transactiondate": datetime.now().strftime("%d %b %Y %H:%M:%S"),
            "sentBy": whoPaid,
        }

        mongo.db.transactions.insert_one(transaction_data)

        flash("Expense updated successfully.")
        return redirect(url_for("people"))

    elif request.method == "GET":
        return render_template("update_expense.html")


if __name__ == "__main__":
    # app.secret_key = 'your_secret_key_here'
    app.run(debug=True)
