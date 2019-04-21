import asyncio
import functools
import pickle
import random
from datetime import datetime, timedelta
from typing import Optional, Tuple

from config import config
from config.config import ATTACK_TIMEOUT, ATTACK_TIMEOUT_TAG, END_TIME_KEY, TOURNAMENT_REWARDS, TOURNAMENT_TIME, \
    UNDER_ATTACK_TAG
from helpers.response import json_error_400
from helpers.validator import ATTACK_SCHEMA, validate
from models.user import User


async def get_opponent_for_player(player_id: str) -> Optional[str]:
    """
    Возвращает валидного оппонента для игрока.
    """
    available_opponents_obj = await config['redis'].get(player_id)
    available_opponents = pickle.loads(available_opponents_obj)
    if available_opponents:
        opponent_id = random.sample(available_opponents, 1)[0]
        return opponent_id
    else:
        return None


async def fight(from_player_id: str, to_player_id: str) -> dict:
    """
    Фукция, имитирующая логику боя.
    """
    medals = random.randint(-10, 10)
    await User.add_num_to_field(from_player_id, 'medals', medals)
    await User.add_num_to_field(to_player_id, 'medals', -medals)

    battle = {
        'from_player_id': from_player_id,
        'to_player_id': to_player_id,
        'medals': medals,
        'win': medals > 0,
    }
    return battle


async def tournament_watcher():
    """
    Следит за переменной в редисе и когда она пропадет, закроет турнир и раздаст награды.
    """
    while True:
        await asyncio.sleep(0.1)
        if bool(await config['redis'].get(END_TIME_KEY)):
            continue
        users = await User.get_last_prize_winners_of_group()
        for user in users:
            await User.add_num_to_field(user['id'], 'money', TOURNAMENT_REWARDS.get(user['rank']))
        return


async def get_user_groups() -> list:
    """
    Возвращает турнирные группы игроков.
    """
    groups = list()
    groups_count = await User.get_groups_count()
    for i in range(groups_count + 1):
        groups.append(await User.get_users_by_group(i))
    return groups


class UserUnderAttack:
    """
    Контекстный менеджер, не дающий одновременно напасть 2-ум и более игрокам на одного и того же.
    """
    def __init__(self, player_id):
        self.player_id = player_id

    async def __aenter__(self):
        await config['redis'].set(self.player_id + UNDER_ATTACK_TAG, 1)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await config['redis'].delete(self.player_id + UNDER_ATTACK_TAG)

    @property
    async def check_under(self) -> bool:
        return bool(await config['redis'].get(self.player_id + UNDER_ATTACK_TAG))


async def set_user_attack_timeout(player_id: str):
    """
    Создает переменную, по которой определяется тайм-аут нападений.

    :param player_id: id игрока.
    """
    await config['redis'].set(player_id + ATTACK_TIMEOUT_TAG, 1, expire=ATTACK_TIMEOUT)


async def start_tournament_timer():
    """
    Создает переменную, по которой определяется, запущен ли турнир и запускает вотчер за ней.
    """
    await config['redis'].set(
        END_TIME_KEY,
        pickle.dumps(datetime.utcnow() + timedelta(seconds=TOURNAMENT_TIME)),
        expire=TOURNAMENT_TIME,
    )
    asyncio.ensure_future(tournament_watcher())


async def is_tournament_start():
    """
    Проверка, идет ли сейчас турнир.
    """
    start_value = await config['redis'].get(END_TIME_KEY)
    return bool(start_value)


def tournament_running_check(func):
    """
    Декоратор для endpoint'ов, который проверяет, идет ли сейчас турнир.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if not await is_tournament_start():
            return json_error_400('tournament_not_started')
        return await func(*args, **kwargs)
    return wrapper


async def validate_attack(from_player_id: str, to_player_id: str, available_opponents: set) \
        -> Tuple[bool, Optional[str]]:
    """
    Валидирует, можно ли нападать.
    """
    data = {
        'from_player_id': from_player_id,
        'to_player_id': to_player_id,
    }
    if not await validate(data, ATTACK_SCHEMA):
        return False, 'invalid_player_id'

    attack_timeout = await config['redis'].get(from_player_id + ATTACK_TIMEOUT_TAG)

    if attack_timeout:
        return False, 'attack_timeout'

    if to_player_id not in available_opponents:
        return False, 'invalid_opponent'

    return True, None
