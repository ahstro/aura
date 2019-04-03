from beets.plugins import BeetsPlugin
from beets import ui
import flask
from flask import Flask, Blueprint


# Constants
AURA_SPEC_VERSION = "0.2.0"
SERVER_NAME = "beets-aura-plugin"
SERVER_VERSION = "0.1.0"


# Routes

api = Blueprint("api", __name__)


@api.route("/server")
def server():
    """Exposes global information and status for the AURA server."""
    return flask.jsonify(
        {
            "data": {
                "id": 0,
                "type": "server",
                "attributes": {
                    "aura-version": AURA_SPEC_VERSION,
                    "server": SERVER_NAME,
                    "server-version": SERVER_VERSION,
                    "auth-required": True,
                },
            }
        }
    )


# Flask

app = Flask(__name__)
app.register_blueprint(api, url_prefix="/aura")


# Plugin


class AuraPlugin(BeetsPlugin):
    """Serve the beets library through an AURA API"""

    def __init__(self):
        super(AuraPlugin, self).__init__()
        self.config.add(
            {
                "host": u"127.0.0.1",
                "port": 8338,
                "cors": "",
                "cors_supports_credentials": False,
                "reverse_proxy": False,
                "include_paths": False,
            }
        )

    def commands(self):
        """Register "aura" subcommand for starting server."""
        cmd = ui.Subcommand("aura", help=u"serve library through aura api")
        cmd.parser.add_option(
            u"-d", u"--debug", action="store_true", default=False, help=u"debug mode"
        )

        def func(lib, opts, args):
            args = ui.decargs(args)
            if args:
                self.config["host"] = args.pop(0)
            if args:
                self.config["port"] = int(args.pop(0))

            app.config["lib"] = lib
            # Normalizes json output
            app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

            app.config["INCLUDE_PATHS"] = self.config["include_paths"]

            # Enable CORS if required.
            if self.config["cors"]:
                self._log.info(u"Enabling CORS with origin: {0}", self.config["cors"])
                from flask_cors import CORS

                app.config["CORS_ALLOW_HEADERS"] = "Content-Type"
                app.config["CORS_RESOURCES"] = {
                    r"/*": {"origins": self.config["cors"].get(str)}
                }
                CORS(
                    app,
                    supports_credentials=self.config["cors_supports_credentials"].get(
                        bool
                    ),
                )

            # Allow serving behind a reverse proxy
            if self.config["reverse_proxy"]:
                app.wsgi_app = ReverseProxied(app.wsgi_app)

            # Start the web application.
            app.run(
                host=self.config["host"].as_str(),
                port=self.config["port"].get(int),
                debug=opts.debug,
                threaded=True,
            )

        cmd.func = func

        return [cmd]
