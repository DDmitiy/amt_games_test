import math
import pickle
from itertools import islice

from aiohttp.web_request import Request
from aiohttp.web_response import Response, json_response
from aiologger.loggers.json import JsonLogger

from config import config
from config.config import GROUP_LIMIT
from helpers.response import json_error_400
from helpers.tournament import UserUnderAttack, fight, get_opponent_for_player, get_user_groups, is_tournament_start, \
    set_user_attack_timeout, start_tournament_timer, tournament_running_check, validate_attack
from models.battle import Battle
from models.user import User

logger = JsonLogger.with_default_handlers()


def init(app):
    prefix = '/api/tournament'

    app.router.add_post(prefix + '/', start_tournament)
    app.router.add_get(prefix + '/', tournament_status)
    app.router.add_get(prefix + '/opponent/', get_opponent)
    app.router.add_post(prefix + '/opponent/', attack)
    app.router.add_get(prefix + '/results/', get_last_tournament_results)


async def start_tournament(request: Request) -> Response:
    if await is_tournament_start():
        return json_error_400('tournament_already_running')
    users = await User.get_all_users_order_by('power')
    users_count = len(users)
    groups = list()
    group_num = math.ceil(len(users) / GROUP_LIMIT)
    for group_i in range(group_num):
        groups.append(list(islice(
            users, group_i * GROUP_LIMIT, min((group_i + 1) * GROUP_LIMIT, users_count),
        )))
        group_user_ids = [user['id'] for user in groups[group_i]]
        await User.set_users_group_by_id(group_user_ids, group_i)
        for user in groups[group_i]:
            opponents = set(group_user_ids)
            opponents.remove(user['id'])
            await config['redis'].set(user['id'], pickle.dumps(opponents))

    await start_tournament_timer()

    return json_response({
        'tournament_start': True,
        'group_num': group_num,
        'users_count': users_count,
        'groups': groups,
    })


@tournament_running_check
async def tournament_status(request: Request) -> Response:
    """
    Возвращает все турнирные группы или указанную по id.

    Query params: Optional id -- group id
    """
    group_id = request.query.get('id')
    if group_id:
        response = {
            'group': await User.get_users_by_group(int(group_id))
        }
    else:
        groups = await get_user_groups()
        response = {
            'groups': groups
        }
    return json_response(response)


@tournament_running_check
async def get_opponent(request: Request) -> Response:
    """
    Возвращает id оппонента для игрока.
    """
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


@tournament_running_check
async def attack(request: Request) -> Response:
    """
    Производит атаку на игрока другим игроком.
    """
    data = await request.json()
    from_player_id = data['from_player_id']
    to_player_id = data['to_player_id']

    available_opponents: set = pickle.loads(await config['redis'].get(from_player_id))

    valid, error = await validate_attack(from_player_id, to_player_id, available_opponents)
    if not valid:
        return json_error_400(error)

    await set_user_attack_timeout(from_player_id)

    attack_context = UserUnderAttack(to_player_id)
    if await attack_context.check_under:
        return json_error_400('player_under_attack')

    async with attack_context as _:
        battle = await fight(from_player_id, to_player_id)
        available_opponents.remove(to_player_id)
        await config['redis'].set(
            from_player_id,
            pickle.dumps(available_opponents)
        )
        await Battle.create(battle)

    return json_response(battle)


async def get_last_tournament_results(request: Request) -> Response:
    """
    Возвращает результаты последнего турнира.
    """
    if await is_tournament_start():
        return json_error_400('tournament_is_running')
    users = await User.get_last_prize_winners_of_group()
    return json_response(users)
