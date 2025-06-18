import json
from asyncio import run
from pika import BlockingConnection, ConnectionParameters
import CTFd.cache as cache
from aiogram import Bot
from CTFd.models import Challenges, Solves, Teams, Users
from CTFd.utils.config import is_teams_mode
from sqlalchemy.event import listen

from ...utils.modes import get_model
from .db_utils import DBUtils





def rabbit_notify(
    solve, rabbit_ip, rabbit_port, rabbit_topic
):
    connection_params = ConnectionParameters(
        host=str(rabbit_ip), 
        port=int(rabbit_port)
    )
    json_text: json = _getText(solve, True)

    with BlockingConnection(connection_params) as conn:
        ch = conn.channel()
        ch.queue_declare(queue=rabbit_topic, durable=True)

        ch.basic_publish(
            exchange='',
            routing_key=rabbit_topic,
            body=json.dumps(json_text),
            properties=None  # можно сюда добавить delivery_mode=2 для персистентности
        )


def telegram_notify(solve, token: str, chat_id: int, message_thread_id: int):
    text = _getText(solve)
    bot = Bot(token)
    run(bot.send_message(chat_id, text, message_thread_id))


def on_solve(mapper, conn, solve):
    config = DBUtils.get_config()
    solves = _getSolves(solve.challenge_id)

    if solves == 1:

        if config.get("rabbit_notifier") == "true":
            rabbit_notify(
                solve,
                config.get("rabbit_ip"),
                config.get("rabbit_port"),
                config.get("rabbit_topic"),
            )

        if config.get("telegram_notifier") == "true":
            telegram_notify(
                solve,
                config.get("telegram_bot_token"),
                config.get("telegram_chat_id"),
                config.get("telegram_message_thread_id"),
            )


def _getSolves(challenge_id):
    Model = get_model()

    solve_count = (
        Solves.query.join(Model, Solves.account_id == Model.id)
        .filter(
            Solves.challenge_id == challenge_id,
            Model.hidden == False,
            Model.banned == False,
        )
        .count()
    )

    return solve_count


def _getChallenge(challenge_id):
    challenge = Challenges.query.filter_by(id=challenge_id).first()
    return challenge


def _getUser(user_id):
    user = Users.query.filter_by(id=user_id).first()
    return user


def _getTeam(team_id):
    team = Teams.query.filter_by(id=team_id).first()
    return team


def _getText(solve, json_r=False):
    name = ""
    score = 0
    place = 0
    cache.clear_standings()
    user = _getUser(solve.user_id)
    challenge = _getChallenge(solve.challenge_id)
    config = DBUtils.get_config()

    if is_teams_mode():
        team = _getTeam(user.team_id)
        name = team.name
        score = team.get_score()
        place = team.get_place()
    else:
        name = user.name
        score = user.get_score()
        place = user.get_place()

    if not json_r:
        
        text = str(config.get("telegram_template_message"))\
            .replace("<name>", name)\
            .replace("<challenge>", challenge.name)\
            .replace("<place>", str(place))\
            .replace("<score>", str(score))
    else:
        text = {"rase": "ctfd", "name": name, "task": challenge.name}

    return text


def load_hooks():
    listen(Solves, "after_insert", on_solve)
