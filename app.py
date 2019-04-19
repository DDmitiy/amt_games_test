import logging
import os

from aiohttp import web
from aiohttp_session import setup

from config import config, setup_config
from config.connect_redis import redis_connect
from config.db import close_pg, init_pg
from routes import apply_routes


async def dispose_redis_pool(app):
    redis_pool.close()
    await redis_pool.wait_closed()


app = web.Application()

# Add config to app
setup_config(app)

# Add templates render

if bool(os.getenv('DEBUG', False)) is True:
    logging.getLogger().setLevel(logging.INFO)
    logging.debug("Logging started")

# Redis connect
storage, redis_pool = redis_connect(app)
setup(app, storage)
config['redis'] = redis_pool

# Add routes
apply_routes(app)

app.on_startup.append(init_pg)
app.on_cleanup.append(close_pg)
app.on_cleanup.append(dispose_redis_pool)


if __name__ == '__main__':
    web.run_app(app, host=os.getenv('HOST', '0.0.0.0'), port=os.getenv('PORT', '8080'))
