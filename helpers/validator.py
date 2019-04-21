from cerberus import Validator


async def validate(data, schema):
    """
    Обертка для валидотора.
    """
    v = Validator()

    if v.validate(data, schema) is False:
        print(v.errors)
        return False

    return True


ATTACK_SCHEMA = {
    'from_player_id': {'required': True, 'type': 'string'},
    'to_player_id': {'required': True, 'type': 'string'},
}