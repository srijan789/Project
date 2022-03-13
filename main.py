from turtle import tracer
from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user



app = Flask(__name__,template_folder="templates")
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3"
db = SQLAlchemy(app)
app.app_context().push()


login_manager = LoginManager()


class user(UserMixin,db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True, nullable = False)
    email_id = db.Column(db.String, unique = True, nullable = False)
    username = db.Column(db.String, unique = True, nullable= False)
    first_name = db.Column(db.String, nullable = False)
    last_name = db.Column(db.String)
    password = db.Column(db.String, nullable = False)

class tracker(db.Model):
    __tablename__ = 'tracker'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True, nullable  = False)
    name = db.Column(db.String, nullable = False)
    type = db.Column(db.String, nullable = False)
    description = db.Column(db.String)
    u_id = db.Column(db.String, db.ForeignKey(user.id), nullable= False)

class log(db.Model):
    __tablename__ = 'log'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True, nullable  = False)
    t_id = db.Column(db.Integer, db.ForeignKey(tracker.id), nullable = False)
    timestamp = db.Column(db.String, nullable = False)
    value = db.Column(db.String, nullable = False)
    note = db.Column(db.String)

@app.route("/", methods = ['GET',"POST"])
def index():
    if request.method == "GET":
        return render_template("login.html")
    else:
        username = request.form["username"]
        return redirect("/user/"+username)

@app.route('/user/<int:username>')
def dashboard(username):
    trackers = tracker.query.filter_by(u_id = username)

if __name__ == "__main__":
    app.debug = True
    app.run()
