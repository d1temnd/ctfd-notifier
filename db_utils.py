from CTFd.models import db

from .models import NotifierConfig


class DBUtils:
    DEFAULT_CONFIG = [
        {"key": "rabbit_notifier", "value": "false"},
        {"key": "rabbit_ip", "value": ""},
        {"key": "rabbit_port", "value": ""},
        {"key": "rabbit_topic", "value": ""},
        {"key": "telegram_bot_token", "value": ""},
        {"key": "telegram_chat_id", "value": ""},
        {"key": "telegram_message_thread_id", "value": ""},
        {"key": "telegram_template_message", "value": "<name> got first blood on <challenge> and is now in <place> place with <score> p"}
    ]

    @staticmethod
    def get(key):
        return NotifierConfig.query.filter_by(key=key).first()

    @staticmethod
    def get_config():
        configs = NotifierConfig.query.all()
        result = {}

        for c in configs:
            result[str(c.key)] = str(c.value)

        return result

    @staticmethod
    def save_config(config):
        for c in config:
            q = db.session.query(NotifierConfig)
            q = q.filter(NotifierConfig.key == c[0])
            record = q.one_or_none()

            if record:
                record.value = c[1]
                db.session.commit()
            else:
                config = NotifierConfig(key=c[0], value=c[1])
                db.session.add(config)
                db.session.commit()
        db.session.close()

    @staticmethod
    def load_default():
        for cv in DBUtils.DEFAULT_CONFIG:
            # Query for the config setting
            k = DBUtils.get(cv["key"])
            # If its not created, create it with its default value
            if not k:
                c = NotifierConfig(key=cv["key"], value=cv["value"])
                db.session.add(c)
        db.session.commit()