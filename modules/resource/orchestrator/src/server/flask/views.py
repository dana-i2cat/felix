from flask import Blueprint
from flask import current_app
from flask import g
from flask import render_template
from flask import request

import methods

ro_flask_views = Blueprint("ro_flask_views", __name__)


@ro_flask_views.route("/", methods = ["GET"])
def homepage():
    return render_template("index.html",
        db=current_app.db)

@ro_flask_views.route("/db/peers", methods = ["GET"])
@methods.check_cli_user_agent
def db_peers():
    try:
        output = methods.get_peers()
        return methods.parse_output_json(output)
    except Exception as e:
        return "Error: %s" % str(e)

@ro_flask_views.route("/db/vlans/used/tn", methods = ["GET"])
@methods.check_cli_user_agent
def db_tn_vlans():
    try:
        output = methods.get_used_tn_vlans()
        return methods.parse_output_json(output)
    except Exception as e:
        return "Error: %s" % str(e)

@ro_flask_views.route("/gui/peers", methods = ["GET"])
@methods.check_gui_user_agent
def gui_peers():
    try:
        output = methods.get_peers()
        return render_template("peers.html", db=current_app.db, domain_routing=output)
    except Exception as e:
        return "Error: %s" % str(e)
