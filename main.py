

from matplotlib import pyplot as plt
import matplotlib.dates
from flask import Flask, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import copy

from flask_restful import Resource
from flask_restful import Api
from flask_restful import fields
from flask_restful import marshal_with
from flask_restful import reqparse
from flask import make_response

from werkzeug.exceptions import HTTPException

app = Flask(__name__, template_folder="templates")
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3"
db = SQLAlchemy(app)
api = Api(app)
app.app_context().push()

# Sessions
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

group_options = ['Chest', 'Triceps', 'Abs',
                 'Back', 'Biceps', 'Shoulders', 'Cardio']


class user(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True,
                   autoincrement=True, nullable=False)
    username = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)
    password = db.Column(db.String, nullable=False)

    def get_user(self):
        return self.username

    def get_password(self):
        return self.password


class tracker(db.Model):
    __tablename__ = 'tracker'
    id = db.Column(db.Integer, primary_key=True,
                   autoincrement=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    option = db.Column(db.String, nullable=False)
    group = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    u_id = db.Column(db.String, db.ForeignKey(user.id), nullable=False)


class log(db.Model):
    __tablename__ = 'log'
    id = db.Column(db.Integer, primary_key=True,
                   autoincrement=True, nullable=False)
    t_id = db.Column(db.Integer, db.ForeignKey(tracker.id), nullable=False)
    timestamp = db.Column(db.String, nullable=False)
    value_1 = db.Column(db.Integer, nullable=False)
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
    if 'user' in session:
        return redirect(url_for('index'))

  # if form is submited
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        active_user = user.query.filter_by(username=username).first()
        if (active_user != None):
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
    if 'user' in session:
        session.pop('user')
        return redirect(url_for("index"))

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        fname = request.form.get("firstname")
        lname = request.form.get("lastname")

        if (len(user.query.filter_by(username=username).all()) > 0):
            return render_template("userexists.html")
        usr = user(
            username=username,
            password=password,
            first_name=fname,
            last_name=lname
        )

        db.session.add(usr)
        db.session.commit()

        session["user"] = request.form.get("username")

        # redirect to the main page
        return redirect("/")
    else:
        return render_template("signup.html")


@app.route("/", methods=['GET'])
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

    uid = user.query.filter_by(username=username).first().id
    tids = []

    groups = {}
    trackers = tracker.query.filter_by(u_id=uid).all()
    for t in trackers:
        tids.append(t.id)
        if t.group not in groups.keys():
            groups[t.group] = [copy.copy(t)]
        else:
            groups[t.group].append(copy.copy(t))

    # Getting top 5 recent logs
    ulogs = db.session.execute(
        'select log.timestamp, log.value_1, log.value_2, log.weight, log.note, tracker.name, tracker.option from log, tracker where log.t_id = tracker.id and log.t_id in (select t.id from user u, tracker t where t.u_id = u.id and u.id={uid}) order by log.id desc limit 5'.format(uid=uid))

    return render_template("dashboard.html", groups=groups, ulogs=ulogs)


@app.route('/add_tracker', methods=['GET', 'POST'])
def add_tracker():
    if 'user' not in session:
        return redirect(url_for('index'))
    username = session['user']
    if request.method == "GET":

        user_groups = []
        for g in group_options:
            user_groups.append(g)

        uid = user.query.filter_by(username=username).first().id
        trackers = tracker.query.filter_by(u_id=uid).all()
        for t in trackers:
            if t.group not in user_groups:
                user_groups.append(t.group)

        return render_template("add_tracker.html", group_options=user_groups)
    else:
        uid = user.query.filter_by(username=username).first().id
        new_tracker = tracker(

            name=request.form.get("name"),
            option=request.form.get("type"),
            group=request.form.get("group"),
            description=request.form.get("description"),
            u_id=uid
        )
        db.session.add(new_tracker)
        db.session.commit()
        return redirect(url_for("index"))


@app.route("/log/<int:tid>", methods=["GET", "POST"])
def enter_log(tid):
    if 'user' not in session:
        return redirect(url_for('index'))

    if request.method == "GET":
        current_tracker = tracker.query.filter_by(id=tid).first()
        return render_template("log.html", tracker=current_tracker)

    else:
        dt = request.form.get("datetime")
        value1 = request.form.get("value1")
        value2 = request.form.get("value2")
        weight = request.form.get("weight")
        note = request.form.get("note")

        new_log = log(
            t_id=tid,
            timestamp=dt,
            value_1=value1,
            value_2=value2,
            weight=weight,
            note=note
        )

        db.session.add(new_log)
        db.session.commit()

        return redirect(url_for("index"))


@app.route("/delete_tracker/<int:tid>")
def delete_tracker(tid):
    if 'user' not in session:
        return redirect(url_for('index'))

    tracker.query.filter_by(id=tid).delete()
    log.query.filter_by(t_id=tid).delete()

    db.session.commit()

    return redirect(url_for("index"))


@app.route("/update_tracker/<int:tid>", methods=['GET', 'POST'])
def update_tracker(tid):
    if 'user' not in session:
        return redirect(url_for('index'))

    username = session['user']
    if request.method == "GET":
        track = tracker.query.filter_by(id=tid).first()
        user_groups = []
        for g in group_options:
            user_groups.append(g)

        uid = user.query.filter_by(username=username).first().id
        trackers = tracker.query.filter_by(u_id=uid).all()
        for t in trackers:
            if t.group not in user_groups:
                user_groups.append(t.group)
        return render_template("update_tracker.html", tracker=track, group_options=user_groups)

    else:
        tracker.query.filter_by(id=tid).update({tracker.name: request.form.get("name"),
                                                tracker.group: request.form.get("group"),
                                                tracker.description: request.form.get("description"),
                                                })
        db.session.commit()
        return redirect(url_for('index'))


@app.route("/view_log/<int:tid>")
def view_log(tid):
    if 'user' not in session:
        return redirect(url_for('index'))

    if request.method == "GET":
        tname = tracker.query.filter_by(id=tid).first().name
        logs = db.session.execute(
            "select * from log where t_id = {tid} order by id desc".format(tid=tid))
        return render_template("view_log.html", logs=logs, tname=tname)


@app.route("/delete_log/<int:lid>", methods=["GET"])
def delete_log(lid):
    if 'user' not in session:
        return redirect(url_for('index'))

    tid = log.query.filter_by(id=lid).first().t_id
    log.query.filter_by(id=lid).delete()
    db.session.commit()
    return redirect(url_for("view_log", tid=tid))


@app.route("/update_log/<int:lid>", methods=["GET", "POST"])
def update_log(lid):
    if 'user' not in session:
        return redirect(url_for('index'))

    ulog = log.query.filter_by(id=lid).first()
    utracker = tracker.query.filter_by(id=ulog.t_id).first()
    if request.method == "GET":
        return render_template("update_log.html", ulog=ulog, tracker=utracker)

    else:
        if request.form.get("choose") == 'existing':
            log.query.filter_by(id=lid).update({log.value_1: request.form.get("value1"),
                                                log.value_2: request.form.get("value2"),
                                                log.weight: request.form.get("weight"),
                                                log.note: request.form.get(
                                                    "note")
                                                })
        else:
            log.query.filter_by(id=lid).update({log.timestamp: request.form.get("datetime"),
                                                log.value_1: request.form.get("value1"),
                                                log.value_2: request.form.get("value2"),
                                                log.weight: request.form.get("weight"),
                                                log.note: request.form.get(
                                                    "note")
                                                })
        db.session.commit()
        return redirect(url_for("view_log", tid=utracker.id))


@app.route("/analyze_tracker/<int:tid>")
def analyze_tracker(tid):
    if 'user' not in session:
        return redirect(url_for('index'))

    utracker = tracker.query.filter_by(id=tid).first()
    ulogs = log.query.filter_by(t_id=tid).all()

    # plt.clf()

    # total reps for sets and reps
    if utracker.option == "Sets and Reps":
        x_axis = []
        y_axis = []
        for l in ulogs:
            x_axis.append(l.timestamp.split("T")[0])
            y_axis.append(l.value_1 * l.value_2)
        x_axis = matplotlib.dates.datestr2num(x_axis)
        plt.plot_date(x_axis, y_axis, color='Teal', xdate=True)
        plt.xlabel("day")
        plt.ylabel("total reps")
        
    elif utracker.option == "Minutes":
        x_axis = []
        y_axis = []
        for l in ulogs:
            x_axis.append(l.timestamp.split("T")[0])
            y_axis.append(l.value_1)
        x_axis = matplotlib.dates.datestr2num(x_axis)
        plt.plot_date(x_axis, y_axis, color='Teal', xdate=True)
        plt.xlabel("day")
        plt.ylabel("Minutes")
    else:
        x_axis = []
        y_axis = []
        for l in ulogs:
            x_axis.append(l.timestamp.split("T")[0])
            y_axis.append(l.value_1)
        x_axis = matplotlib.dates.datestr2num(x_axis)
        plt.plot_date(x_axis, y_axis, color='Teal', xdate=True)
        plt.xlabel("day")
        plt.ylabel("Seconds")

    plt.savefig('static/myplot.png')
    plt.close()
    return render_template("analyze_tracker.html", tracker=utracker)

# -------------Tracker API ------------------------------------------


tracker_op = {
    "id": fields.Integer,
    "name": fields.String,
    "option": fields.String,
    "group": fields.String,
    "description": fields.String,
    "u_id": fields.Integer
}
    

class TrackerNotFound(HTTPException):
    def __init__(self, status_code, error_msg):
        self.response = make_response(error_msg, status_code, {
                                      "Content-Type": "application/json"})


create_tracker_parser = reqparse.RequestParser()
create_tracker_parser.add_argument("name")
create_tracker_parser.add_argument("u_id")
create_tracker_parser.add_argument("type")
create_tracker_parser.add_argument("description")
create_tracker_parser.add_argument("group")

update_tracker_parser = reqparse.RequestParser()
update_tracker_parser.add_argument("name")
update_tracker_parser.add_argument("description")
update_tracker_parser.add_argument("group")


class trackerAPI(Resource):

    @marshal_with(tracker_op)
    def get(self, id):
        utrack = tracker.query.filter_by(id=id).first()
        if utrack:
            return utrack, 200
        else:
            raise TrackerNotFound(
                status_code=404, error_msg="tracker not found")

    @marshal_with(tracker_op)
    def put(self, id):
        args = update_tracker_parser.parse_args()
        utrack = tracker.query.filter_by(id=id).first()
        if utrack:
            tracker.query.filter_by(id=id).update({tracker.name: args.get("name"),
                                                   tracker.group: args.get("group"),
                                                   tracker.description: args.get("description")})
            db.session.commit()
            utrack = tracker.query.filter_by(id=id).first()
            return utrack, 200
        else:
            raise TrackerNotFound(
                status_code=404, error_msg="tracker not found")

    @marshal_with(tracker_op)
    def delete(self, id):
        utrack = tracker.query.filter_by(id=id).first()
        if utrack:
            tracker.query.filter_by(id=id).delete()
            db.session.commit()
            return utrack, 200
        else:
            raise TrackerNotFound(
                status_code=404, error_msg="tracker not found")

    @marshal_with(tracker_op)
    def post(self):
        args = create_tracker_parser.parse_args()
        utrack = tracker(name =args.get('name'),
                         u_id = args.get('u_id'),
                         option = args.get('type'),
                         group = args.get('group'),
                         description = args.get('description'))
        db.session.add(utrack)
        db.session.commit()
        return utrack, 200
        


api.add_resource(trackerAPI, "/api/tracker", "/api/tracker/<int:id>")


#---------------------- Log API -----------------------------------------

tracker_op = {
    "id": fields.Integer,
    "t_id": fields.Integer,
    "timestamp": fields.String,
    "value_1": fields.Integer,
    "value_2": fields.Integer,
    "weight": fields.String,
    "note": fields.String
}

class LogNotFound(HTTPException):
    def __init__(self, status_code, error_msg):
        self.response = make_response(error_msg, status_code, {
                                      "Content-Type": "application/json"})

create_log_parser = reqparse.RequestParser()
create_log_parser.add_argument("t_id")
create_log_parser.add_argument("timestamp")
create_log_parser.add_argument("value1")
create_log_parser.add_argument("value2")
create_log_parser.add_argument("weight")
create_log_parser.add_argument("note")

update_log_parser = reqparse.RequestParser()
update_log_parser.add_argument("timestamp")
update_log_parser.add_argument("value1")
update_log_parser.add_argument("value2")
update_log_parser.add_argument("weight")
update_log_parser.add_argument("note")

class logAPI(Resource):

    @marshal_with(tracker_op)
    def get(self, id):
        ulog = log.query.filter_by(id = id).first()
        if ulog:
            return ulog, 200
        else:
            raise LogNotFound(status_code=404, error_msg="could not find")
    
    @marshal_with(tracker_op)
    def delete(self, id):
        ulog = log.query.filter_by(id = id).first()
        if ulog:
            log.query.filter_by(id = id).delete()
            db.session.commit()
            return ulog, 200
        else:
            raise LogNotFound(status_code=404, error_msg="could not find")

    @marshal_with(tracker_op)
    def put(self, id):
        args = update_log_parser.parse_args()
        ulog = log.query.filter_by(id = id).first()
        if ulog:
            log.query.filter_by(id = id).update({
                log.timestamp: args.get('timestamp'),
                log.value_1: args.get('value1'),
                log.value_2: args.get("value2"),
                log.weight: args.get("weight"),
                log.note: args.get("note")
            })

            db.session.commit()

            ulog = log.query.filter_by(id = id).first()

            return ulog, 200
        else:
            raise LogNotFound(status_code=404, error_msg="could not find")

    @marshal_with(tracker_op)
    def post(self):
        args = create_log_parser.parse_args()
        
        ulog = log(
            t_id = args.get("t_id"),
            timestamp = args.get("timestamp"),
            value_1 = args.get("value1"),
            value_2 = args.get('value2'),
            weight = args.get('weight'),
            note = args.get('note')
        )

        db.session.add(ulog)
        db.session.commit()

        return ulog, 200

api.add_resource(logAPI, "/api/log", "/api/log/<int:id>")


if __name__ == "__main__":
    app.debug = True
    app.run()
