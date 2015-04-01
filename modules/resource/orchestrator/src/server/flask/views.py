from core.config import ConfParser
from flask import Blueprint
from flask import g
from flask import render_template

import ast

ro_flask_views = Blueprint("ro_flask_views", __name__)

@ro_flask_views.route("/")
def homepage():
    # XXX Load mongoDB info from ro.conf file or similar
    config = ConfParser("ro.conf")
    master_ro = config.get("master_ro")
    mro_enabled = ast.literal_eval(master_ro.get("mro_enabled"))
    if mro_enabled:
        db_name = "felix_mro"
    else:
        db_name = "felix_ro"
    # g.mongo has been previously "attached" for the request
    routing_table = g.mongo.db[db_name].domain.routing.find()
    return render_template("index.html",
        routing_table=routing_table)
