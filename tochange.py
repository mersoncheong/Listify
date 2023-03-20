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
@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("/login")
    
@app.route("/register")
def register():
    return render_template("/register")

@app.post("/register")
# ? a flask decorator listening for POST requests at the url /table-insert and handles the entry insertion into the given table/relation
# * You might wonder why PUT or a similar request header was not used here. Fundamentally, they act as POST. So the code was kept simple here
def insert_into_table():
    try:
        data = {
        "name" : "registered",
        "body" : {
        "username": request.form.get("registername"),
        "email": request.form.get("registeremail"),
        "password": request.form.get("registerpassword")
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
        flash("email/username already exists!")
        return redirect(url_for("home"))
        # return Response(str(e), 403)

# @app.post("/login")
# def login_into_account():
#     try:
#         data = {
#         "name" : "registered",
#         "body" : {
#         "username": request.form.get("registername"),
#         "email": request.form.get("registeremail"),
#         "password": request.form.get("registerpassword")
#         }
#     }




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