from configparser import ConfigParser


class ConfigError(Exception):
    pass


config_file = './config.ini'

config = ConfigParser()
config.read(config_file)

debug_config = {
    'debug': True,
    'log_level': 'DEBUG'
}
if 'Debug' in config:
    if 'debug' in config['Debug']:
        debug_config['debug'] = config['Debug']['debug'] == 'true'
    if 'log_level' in config['Debug']:
        debug_config['log_level'] = config['Debug']['log_level']

if 'Database' not in config:
    raise ConfigError('Не заданы параметры базы данных')
if 'host' not in config['Database']:
    raise ConfigError('Не задан хост базы данных')
if 'port' not in config['Database']:
    raise ConfigError('Не задан порт базы данных')
if 'user' not in config['Database']:
    raise ConfigError('Не задан пользователь базы данных')
if 'password' not in config['Database']:
    raise ConfigError('Не задан пароль базы данных')
if 'name' not in config['Database']:
    raise ConfigError('Не задано имя базы данных')
database_config = {
    'host': config['Database']['host'],
    'port': config['Database']['port'],
    'user': config['Database']['user'],
    'password': config['Database']['password'] if config['Database']['password'] else None,
    'name': config['Database']['name']
}

if 'Redis' not in config:
    raise ConfigError("Не заданы параметры подключения к Redis")
if 'host' not in config['Redis']:
    raise ConfigError("Не задан хост Redis")
if 'port' not in config['Redis']:
    raise ConfigError("Не задан порт Redis")
redis_config = {
    'host': config['Redis']['host'],
    'port': int(config['Redis']['port']),
}

if 'Bot' not in config:
    raise ConfigError('Не заданы параметры бота')
if 'token' not in config['Bot']:
    raise ConfigError('Не задан API TOKEN')
bot_config = {
    'token': config['Bot']['token'],
}

if 'Localization' not in config:
    raise ConfigError('Не заданы параметры локализации')
if 'lang' not in config['Localization'] or config['Localization']['lang'] not in ['ru', 'en']:
    raise ConfigError('Не задан язык')
localization_config = {
    'lang': config['Localization']['lang'],
}

if 'Secret' not in config:
    raise ConfigError('Не заданы секретные параметры')
if 'django_secret' not in config['Secret']:
    raise ConfigError('Не задан секрет Django')
secret_config = {
    'django_secret': config['Secret']['django_secret'],
}

if 'Extra' not in config:
    raise ConfigError('Не заданы особые параметры')
if 'allowed_hosts' not in config['Extra']:
    raise ConfigError('Не заданы доступные хосты')
if 'static_root' not in config['Extra']:
    raise ConfigError('Не заданы корневой каталог статических файлов')
extra_config = {
    'allowed_hosts': config['Extra']['allowed_hosts'].split(" ") if len(config['Extra']['allowed_hosts']) > 0 else [],
    'static_root': config['Extra']['static_root']
}
