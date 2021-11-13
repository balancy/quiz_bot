from environs import Env

from redis import Redis


if __name__ == '__main__':
    env = Env()
    env.read_env()

    redis_endpoint = env.str('REDIS_ENDPOINT')
    redis_port = env.str('REDIS_PORT')
    redis_password = env.str('REDIS_PASSWORD')

    db = Redis(
        host=redis_endpoint,
        port=redis_port,
        password=redis_password,
    )

    db.flushdb()
    print(f'Number of DB records is {len(db.keys())}')
