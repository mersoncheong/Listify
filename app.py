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
    user = session["user"]
    algo = 0
    if "search" in session:
        algo = 1
        keyword = session["search"]
        statement = get_search(keyword)
        length = db.execute(statement).fetchone()[0]
        session.pop("search", None)
        result = db.execute(statement)
    elif "filter_date" in session:
        algo = 2
        date = session['filter_date']
        statement = filter_date(date)
        length_statement = filter_date_length(date)
        length = db.execute(length_statement).fetchone()[0]
        session.pop("filter_date", None)
        result = db.execute(statement)
    else:
        algo = 3
        first_statement = recommendation(user)
        second_statement = cat_recommendation(user)
        first = db.execute(first_statement)
        second = db.execute(second_statement)

    products = {}
    if algo == 1 or algo == 2:
        rows = result.fetchall()
        c = 0
        for row in rows:
            my_dict = {}
            for i in range(9):
                my_dict[i] = row[i]
            products[c] = my_dict
            c += 1
    else:
        first_row = first.fetchall()
        second_row = second.fetchall()
        c = 0
        for row in first_row:
            my_dict = {}
            for i in range(9):
                my_dict[i] = row[i]
            products[c] = my_dict
            c += 1
        for row in second_row:
            my_dict = {}
            for i in range(9):
                my_dict[i] = row[i]
            products[c] = my_dict
            c += 1
        if c == 0:
            statement = start_page()
            result = db.execute(statement)
            rows = result.fetchall()
            c = 0
            for row in rows:
                my_dict = {}
                for i in range(9):
                    my_dict[i] = row[i]
                products[c] = my_dict
                c += 1
    return render_template("home.html", user=user, length=c, products=products)


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
            "username": request.form.get("username"),
            "email": request.form.get("email"),
            "password": request.form.get("password")
        }
        statement = register_statement(data)
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
    email = insertion["email"]
    statement = f"SELECT password FROM users WHERE email = '{email}'"
    return sqlalchemy.text(statement)


def register_statement(insertion):
    username = insertion["username"]
    email = insertion["email"]
    password = insertion["password"]
    statement = f"""
    INSERT INTO users VALUES ( '{email}', '{username}', '{password}', CURRENT_DATE)
    """
    return sqlalchemy.text(statement)


def start_page():
    statement = f"SELECT * FROM listings ORDER BY (date_posted) LIMIT(100)"
    return sqlalchemy.text(statement)


def get_username(insertion):
    statement = f"SELECT username FROM users WHERE email = '{insertion}'"
    return sqlalchemy.text(statement)


def get_search(insertion):
    statement = f"SELECT * FROM listings WHERE name LIKE '%{insertion}%' ORDER BY date_posted DESC"
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
    db.commit()
    return redirect(url_for("mylisting"))


@app.post("/gohome")
def gohome():
    return redirect(url_for("marketplace"))


def recommendation(user):
    statement = f"""
    SELECT * FROM listings l1 
    WHERE l1.brand_name IN (
        SELECT l.brand_name
        FROM transactions t, listings l 
        WHERE l.listingid = t.listing
        AND t.buyer = '{user}' )
    ORDER BY l1.date_posted DESC
    LIMIT(30)
    """
    return sqlalchemy.text(statement)


def cat_recommendation(user):
    statement = f"""
    SELECT * 
    FROM listings l1 
    WHERE l1.main_category IN (
    SELECT l.main_category 
        FROM transactions t, listings l 
        WHERE l.listingid = t.listing
        AND t.buyer = '{user}'
        )
    ORDER BY l1.date_posted DESC
    LIMIT(30)
    """
    return sqlalchemy.text(statement)


@app.post("/buyform")
def buy_listing():
    try:
        data = request.form.get("item")
        db.execute(buy_statement(data))
        db.commit()
        return redirect(url_for("marketplace"))
    except Exception as e:
        return redirect(url_for("marketplace"))


def buy_statement(id):
    statement = f"""
    UPDATE listings
    SET purchased = true
    WHERE listingid = '{id}'
    """
    return sqlalchemy.text(statement)



@app.post("/stats")
def stats_page():
    return render_template("stats.html")



def most_popular_sellers():
    statement = f"""
    SELECT 
    FROM transactions t
    WHERE
    """












PORT = 2222

if __name__ == "__main__":
    # app.run("0.0.0.0", PORT)
    app.run(debug=True)
