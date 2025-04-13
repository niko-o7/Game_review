from flask import Flask
import sqlite3
from flask import redirect, render_template, request, session, abort
from werkzeug.security import generate_password_hash
import db
import config
import forum
import users



app = Flask(__name__)
app.secret_key = config.secret_key



@app.route("/")
def index():
    return render_template("index.html")



#REGISTRATION
@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():

    
    username = request.form["username"]
    firstpassword = request.form["password1"]
    secondpassword = request.form["password2"]
    if firstpassword != secondpassword:
        return "Error: Given passwords don't match"
    #password_hash = generate_password_hash(firstpassword)
    
    try:
        users.create_user(username, firstpassword)
        #sql = "INSERT INTO users (username, password_hash) VALUES (?,?)"
        #db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "Error: username already exists"
    
    return "Account created"

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_id = users.check_login(username, password)
        if user_id:
            session["user_id"] = user_id
            session["username"] = username
            return redirect("/")
        else:
            return "Error: wrong username or password"

@app.route("/logout")
def logout():
    if "user_id" in session:
        del session["user_id"]
        del session["username"]
    return redirect("/")



#Reviews

@app.route("/reviewpage")
def reviewpage():
    try:
        threads = forum.get_threads()
        return render_template("reviewpage.html", threads=threads)
    except:
        return render_template("reviewpage.html")

@app.route("/new_thread", methods=["POST"])
def new_thread():
    title = request.form["title"]
    genres = request.form.getlist("genres")
    grade = request.form.get("grade")
    text = request.form["review"]

    user_id = session["user_id"]
    
    genres = ",".join(genres)
    thread_id = forum.add_thread(title, genres, grade, text, user_id)
    return redirect("/thread/" + str(thread_id))

@app.route("/thread/<int:thread_id>")
def view_thread(thread_id):
    thread = forum.get_thread(thread_id)
    if not thread:
        abort(404)
    #author = users.get_user(thread["user_id"])
    comments = forum.get_comments(thread_id)
    return render_template("thread.html", thread=thread, author=thread["author_username"], comments=comments or [])

@app.route("/edit/<int:thread_id>", methods=["GET", "POST"])
def edit_thread(thread_id):
    thread = forum.get_thread(thread_id)
    if request.method == "GET":
        return render_template("edit.html", thread=thread)
    if request.method == "POST":
        review = request.form["review"]
        forum.update_thread(thread["thread_id"], review)
        return redirect("/thread/" + str(thread["thread_id"]))

@app.route("/remove/<int:thread_id>", methods = ["GET", "POST"])
def remove_thread(thread_id):
    thread = forum.get_thread(thread_id)

    if request.method == "GET":
        return render_template("remove.html", thread=thread)
    
    if request.method == "POST":
        if "continue" in request.form:
            forum.remove_thread(thread["thread_id"])
        return redirect("/reviewpage")


@app.route("/search")
def search():
    query = request.args.get("query", "").strip()
    results = forum.search(query) if query else []
    return render_template("reviewpage.html", query=query, results=results, threads=forum.get_threads())


#comment section

@app.route("/thread/<int:thread_id>/comment", methods=["POST"])
def add_comment(thread_id):
    content = request.form.get("content")
    forum.add_comment(thread_id, session["user_id"], content)
    thread = forum.get_thread(thread_id)
    return redirect("/thread/" + str(thread["thread_id"]))

@app.route("/comment/<int:comment_id>/delete", methods=["POST"])
def delete_comment(comment_id):
    forum.delete_comment(comment_id, session["user_id"])
    return redirect(request.referrer)


#profile

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    username = session.get("username")
    reviews = forum.user_reviews(user_id)
    reviewcount = forum.total_reviews(user_id)
    return render_template("profile.html", username = username, reviews = reviews, reviewcount = reviewcount)