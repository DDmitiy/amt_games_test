import pathlib

config = dict()

config['root_path'] = str(pathlib.Path(__file__).parent.parent)
config['db'] = None
config['redis'] = None
