from flask import Flask, render_template

app = Flask(__name__);




@app.route("/")  #path used to get to function
def home():
    return render_template("index.html")

# @app.route("/")
# def some_page(name):
#     return render_template("something.html" = content = name)










PORT = 2222 

if __name__ == "__main__":
    app.run("0.0.0.0", PORT)
    # app.run()