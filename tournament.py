import asyncio
import json
import random

import requests
from aiohttp import ClientSession

BASE_URL = 'http://localhost:8080/api/'
USERS_COUNT = 200
DELAY = 0.5


async def make_attack(user_id, opponent_id, session):
    async with session.post(
        BASE_URL + 'tournament/opponent/',
        json={
            'from_player_id': user_id,
            'to_player_id': opponent_id,
        }
    ) as response:
        i = json.loads(await response.read())
        return i


async def main():
    users_ids = set()
    for i in range(USERS_COUNT):
        resp = requests.post(BASE_URL + 'user/', json={'name': f'player-{i}'})
        users_ids.add(resp.json()['id'])
    print('users created')

    requests.post(BASE_URL + 'tournament/')
    print('tournament started')
    tournament_started = True
    while tournament_started:
        await asyncio.sleep(DELAY)
        attacks = list()
        async with ClientSession() as session:
            for i in range(15):
                user_id = random.sample(users_ids, 1)[0]
                resp = requests.get(
                    BASE_URL + 'tournament/opponent/',
                    params={'player_id': user_id}
                ).json()

                if resp.get('error') and resp['error'] == 'tournament_not_started':
                    tournament_started = False
                    break
                attack = asyncio.ensure_future(make_attack(user_id, resp['opponent_id'], session))
                attacks.append(attack)
            responses = await asyncio.gather(*attacks)

            for resp in responses:
                print(resp)
                if resp.get('error') and resp['error'] == 'tournament_not_started':
                    tournament_started = False
                    break

    await asyncio.sleep(DELAY)
    resp = requests.get(BASE_URL + 'tournament/results/').json()
    print(f"""
    ___________________________
    Tournament ended
           RESULTS
    Place | Group | Name  """)

    for user in resp:
        print(f"      {user['rank']}   |   {user['group_num']}   | {user['name']} | Medals: {user['medals']} | Money: {user['money']}")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(main())
    loop.run_until_complete(future)
