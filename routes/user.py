from aiohttp.web import json_response
from aiohttp.web_request import Request

from helpers.response import json_error_400
from helpers.validator import validate
from models.user import User


def init(app):
    prefix = '/api/user'

    app.router.add_post(prefix + '/', create_user)
    app.router.add_get(prefix + '/', get_user_info)
    app.router.add_get(prefix + 's/', get_all_users)


async def create_user(request: Request):
    data = await request.json()
    user_exists = await User.check_user_exists(data['name'])
    schema = {'name': {'required': True, 'type': 'string'}}
    if not await validate(data, schema):
        return json_error_400('invalid_name')
    if not user_exists:
        user = await User.create_user(data)
        return json_response({'created': user})

    return json_error_400('user_exists')


async def get_all_users(request: Request):
    users = await User.get_all_users()
    return json_response(users)


async def get_user_info(request: Request):
    player_id = request.query.get('id')
    if player_id:
        user = await User.get_user_by_id(player_id)
        return json_response(user)
    return json_error_400('user_not_found')
