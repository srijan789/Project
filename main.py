from crypt import methods
from turtle import tracer
from flask import Flask, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import copy



app = Flask(__name__,template_folder="templates")
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3"
db = SQLAlchemy(app)
app.app_context().push()

#Sessions
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

group_options = ['Chest', 'Triceps', 'Abs', 'Back', 'Biceps', 'Shoulders', 'Cardio']



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
    value_2 = db.Column(db.Integer)
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

        if (len(user.query.filter_by(username = username).all()) > 0 ):
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

    if 'user' not in session:
        return redirect(url_for('index'))

    username = session['user']

    uid = user.query.filter_by(username = username).first().id

    groups = {}
    trackers = tracker.query.filter_by(u_id = uid).all()
    for t in trackers:
        if t.group not in groups.keys():
            groups[t.group] = [copy.copy(t)]
        else:
            groups[t.group].append(copy.copy(t))
    
    return render_template("dashboard.html", groups = groups)

@app.route('/add_tracker', methods = ['GET', 'POST'])
def add_tracker():
    if 'user' not in session:
        return redirect(url_for('index'))
    username = session['user']
    if request.method == "GET":
        

        user_groups = []
        for g in group_options:
            user_groups.append(g)

        uid = user.query.filter_by(username = username).first().id
        trackers = tracker.query.filter_by(u_id = uid).all()
        for t in trackers:
            if t.group not in user_groups:
                user_groups.append(t.group)
        
        return render_template("add_tracker.html", group_options = user_groups)
    else:
        uid = user.query.filter_by(username = username).first().id
        new_tracker = tracker(
            name = request.form.get("name"),
            option = request.form.get("type"),
            group = request.form.get("group"),
            description = request.form.get("description"),
            u_id = uid
        )
        db.session.add(new_tracker)
        db.session.commit()
        return redirect(url_for("index"))

@app.route("/log/<int:t_id>", methods = ["GET","POST"])
def log(t_id):
    if 'user' not in session:
        return redirect(url_for('index'))
    
    if request.method == "GET":
        current_tracker = tracker.query.filter_by(id = t_id).first()
        return render_template("log.html", tracker = current_tracker)
    else:
        




if __name__ == "__main__":
    app.debug = True
    app.run()
