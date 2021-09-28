import os
from flask import (Flask, flash, render_template,
                   redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_tasks")
def get_tasks():
    tasks = list(mongo.db.tasks.find())
    return render_template("tasks.html", tasks=tasks)


# Function for Search
@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    tasks = list(mongo.db.tasks.find({"$text" : {"$search" : query}}))
    return render_template("tasks.html", tasks=tasks)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check if user already exists in DB
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash ("Username already exists")
            return redirect(url_for('register'))

        # Create new username/password dictionary to add to DB
        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration successful")
        return redirect(url_for('profile', username=session["user"]))

    return render_template("register.html")

# function for Log In 
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if user already exists in DB
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # Check hashed passwords match:
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get("username").lower()))
                return redirect(url_for('profile', username=session["user"]))
            else:
                # password doesn't match
                flash("Username and/or Password incorrect, please try again")
                return redirect(url_for('login'))

        else:
            # username does not exist
            flash("Username and/or Password incorrect, please try again")
            return redirect(url_for('login'))

    return render_template("login.html")


# function for Profile
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # Grab the session user's username from the db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)
    else:
        return redirect(url_for('login'))


# Function for log Out
@app.route("/logout")
def logout():
    # Clear the session user cookie
    flash("You have been Logged out")
    session.pop("user")
    return redirect(url_for('login'))


# Function for Add Task
@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        # Create new task dictionary to add to DB
        is_urgent = "on" if request.form.get("is_urgent") else "off"
        task={
            "category_name": request.form.get("category_name"),
            "task_name": request.form.get("task_name"),
            "task_description": request.form.get("task_description"),
            "due_date": request.form.get("due_date"),
            "is_urgent": is_urgent,
            "created_by": session["user"]
        }
        mongo.db.tasks.insert_one(task)
        flash("Task successfully created")
        return redirect(url_for('get_tasks'))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_task.html", categories=categories)


# Function for Edit Task
@app.route("/edit_task/<task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if request.method == "POST":
            # Create new task dictionary to add to DB
            is_urgent = "on" if request.form.get("is_urgent") else "off"
            update={
                "category_name": request.form.get("category_name"),
                "task_name": request.form.get("task_name"),
                "task_description": request.form.get("task_description"),
                "due_date": request.form.get("due_date"),
                "is_urgent": is_urgent,
                "created_by": session["user"]
            }
            mongo.db.tasks.update({"_id": ObjectId(task_id)}, update)
            flash("Task successfully updated")
            return redirect(url_for('get_tasks'))

    task= mongo.db.tasks.find_one({"_id": ObjectId(task_id)})

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_task.html", task=task, categories=categories)


# Function for Delete Task
@app.route("/delete_task/<task_id>")
def delete_task(task_id):
   mongo.db.tasks.remove({"_id": ObjectId(task_id)})
   flash("Task has successfully been removed")
   return redirect(url_for('get_tasks'))


# Function for Manage Categories
@app.route("/get_categories")
def get_categories():
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories)

# Function for Add Categroy
@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        # Create new caetgory dictionary to add to DB
        category={
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash("category successfully created")
        return redirect(url_for('get_tasks'))

    return render_template("add_category.html")


# Function for Edit Category
@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
            # Create new category dictionary to add to DB
            update={
                "category_name": request.form.get("category_name")
            }
            mongo.db.categories.update({"_id": ObjectId(category_id)}, update)
            flash("Category successfully updated")
            return redirect(url_for('get_categories'))

    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category)

# Function for Delete Category
@app.route("/delete_category/<category_id>")
def delete_category(category_id):
   mongo.db.categories.remove({"_id": ObjectId(category_id)})
   flash("Category has successfully been removed")
   return redirect(url_for('get_categories'))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
