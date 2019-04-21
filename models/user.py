import random
from typing import Optional
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base

from config import config
from config.config import TOURNAMENT_REWARDS

Base = declarative_base()


def get_random_power():
    return random.randint(1, 1000)


def gen_uuid4():
    return str(uuid4())


class User(Base):
    """
    Модель игрока.
    """
    __tablename__ = 'users'
    id = Column(String, primary_key=True, nullable=False, default=gen_uuid4)
    name = Column(String, nullable=True, unique=True)
    power = Column(Integer, default=get_random_power, nullable=False)
    medals = Column(Integer, default=1000, nullable=False)
    money = Column(Integer, default=0, nullable=False)
    group_num = Column(Integer)

    @staticmethod
    async def get_user_by_id(user_id: str) -> dict:
        async with config['db'].acquire() as conn:
            query = sa.select([sa_user.c.id,
                               sa_user.c.name,
                               sa_user.c.power,
                               sa_user.c.medals,
                               sa_user.c.money,
                               sa_user.c.group_num
                               ]) \
                .select_from(sa_user) \
                .where(sa_user.c.id == user_id)
            users = list(map(lambda x: dict(x), await conn.execute(query)))
            return users[0] if len(users) == 1 else None

    @staticmethod
    async def create_user(data: dict) -> bool:
        async with config['db'].acquire() as conn:
            query = sa_user.insert().values(data)
            await conn.execute(query)
        return True

    @classmethod
    async def get_all_users(cls) -> list:
        async with config['db'].acquire() as conn:
            query = sa.select([sa_user.c.id,
                               sa_user.c.name,
                               sa_user.c.power,
                               sa_user.c.medals,
                               sa_user.c.money,
                               sa_user.c.group_num
                               ]) \
                .select_from(sa_user)
            return list(map(lambda x: dict(x), await conn.execute(query)))

    @classmethod
    async def get_all_users_ids(cls) -> list:
        async with config['db'].acquire() as conn:
            query = sa.select([sa_user.c.id,
                               ]) \
                .select_from(sa_user)
            return [i[0] for i in list(await conn.execute(query))]

    @classmethod
    async def get_all_users_order_by(cls, order_by: str) -> list:
        order_by_fields = {
            'power': sa_user.c.power,
            'medals': sa_user.c.medals,
        }
        async with config['db'].acquire() as conn:
            query = sa.select([sa_user.c.id,
                               sa_user.c.name,
                               sa_user.c.power,
                               sa_user.c.medals,
                               sa_user.c.money,
                               sa_user.c.group_num
                               ]) \
                .select_from(sa_user) \
                .order_by(order_by_fields.get(order_by).desc())
            return list(map(lambda x: dict(x), await conn.execute(query)))

    @classmethod
    async def get_users_by_id_list(cls, ids: list) -> list:
        async with config['db'].acquire() as conn:
            query = sa.select([sa_user.c.id,
                               sa_user.c.name,
                               sa_user.c.power,
                               sa_user.c.medals,
                               sa_user.c.money,
                               sa_user.c.group_num
                               ]) \
                .select_from(sa_user) \
                .where(sa_user.c.id.in_(ids))
            return list(map(lambda x: dict(x), await conn.execute(query)))

    @staticmethod
    async def check_user_exists(name: str) -> bool:
        user = await User.get_user_by_name(name)
        return bool(user)

    @staticmethod
    async def get_user_by_name(name: str) -> Optional[dict]:
        async with config['db'].acquire() as conn:
            query = sa.select([sa_user.c.id,
                               sa_user.c.name]) \
                .select_from(sa_user) \
                .where(sa_user.c.name == name)

            user = list(map(lambda x: dict(x), await conn.execute(query)))
        return user[0] if user else None

    @staticmethod
    async def set_users_group_by_id(users_ids: list, group_num: int):
        async with config['db'].acquire() as conn:
            query = sa_user.update().values({'group_num': group_num})\
                .where(sa_user.c.id.in_(users_ids))
            await conn.execute(query)

    @staticmethod
    async def get_groups_count() -> int:
        async with config['db'].acquire() as conn:
            query = text("""
                SELECT MAX(group_num)
                FROM users;
            """)
            groups_num = list(map(lambda x: dict(x), await conn.execute(query)))
        return groups_num[0]['max']

    @staticmethod
    async def get_users_by_group(id: int) -> list:
        async with config['db'].acquire() as conn:
            query = sa.select([sa_user.c.id,
                               sa_user.c.name,
                               sa_user.c.power,
                               sa_user.c.medals,
                               sa_user.c.money,
                               sa_user.c.group_num
                               ]) \
                .select_from(sa_user) \
                .where(sa_user.c.group_num == id) \
                .order_by(sa_user.c.medals.desc())
            return list(map(lambda x: dict(x), await conn.execute(query)))

    @staticmethod
    async def add_num_to_field(user_id: str, field: str, num: int):
        async with config['db'].acquire() as conn:
            query = text("""
                UPDATE users
                SET {field} = {field} + {num}
                WHERE id = '{user_id}'           
            """.format(
                user_id=user_id,
                num=num,
                field=field
            ))
            await conn.execute(query)

    @staticmethod
    async def get_last_prize_winners_of_group() -> list:
        async with config['db'].acquire() as conn:
            query = text("""
                SELECT id, name, money, medals, group_num, rank
                FROM (
                    SELECT id, name, money, medals, group_num, ROW_NUMBER()
                        OVER (PARTITION BY group_num ORDER BY medals DESC, name) AS rank
                    FROM users
                ) rs WHERE rank <= {rewards_num}
            """.format(rewards_num=len(TOURNAMENT_REWARDS)))
            prize_winners = list(map(lambda x: dict(x), await conn.execute(query)))
        return prize_winners


sa_user = User.__table__
