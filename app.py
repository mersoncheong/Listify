from flask_cors import CORS, cross_origin
import json
from flask import Flask, redirect, url_for, render_template, request, Response, flash, session
import sqlalchemy
import psycopg2
from datetime import datetime

app = Flask(__name__, template_folder='view',
            static_folder='view/static')
app.config['SECRET_KEY'] = "secret"

CORS(app)


YOUR_POSTGRES_PASSWORD = "postgres"
connection_string = f"postgresql://postgres:{YOUR_POSTGRES_PASSWORD}@localhost/postgres"
engine = sqlalchemy.create_engine(connection_string)


db = engine.connect()


@app.route("/", methods=['GET', 'POST'])
def home():
    if "user" in session:
        session.clear()
    return render_template("index.html")


@app.route("/listing")
def listings():
    return marketplace()


@app.route("/marketplace")
def marketplace():
    if "search" in session:
        keyword = session["search"]
        statement = get_search(keyword)
        second = get_length(keyword)
        length = db.execute(second).fetchone()[0]
        session.pop("search", None)
    elif "filter_date" in session:
        date = session['filter_date']
        statement = filter_date(date)
        length_statement = filter_date_length(date)
        length = db.execute(length_statement).fetchone()[0]
        session.pop("filter_date", None)
    else:
        statement = start_page()
        length = 100

    if "user" in session:
        user = session["user"]

    result = db.execute(statement)
    products = {}
    rows = result.fetchall()
    c = 0
    for row in rows:
        my_dict = {}
        for i in range(9):
            my_dict[i] = row[i]
        products[c] = my_dict
        c += 1
    return render_template("home.html", user=user, length=length, products=products)


@app.route("/user")
def user():
    if "user" in session:
        user = session["user"]
        return render_template("home.html", user=user)
    else:
        flash("Please Login")
        return redirect(url_for("home"))


@app.post("/login")
def login_into_account():
    try:
        data = {
            "name": "registered",
            "email": request.form.get("email"),
            "password": request.form.get("password")
        }

        statement = check_login_state(data)
        result = db.execute(statement)
        # try:
        row = result.fetchone()
        value = row[0]
        # except:
        #     flash("Account does not exists")
        #     return redirect(url_for(home))
        if value != data["password"]:
            flash("Wrong Password")
            return redirect(url_for("home"))
        else:
            name = get_username(data["email"])
            findName = db.execute(name)
            name = findName.fetchone()[0]
            session["user"] = name
            return redirect(url_for("marketplace"))
    except Exception as e:
        db.rollback()
        flash("User does not exists! Please Try Again")
        return redirect(url_for("home"))


@app.post("/register")
# ? a flask decorator listening for POST requests at the url /table-insert and handles the entry insertion into the given table/relation
# * You might wonder why PUT or a similar request header was not used here. Fundamentally, they act as POST. So the code was kept simple here
def insert_into_table():
    try:
        data = {
            "name": "registered",
            "body": {
                "username": request.form.get("username"),
                "email": request.form.get("email"),
                "password": request.form.get("password")
            }
        }
        # insertion = json.loads(data)
        statement = generate_insert_table_statement(data)
        db.execute(statement)
        db.commit()
        flash("Account Creation Sucessful")
        return redirect(url_for("home"))
    except Exception as e:
        db.rollback()
        flash("Username/Email has been taken. Please try again.")
        return redirect(url_for("home"))
        # return Response(str(e), 403)


@app.post("/search")
def search():
    try:
        data = request.form.get("search_query")
        session["search"] = data
        return redirect(url_for("marketplace"))
    except:
        flash("Search Error")
        return redirect(url_for("marketplace"))


@app.post("/filter")
def filter_days():
    data = request.form['dropdown']
    session['filter_date'] = data
    return redirect(url_for("marketplace"))


@app.post("/logout")
def logout():
    return redirect(url_for("home"))


def check_login_state(insertion):
    table_name = "registered"
    email = insertion["email"]
    password = insertion["password"]
    statement = f"SELECT password FROM {table_name} WHERE email = '{email}'"
    return sqlalchemy.text(statement)


def start_page():
    statement = f"SELECT * FROM listings LIMIT(100)"
    return sqlalchemy.text(statement)


def get_username(insertion):
    statement = f"SELECT username FROM registered WHERE email = '{insertion}'"
    return sqlalchemy.text(statement)


def get_search(insertion):
    statement = f"SELECT productname, price, date FROM products WHERE productname LIKE '%{insertion}%' ORDER BY popularity DESC"
    return sqlalchemy.text(statement)


def get_length(insertion):
    statement = f"SELECT COUNT(*) FROM listings WHERE name LIKE '%{insertion}%'"
    return sqlalchemy.text(statement)


def filter_date(value):
    x = float('inf')
    if value == "today":
        x = 0
    elif value == "past 3 days":
        x = 3
    elif value == "past 7 days":
        x = 7
    statement = f"SELECT * FROM listings WHERE ( date_posted  >= CURRENT_DATE - {x})"
    return sqlalchemy.text(statement)


def filter_date_length(value):
    x = float('inf')
    if value == "today":
        x = 0
    elif value == "past 3 days":
        x = 3
    elif value == "past 7 days":
        x = 7
    statement = f"SELECT COUNT(*) FROM listings WHERE ( date_posted  >= CURRENT_DATE - {x})"
    return sqlalchemy.text(statement)


def generate_insert_table_statement(insertion):
    table_name = insertion["name"]
    body = insertion["body"]
    statement = f"INSERT INTO {table_name}  "

    column_names = "("
    column_values = "("
    for key, value in body.items():
        column_names += (key+",")
        column_values += (f"'{value}',")

    column_names = column_names[:-1]+")"
    column_values = column_values[:-1]+")"
    statement = statement + column_names+" VALUES " + column_values+";"
    return sqlalchemy.text(statement)


@app.route("/mylisting", methods=['GET', 'POST'])
def mylisting():
    user = session["user"]
    statement = get_seller_listings(user)
    result = db.execute(statement)
    rows = result.fetchall()
    products = {}
    c = 0
    for row in rows:
        my_dict = {}
        for i in range(9):
            my_dict[i] = row[i]
        products[c] = my_dict
        c += 1
    length = c
    return render_template("selling.html", length=length, user=user, products=products)


def get_seller_listings(user):
    statement = f"SELECT * FROM listings WHERE seller = '{user}' ORDER BY (date_posted)"
    return sqlalchemy.text(statement)


@app.post("/sell")
def create_listing():
    item = request.form.get("item")
    price = request.form.get("price")
    brand = request.form.get("brand")
    condition = request.form.get("itemcon")
    category = request.form.get("itemcat")
    user = session["user"]
    date = datetime.today().strftime('%Y-%m-%d')
    get_listid = sqlalchemy.text(f"SELECT MAX(listingid) FROM listings")
    listing_id = db.execute(get_listid).fetchone()[0] + 1
    statement = f"INSERT INTO listings VALUES ('{listing_id}','{item}', '{condition}', '{brand}', '{price}', '{category}', '{date}', '{user}', false)"
    db.execute(sqlalchemy.text(statement))
    return redirect(url_for("mylisting"))


@app.post("/gohome")
def gohome():
    return redirect(url_for("marketplace"))


def recommendation(user):
    statement = F"SELECT "


PORT = 2222

if __name__ == "__main__":
    # app.run("0.0.0.0", PORT)
    app.run(debug=True)
