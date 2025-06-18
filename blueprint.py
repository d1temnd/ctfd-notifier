from CTFd.utils.decorators import admins_only
from flask import Blueprint, render_template, request

from .db_utils import DBUtils

notifier_bp = Blueprint("notifier", __name__, template_folder="templates")


def load_bp(plugin_route):
    @notifier_bp.route(plugin_route, methods=["GET"])
    @admins_only
    def get_config():
        config = DBUtils.get_config()
        return render_template("ctfd_notifier/config.html", config=config)

    @notifier_bp.route(plugin_route, methods=["POST"])
    @admins_only
    def update_config():
        config = request.form.to_dict()
        del config["nonce"]

        errors = test_config(config)

        if len(errors) > 0:
            return render_template(
                "ctfd_notifier/config.html", config=DBUtils.get_config(), errors=errors
            )
        else:
            DBUtils.save_config(config.items())
            return render_template(
                "ctfd_notifier/config.html", config=DBUtils.get_config()
            )

    return notifier_bp


def test_config(config):
    errors = list()
    error = False
    if "discord_notifier" in config:
        if config["discord_notifier"]:
            webhookurl = config["discord_webhook_url"]
            if error:
                errors.append("test error")

    return errors