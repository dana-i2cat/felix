from core.config import ConfParser
from flask import Blueprint
from flask import current_app
from flask import g
from flask import render_template

import ast

ro_flask_views = Blueprint("ro_flask_views", __name__)

@ro_flask_views.route("/")
def homepage():
    return render_template("index.html",
        db=current_app.db)

@ro_flask_views.route("/peers")
def peers():
    #domain_routing = g.mongo.db[current_app.db].domain.routing.find()
    domain_routing = [ p for p in current_app.mongo.get_configured_peers() ]
    # Retrieve domain URN per peer
    for route in domain_routing:
        try:
            peer_urns = []
            assoc_peers = current_app.mongo.get_info_peers({"_ref_peer": route["_id"]})
            for r in range(0, assoc_peers.count()):
                peer_urns.append(assoc_peers.next().get("domain_urn"))
            route["urn"] = peer_urns
        except:
            pass
    return render_template("peers.html", db=current_app.db, domain_routing=domain_routing)
