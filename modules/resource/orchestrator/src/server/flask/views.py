from flask import Blueprint
from flask import g
from flask import render_template

ro_flask_views = Blueprint("ro_flask_views", __name__)

@ro_flask_views.route("/")
def homepage():
    # g.mongo has been previously "attached" for the request
    # XXX Load mongoDB info from ro.conf file or similar
    routing_table = g.mongo.db["felix_ro_"].domain.routing.find()
    return render_template("index.html",
        routing_table=routing_table)
