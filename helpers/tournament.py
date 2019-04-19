import asyncio
import pickle
import random
from datetime import datetime, timedelta

from config import config
from models.user import User

END_TIME_KEY = 'end_time'
TOURNAMENT_TIME = 2 * 60
GROUP_LIMIT = 50
UNDER_ATTACK_TAG = '-attacked'
ATTACK_TIMEOUT_TAG = '-attack_timeout'
ATTACK_TIMEOUT = 5
TOURNAMENT_REWARDS = [300, 200, 100]


async def get_opponent_for_player(player_id: str) -> str:
    available_opponents_obj = await config['redis'].get(player_id)
    available_opponents = pickle.loads(available_opponents_obj)
    opponent_id = random.sample(available_opponents, 1)[0]
    return opponent_id


def fight(from_player_id: str, to_player_id: str) -> dict:
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
    while True:
        await asyncio.sleep(0.1)
        if bool(await config['redis'].get(END_TIME_KEY)):
            continue
        groups = await get_user_groups()
        for group in groups:
            for i, reward in enumerate(TOURNAMENT_REWARDS, 0):
                await User.add_num_to_field(group[i]['id'], 'money', reward)
        return


async def get_user_groups() -> list:
    groups = list()
    groups_count = await User.get_groups_count()
    for i in range(groups_count + 1):
        groups.append(await User.get_users_by_group(i))
    return groups


class UserUnderAttack:
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
    await config['redis'].set(player_id + ATTACK_TIMEOUT_TAG, 1, expire=ATTACK_TIMEOUT)


async def start_tournament_timer():
    await config['redis'].set(
        END_TIME_KEY,
        pickle.dumps(datetime.utcnow() + timedelta(seconds=TOURNAMENT_TIME)),
        expire=TOURNAMENT_TIME,
    )
    asyncio.ensure_future(tournament_watcher())


async def is_tournament_start():
    start_value = await config['redis'].get(END_TIME_KEY)
    return bool(start_value)
