from flask import Flask, render_template

app = Flask("simple example")


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/statistic")
def statistic():
    return render_template("statistic.html")


app.run(debug=True)