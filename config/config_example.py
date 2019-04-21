import os
import pathlib

config = dict()

config['root_path'] = str(pathlib.Path(__file__).parent.parent)
config['db'] = None
config['redis'] = None

config['tournament_time'] = int(os.getenv('AMT_TOURNAMENT_TIME', 2 * 60))
config['group_limit'] = int(os.getenv('ANT_GROUP_LIMIT', 50))

END_TIME_KEY = 'end_time'
TOURNAMENT_TIME = config['tournament_time']
GROUP_LIMIT = config['group_limit']
UNDER_ATTACK_TAG = '-attacked'
ATTACK_TIMEOUT_TAG = '-attack_timeout'
ATTACK_TIMEOUT = 5
TOURNAMENT_REWARDS = {
    1: 300,
    2: 200,
    3: 100,
}