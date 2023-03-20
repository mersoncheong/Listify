from flask_cors import CORS, cross_origin
import json
from flask import Flask, redirect, url_for, render_template, request, Response, flash, session
import sqlalchemy
import psycopg2


app = Flask(__name__, template_folder= 'templates' , static_folder = 'static')
app.config['SECRET_KEY'] = "secret"

CORS(app)


YOUR_POSTGRES_PASSWORD = "Password.1"
connection_string = f"postgresql://postgres:{YOUR_POSTGRES_PASSWORD}@localhost/users"
engine = sqlalchemy.create_engine(connection_string)

db = engine.connect();



@app.route("/")
def home():
    return render_template("login.html")

@app.route("/marketplace")
def marketplace():
    return render_template("home.html");

@app.route("/user") 
def user():
    if "user" in session:
        user = session["user"]
        render_template("home.html", user =user)
    else:
        flash("Please Login")
        return redirect(url_for("home"))

@app.post("/login")
def login_into_account():
    try:
        data = {
        "name" : "registered",
        "email": request.form.get("email"),
        "password": request.form.get("password")
        }

        statement = check_login_state(data)
        result = db.execute(statement)
        # try:
        row = result.fetchone()
        value = row[0];
        # except:
        #     flash("Account does not exists")
        #     return redirect(url_for(home))
        if value != data["password"]:
            flash("Wrong Password")
            return redirect(url_for("home"))
        else:
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
        "name" : "registered",
        "body" : {
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

def check_login_state(insertion):
    table_name = "registered"
    email = insertion["email"]
    password = insertion["password"]
    string = f"{email}" + "," f"{password}"
    statement = f"SELECT password FROM {table_name} WHERE email = '{email}'"
    return sqlalchemy.text(statement)









def generate_insert_table_statement(insertion):
    # ? Fetching table name and the rows/tuples body object from the request
    table_name = insertion["name"]
    body = insertion["body"]
    # valueTypes = insertion["valueTypes"]

    # ? Generating the default insert statement template
    statement = f"INSERT INTO {table_name}  "

    # ? Appending the entries with their corresponding columns
    column_names = "("
    column_values = "("
    for key, value in body.items():
        column_names += (key+",")
        # if valueTypes[key] == "TEXT" or valueTypes[key] == "TIME":
        #     column_values += (f"\'{value}\',")
        # else:
        column_values += (f"'{value}',")

    # ? Removing the last default comma
    column_names = column_names[:-1]+")"
    column_values = column_values[:-1]+")"

    # ? Combining it all into one statement and returning
    #! You may try to expand it to multiple tuple insertion in another method
    statement = statement + column_names+" VALUES "+ column_values+";"
    return sqlalchemy.text(statement)








PORT = 2222;

if __name__ == "__main__":
     app.run(debug = True);