from models.user import User

TEST_USERNAME = 'test_user'


async def test_create_user(cli):
    resp = await cli.post('/api/user/', json={'name': TEST_USERNAME})
    assert resp.status != 500
    user = await User.get_user_by_name(TEST_USERNAME)
    assert user['name'] == TEST_USERNAME


async def test_get_user_info(cli):
    user = await User.get_user_by_name(TEST_USERNAME)
    resp = await cli.get('/api/user/', params={'id': user['id']})
    assert resp.status == 200
    json_data = await resp.json()
    assert json_data['name'] == TEST_USERNAME


async def test_get_users(cli):
    resp = cli.get('/api/users/')
    assert resp.status == 200
    resp_json = await resp.json()
    assert isinstance(resp_json, list)
