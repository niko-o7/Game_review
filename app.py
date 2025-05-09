from flask import Flask
import sqlite3
from flask import redirect, render_template, request, session, abort, make_response, flash
from werkzeug.security import generate_password_hash
import db
import config
import forum
import users
import secrets
import markupsafe
import math

app = Flask(__name__)
app.secret_key = config.secret_key



@app.route("/")
def index():
    return render_template("index.html")



#REGISTRATION
@app.route("/register")
def register():
    filled = {"username": ""}
    return render_template("register.html", filled=filled)

@app.route("/create", methods=["POST"])
def create():

    
    username = request.form["username"]
    filled = {"username": username}

    if len(username) > 16:
        flash("Username has to be less than 16 characters")
        return render_template("register.html", filled=filled)

    firstpassword = request.form["password1"]
    secondpassword = request.form["password2"]

    if firstpassword != secondpassword:
        flash("Error: Given passwords don't match")
        return render_template("register.html", filled=filled)

    try:
        users.create_user(username, firstpassword)
        
    except sqlite3.IntegrityError:
        flash("Error: username already exists")
        return render_template("register.html", filled=filled)
    
    flash("Account created!")
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_id = users.check_login(username, password)
        if user_id:
            session["user_id"] = user_id
            session["username"] = username
            session["csrf_token"] = secrets.token_hex(16)
            return redirect("/")
        else:
            flash("Error: wrong username or password")
            return redirect("/")

@app.route("/logout")
def logout():
    if "user_id" in session:
        del session["user_id"]
        del session["username"]
    flash("Logged out")
    return redirect("/")



#Reviews

@app.route("/reviewpage")
@app.route("/<int:page>")
def reviewpage(page=1):
    page_size = 15
    thread_count = forum.thread_count()
    page_count = math.ceil(thread_count / page_size)
    page_count = max(page_count, 1)

    if page < 1:
        return redirect("/reviewpage/1")
    if page > page_count:
        return redirect(f"/reviewpage/{page_count}")

    try:
        threads = forum.get_threads(page, page_size)
        return render_template("reviewpage.html", threads=threads, page=page, page_count=page_count)
    except:
        return render_template("reviewpage.html")




def check_csrf():
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

@app.route("/new_thread", methods=["POST"])
def new_thread():
    check_csrf()
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
    page = request.args.get("page", 1, type=int)
    per_page = 15
    if query:
        results, total_results = forum.search(query, page=page, per_page=per_page)
    else:
        results = []
    return render_template("reviewpage.html", query=query, total_results=total_results, threads=results, current_page=page, total_pages=(total_results + per_page - 1) // per_page)


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
    user = users.get_user(user_id)
    reviews = forum.user_reviews(user_id)
    reviewcount = forum.total_reviews(user_id)
    return render_template("profile.html", user=user, username = user["username"], reviews = reviews, reviewcount = reviewcount)

@app.route("/add_image", methods=["GET", "POST"])
def add_image():


    if request.method == "GET":
        return render_template("add_image.html")
    
    if request.method == "POST":
        file = request.files["image"]
        if not file.filename.endswith(".jpg"):
            flash("ERROR: wrong file type")
            return redirect("/add_image")
        
        image = file.read()
        if len(image) > 100 * 1024:
            flash("ERROR: file size too large")
            return redirect("/add_image")
        
        user_id = session["user_id"]
        users.update_image(user_id, image)
        return redirect("/profile")
    
@app.route("/image/<int:user_id>")
def show_image(user_id):
    image = users.get_image(user_id)
    if not image:
        abort(404)
    
    response = make_response(bytes(image))
    response.headers.set("Content-Type", "image/jpeg")
    return response


@app.template_filter()
def show_lines(content):
    content = str(markupsafe.escape(content))
    content = content.replace("\n", "<br />")
    return markupsafe.Markup(content)