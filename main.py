from turtle import tracer
from flask import Flask, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session



app = Flask(__name__,template_folder="templates")
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3"
db = SQLAlchemy(app)
app.app_context().push()

#Sessions
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

groups = ['Chest', 'Triceps', 'Abs', 'Back', 'Biceps', 'Shoulders', 'Cardio']



class user(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True, nullable = False)
    username = db.Column(db.String, unique = True, nullable= False)
    first_name = db.Column(db.String, nullable = False)
    last_name = db.Column(db.String)
    password = db.Column(db.String, nullable = False)

    def get_user(self):
        return self.username

    def get_password(self):
        return self.password
    

class tracker(db.Model):
    __tablename__ = 'tracker'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True, nullable  = False)
    name = db.Column(db.String, nullable = False)
    option = db.Column(db.String, nullable = False)
    group = db.Column(db.String, nullable = False)
    description = db.Column(db.String)
    u_id = db.Column(db.String, db.ForeignKey(user.id), nullable= False)

class log(db.Model):
    __tablename__ = 'log'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True, nullable  = False)
    t_id = db.Column(db.Integer, db.ForeignKey(tracker.id), nullable = False)
    timestamp = db.Column(db.String, nullable = False)
    value_1 = db.Column(db.Integer, nullable = False)
    value_2 = db.Column(db.Integer, nullable = False)
    weight = db.Column(db.Integer)
    note = db.Column(db.String)


@app.route("/logout")
def logout():
    if 'user' in session:
        session.pop('user')
    return redirect(url_for("index"))


@app.route("/login", methods=["POST", "GET"])
def login():
  # if form is submited
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        active_user = user.query.filter_by(username = username).first()
        if ( active_user != None ):
            if active_user.password == password:
                session["user"] = username
                # redirect to the main page
                return redirect("/")
        return render_template("incorrect.html")
    else:
        return render_template("login.html")


@app.route("/signup", methods=["POST", "GET"])
def signup():
  # if form is submited
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        fname = request.form.get("firstname")
        lname = request.form.get("lastname")
        if (user.query.filter_by(username = username).all() != None):
                return render_template("userexists.html")
        usr = user(
            username = username,
            password = password,
            first_name = fname,
            last_name = lname
        )
        
        db.session.add(usr)
        db.session.commit()
        
        session["user"] = request.form.get("username")
        
        # redirect to the main page
        return redirect("/")
    else:
        return render_template("signup.html")



@app.route("/", methods = ['GET'])
def index():
        if 'user' in session:
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html")



@app.route('/dashboard')
def dashboard():
    username = session['user']

    trackers = tracker.query.filter_by(u_id = username)

if __name__ == "__main__":
    app.debug = True
    app.run()
