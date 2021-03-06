from __future__ import with_statement

import os
import pathlib
import sys

sys.path.append(os.getcwd())
from sqlalchemy import engine_from_config, pool, MetaData, Table
from alembic import context
from logging.config import fileConfig
config = context.config
fileConfig(config.config_file_name)


def combine_metadata(*args):
    m = MetaData()
    for metadata_temp in args:
        for metadata in metadata_temp:
            for t in metadata.tables.values():
                t.tometadata(m)
    return m


meta_list = list()

for file in [file for file in os.listdir(str(pathlib.Path(__file__).parent.parent) + "/models/") if file != '__pycache__' and file != '__init__.py']:
    p, m = file.rsplit('.', 1)
    module_in_file = __import__("models." + str(p))
    files_module_in_directory = getattr(module_in_file, p)

    new_model = []
    for item in files_module_in_directory.__dict__:
        try:
            files_module = getattr(files_module_in_directory, item)
            if isinstance(files_module, Table) is True:
                meta_list.append(files_module.metadata)
        except Exception as e:
            print(e)

target_metadata = combine_metadata(meta_list)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = f"{os.getenv('POSTGRES_TYPE')}://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@" \
          f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"


    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = f"{os.getenv('POSTGRES_TYPE')}://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@" \
          f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

    config_dict = dict()
    config_dict['sqlalchemy.url'] = url

    connectable = engine_from_config(
        config_dict,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
