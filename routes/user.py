from aiohttp.web import json_response
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiologger.loggers.json import JsonLogger

from helpers.response import json_error_400
from helpers.validator import validate
from models.battle import Battle
from models.user import User

logger = JsonLogger.with_default_handlers()


def init(app):
    prefix = '/api/user'

    app.router.add_post(prefix + '/', create_user)
    app.router.add_get(prefix + '/', get_user_info)
    app.router.add_get(prefix + 's/', get_all_users)
    app.router.add_get('/api/battles/', get_battles)


async def create_user(request: Request) -> Response:
    """
    Создает игрока.
    """
    data = await request.json()
    logger.debug(data)
    user_exists = await User.check_user_exists(data['name'])
    schema = {'name': {'required': True, 'type': 'string'}}
    if not await validate(data, schema):
        logger.debug('invalid_name')
        return json_error_400('invalid_name')
    if user_exists:
        logger.debug('user_exists')
        return json_error_400('user_exists')

    user = await User.create_user(data)
    new_user_id = await User.get_user_by_name(data['name'])
    return json_response({'created': user, 'id': new_user_id['id']})


async def get_all_users(request: Request) -> Response:
    """
    Возвращает список всех игрогов.
    """
    users = await User.get_all_users()
    return json_response(users)


async def get_user_info(request: Request) -> Response:
    """
    Возвращает информацию о игроке.
    """
    player_id = request.query.get('id')
    if player_id:
        user = await User.get_user_by_id(player_id)
        return json_response(user)
    logger.debug('user_not_found')
    return json_error_400('user_not_found')


async def get_battles(request: Request) -> Response:
    battles = await Battle.get_battles()
    return json_response(battles)
