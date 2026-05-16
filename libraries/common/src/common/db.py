import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[4]

dsn = (f'postgresql://'
       f'{os.environ["POSTGRES_USER"]}'
       f':'
       f'{os.environ["POSTGRES_PASSWORD"]}'
       f'@localhost:5432/'
       f'{os.environ["POSTGRES_DB"]}')