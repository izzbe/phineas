import os

dsn = (f'postgresql://'
       f'{os.environ["POSTGRES_USER"]}'
       f':'
       f'{os.environ["POSTGRES_PASSWORD"]}'
       f'@localhost:5432/'
       f'{os.environ["POSTGRES_DB"]}')