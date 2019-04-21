import pytest

from app import app
from routes.tournament import attack, get_opponent, start_tournament, tournament_status
from routes.user import create_user, get_all_users, get_user_info


@pytest.fixture()
def cli(loop, aiohttp_client):
    prefix = '/api/user'

    app.router.add_post(prefix + '/', create_user)
    app.router.add_get(prefix + '/', get_user_info)
    app.router.add_get(prefix + 's/', get_all_users)

    prefix = '/api/tournament'

    app.router.add_post(prefix + '/', start_tournament)
    app.router.add_get(prefix + '/', tournament_status)
    app.router.add_get(prefix + '/opponent/', get_opponent)
    app.router.add_post(prefix + '/opponent/', attack)

    return loop.run_until_complete(aiohttp_client(app))
