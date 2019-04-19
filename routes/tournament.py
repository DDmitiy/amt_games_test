import math
import pickle
from itertools import islice

from aiohttp.web_request import Request
from aiohttp.web_response import Response, json_response

from config import config
from helpers.response import json_error_400
from helpers.tournament import ATTACK_TIMEOUT_TAG, GROUP_LIMIT, UserUnderAttack, fight, get_opponent_for_player, \
    get_user_groups, is_tournament_start, set_user_attack_timeout, start_tournament_timer
from helpers.validator import ATTACK_SCHEMA, validate
from models.battle import Battle
from models.user import User


def init(app):
    prefix = '/api/tournament'

    app.router.add_post(prefix + '/', start_tournament)
    app.router.add_get(prefix + '/', tournament_status)
    app.router.add_get(prefix + '/opponent/', get_opponent)
    app.router.add_post(prefix + '/opponent/', attack)


async def start_tournament(request: Request) -> Response:
    users_ids = await User.get_all_users_ids()
    for user in users_ids:
        opponents = set(users_ids)
        opponents.remove(user)
        await config['redis'].set(user, pickle.dumps(opponents))

    await start_tournament_timer()

    users = await User.get_all_users_order_by('power')
    users_count = len(users)
    groups = list()
    group_num = math.ceil(len(users) / GROUP_LIMIT)
    for group_i in range(group_num):
        groups.append(list(islice(
            users, group_i * GROUP_LIMIT, min((group_i + 1) * GROUP_LIMIT, users_count),
        )))
        await User.set_users_group_by_id([user['id'] for user in users], group_i)

    return json_response({
        'tournament_start': True,
        'group_num': group_num,
        'users_count': users_count,
        'groups': groups,
    })


async def tournament_status(request: Request) -> Response:
    response = dict()
    group_id = request.query.get('id')
    if group_id:
        response.update({
            'group': await User.get_users_by_group(int(group_id))
        })
    else:
        groups = await get_user_groups()
        response.update({
            'groups': groups
        })
    response.update({
        'tournament_start': await is_tournament_start(),
    })
    return json_response(response)


async def get_opponent(request: Request) -> Response:
    player_id = request.query.get('player_id')
    if not player_id:
        return json_error_400('id_required')
    user = await User.get_user_by_id(player_id)
    if not user:
        return json_error_400('invalid_id')
    opponent_id = await get_opponent_for_player(user['id'])
    return json_response({
        'opponent_id': opponent_id,
    })


async def attack(request: Request) -> Response:
    if not is_tournament_start():
        return json_error_400('tournament_ended')

    data = await request.json()
    from_player_id = data['from_player_id']
    to_player_id = data['to_player_id']

    if not await validate(data, ATTACK_SCHEMA):
        return json_error_400('invalid_player_id')

    attack_timeout = await config['redis'].get(from_player_id + ATTACK_TIMEOUT_TAG)

    if attack_timeout:
        return json_error_400('attack_timeout')

    available_opponents: set = pickle.loads(await config['redis'].get(from_player_id))

    if to_player_id not in available_opponents:
        return json_error_400('invalid_opponent')

    await set_user_attack_timeout(from_player_id)

    attack_context = UserUnderAttack(to_player_id)
    if await attack_context.check_under:
        return json_error_400('player_under_attack')

    async with attack_context as _:
        battle = fight(from_player_id, to_player_id)
        available_opponents.remove(to_player_id)
        await config['redis'].set(
            from_player_id,
            pickle.dumps(available_opponents)
        )
        await Battle.create(battle)

    return json_response(battle)
