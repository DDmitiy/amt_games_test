from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from config import config

Base = declarative_base()


class Battle(Base):
    __tablename__ = 'battles'
    id = Column(Integer, primary_key=True, nullable=False)
    from_player_id = Column(String, ForeignKey('users.id'))
    to_player_id = Column(String, ForeignKey('users.id'))
    medals = Column(Integer, nullable=False)
    win = Column(Boolean, nullable=False)

    @staticmethod
    async def create(data: dict) -> bool:
        async with config['db'].acquire() as conn:
            query = sa_battle.insert().values(data)
            await conn.execute(query)
        return True


sa_battle = Battle.__table__
