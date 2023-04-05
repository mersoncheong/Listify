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
    if "user" in session or "admin" in session:
        session.clear()
    return render_template("index.html")


@app.route("/listing")
def listings():
    return marketplace()


@app.route("/marketplace")
def marketplace():
    if "admin" in session:
        user = "admin"
        useremail = "admin"
        header_value = "Sellers' Statistics"
    else:
        user = session["user"]
        useremail = session["useremail"]
        header_value = "My Listings"
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
    return render_template("home.html", username=user, user=useremail, length=c, products=products,
                           header_value = header_value)


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
            admin_result = db.execute(admin_users(data['email']))
            admin_name = admin_result.fetchone()[0]
            admin_name = int(admin_name)
            if admin_name:
                session["admin"] = "admin"
                return redirect(url_for("adminpage"))
            name = get_username(data["email"])
            findName = db.execute(name)
            name = findName.fetchone()[0]
            session["user"] = name
            session["useremail"] = data["email"]
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
    statement = f"SELECT * FROM listings ORDER BY (date_posted) DESC LIMIT(100)"
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
    if "admin" in session:
        return redirect(url_for("adminpage"))
    user = session["user"]
    useremail = session['useremail']
    if "search" in session:
        data = session["search"]
        statement = searchsellingquery(useremail, data)
        session.pop('search', None)
    else:
        statement = get_seller_listings(useremail)
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
    user = session["useremail"]
    date = datetime.today().strftime('%Y-%m-%d')
    get_listid = sqlalchemy.text(f"SELECT MAX(listingid) FROM listings")
    listing_id = db.execute(get_listid).fetchone()[0] + 1
    statement = f"INSERT INTO listings VALUES ('{listing_id}','{item}', '{condition}', '{brand}', '{price}', '{category}', '{date}', '{user}', false)"
    try:
        db.execute(sqlalchemy.text(statement))
        db.commit()
        return redirect(url_for("mylisting"))
    except Exception as e:
        db.rollback()
        flash("Please ensure fields are entered correctly")
        return redirect(url_for("mylisting"))


@app.post("/gohome")
def gohome():
    return redirect(url_for("marketplace"))


@app.post("/searchselling")
def searchselling():
    data = request.form.get("search_selling")
    session["search"] = data
    return redirect(url_for("mylisting"))


def searchsellingquery(user, data):
    statement = f"""
    SELECT * FROM listings 
    WHERE seller = '{user}'
    AND name LIKE '%{data}%'
    ORDER BY (date_posted)
    """
    return sqlalchemy.text(statement)


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



def top_users():
    statement = f"""
    SELECT seller
    FROM transactions t
    GROUP BY seller
    ORDER BY COUNT(seller) DESC
    LIMIT 50;
    """
    return sqlalchemy.text(statement)


def admin_users(user):
    statement = f"""
    SELECT COUNT(*)
    FROM admins
    WHERE email = '{user}'
    """
    return sqlalchemy.text(statement)


@app.route("/admin", methods=['GET', 'POST'])
def adminpage():
    if "adminsearch" in session:
        adminsearch = session["adminsearch"]
        statement = adminsearchquery(adminsearch)
    else:
        statement = admin_home()
    results = db.execute(statement)
    rows = results.fetchall()
    c = 0
    products = {}
    for row in rows:
        my_dict = {}
        for i in range(7):
            my_dict[i] = row[i]
        products[c] = my_dict
        c += 1
    return render_template("admin.html", length=c, products=products, input="Sales", input_two="Earnings")


def admin_home():
    statement = f"""
    SELECT u.email, u.username, u.join_date, SUM(l.price) as total_sales, COUNT(*) as total_volumes,
    ROUND(SUM(l.price)/COUNT(*),2) as earnings_per_item, CURRENT_DATE - u.join_date as daysjoin
    FROM users u, transactions t, listings l
    WHERE u.email = t.seller
    AND t.listing = l.listingid
    GROUP BY u.email
    ORDER BY total_sales DESC
    LIMIT(50);
    """
    return sqlalchemy.text(statement)


@app.post("/delete_users")
def delete_users():
    email = request.form.get("deleteusers")
    statement = f"""
    DELETE FROM users 
    WHERE email = '{email}'
    """
    result = sqlalchemy.text(statement)
    try:
        db.execute(result)
        db.commit()
        return redirect(url_for("adminpage"))
    except Exception as e:
        db.rollback()
        flash("User not found")
        return redirect(url_for("adminpage"))


@app.post("/filter_admin")
def admin_filter():
    data = request.form.get("admindropdown")
    filter_dict = {"top_sellers": [admin_home(), 0],
                   "top_buyers": [admin_filter_buyers(), 1],
                   "top_sellers_v": [admin_filter_seller_v(), 0],
                   "top_buyers_v" : [admin_filter_buyers_v(),1],
                   "upper_q_buyers": [admin_filter_upper_q(), 1],
                   "lower_q_buyers": [admin_filter_lower_q(), 1],
                   "inactive":  [admin_filter_inactive(), 1]
                   }
    func = filter_dict[data][0]
    if filter_dict[data][1]:
        input = "Purchases"
        input_two = "Purchase Price"
    else:
        input = "Sales"
        input_two = "Earnings"
    result = db.execute(func)
    rows = result.fetchall()
    c = 0
    products = {}
    for row in rows:
        my_dict = {}
        for i in range(7):
            my_dict[i] = row[i]
        products[c] = my_dict
        c += 1
    return render_template("admin.html", length=c, products=products, input=input, input_two=input_two)


def admin_filter_buyers():
    statement = f"""
    SELECT u.email, u.username, u.join_date, SUM(l.price) as total_purchase, COUNT(*) as total_volumes,
    ROUND(SUM(l.price)/COUNT(*),2) as purchase_per_item, CURRENT_DATE - u.join_date as daysjoin
    FROM users u, transactions t, listings l
    WHERE u.email = t.buyer
    AND t.listing = l.listingid
    GROUP BY u.email
    ORDER BY total_purchase DESC
    LIMIT(50); 
    """
    return sqlalchemy.text(statement)


def admin_filter_seller_v():
    statement = f"""
    SELECT u.email, u.username, u.join_date, SUM(l.price) as total_sales, COUNT(*) as total_volumes,
    ROUND(SUM(l.price)/COUNT(*),2) as earnings_per_item, CURRENT_DATE - u.join_date as daysjoin
    FROM users u, transactions t, listings l
    WHERE u.email = t.seller
    AND t.listing = l.listingid
    GROUP BY u.email
    ORDER BY total_volumes DESC
    LIMIT(50);
    """
    return sqlalchemy.text(statement)

def admin_filter_buyers_v():
    statement = f"""
    SELECT u.email, u.username, u.join_date, SUM(l.price) as total_purchase, COUNT(*) as total_volumes,
    ROUND(SUM(l.price)/COUNT(*),2) as purchase_per_item, CURRENT_DATE - u.join_date as daysjoin
    FROM users u, transactions t, listings l
    WHERE u.email = t.buyer
    AND t.listing = l.listingid
    GROUP BY u.email
    ORDER BY total_volumes DESC
    LIMIT(50); 
    """
    return sqlalchemy.text(statement)

def admin_filter_upper_q():
    statement = f"""
    SELECT u.email, u.username, u.join_date, SUM(l.price) as total_purchase, COUNT(*) as total_volumes,
    ROUND(SUM(l.price)/COUNT(*),2) as purchase_per_item, CURRENT_DATE - u.join_date as daysjoin
    FROM users u, transactions t, listings l
    WHERE u.email = t.buyer
    AND t.listing = l.listingid
    AND u.email IN (
        SELECT t1.buyer
        FROM transactions t1
        WHERE NOT EXISTS (
            SELECT * 
            FROM transactions t2, listings l1
            WHERE t2.listing = l1.listingid
            AND l1.price < (
                    SELECT PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY l2.price ASC) FROM listings l2
            )
        )
    GROUP BY t1.buyer
    )
    GROUP BY u.email
    ORDER BY total_purchase DESC
    LIMIT(50);
    """
    return sqlalchemy.text(statement)


def admin_filter_lower_q():
    statement = f"""
    SELECT u.email, u.username, u.join_date, SUM(l.price) as total_purchase, COUNT(*) as total_volumes,
    ROUND(SUM(l.price)/COUNT(*),2) as purchase_per_item, CURRENT_DATE - u.join_date as daysjoin
    FROM users u, transactions t, listings l
    WHERE u.email = t.buyer
    AND t.listing = l.listingid
    AND u.email IN (
        SELECT t1.buyer
        FROM transactions t1
        WHERE NOT EXISTS (
            SELECT * 
            FROM transactions t2, listings l1
            WHERE t2.listing = l1.listingid
            AND l1.price > (
                    SELECT PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY l2.price ASC) FROM listings l2
            )
        )
    GROUP BY t1.buyer
    )
    GROUP BY u.email
    ORDER BY total_purchase DESC
    LIMIT(50);
    """
    return sqlalchemy.text(statement)


def admin_filter_inactive():
    statement = f"""
    SELECT u.email, u.username, u.join_date, SUM(l.price) as total_purchase, COUNT(*) as total_volumes,
    ROUND(SUM(l.price)/COUNT(*),2) as purchase_per_item, CURRENT_DATE - u.join_date as daysjoin
    FROM users u, transactions t, listings l
    WHERE u.email = t.buyer
    AND t.listing = l.listingid
    AND u.email NOT IN (
    SELECT DISTINCT t.buyer
    FROM transactions t
    WHERE transactiondate between DATE_TRUNC('month', NOW() - INTERVAL '6 month') AND NOW()
    )
    GROUP BY u.email
    ORDER BY total_volumes DESC
    LIMIT(50);
    """
    return sqlalchemy.text(statement)


@app.post("/searchadminbutton")
def searchadminbutton():
    data = request.form.get("searchadminbutton")
    session["adminsearch"] = data
    return redirect(url_for("adminpage"))


def adminsearchquery(data):
    statement = f"""
    SELECT u.email, u.username, u.join_date, SUM(l.price) as total_sales, COUNT(*) as total_volumes,
    ROUND(SUM(l.price)/COUNT(*),2) as earnings_per_item, CURRENT_DATE - u.join_date as daysjoin
    FROM users u, transactions t, listings l
    WHERE u.email = t.seller
    AND t.listing = l.listingid
    AND u.username = '{data}'
    GROUP BY u.email
    ORDER BY total_sales DESC
    LIMIT(50);
    """
    return sqlalchemy.text(statement)

PORT = 2222

if __name__ == "__main__":
    # app.run("0.0.0.0", PORT)
    app.run(debug=True)
