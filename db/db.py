from configparser import ConfigParser
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker



config = ConfigParser()
config.read("config.ini")

engine = create_async_engine(
    "{}+{}://{}:{}@{}/{}".format(
        config['DataBase']['dialect'],
        config['DataBase']['driver'],
        config['DataBase']['username'],
        config['DataBase']['password'],
        config['DataBase']['host'],
        config['DataBase']['database']
    )
)

async_session = sessionmaker(
      engine,
      expire_on_commit=False,
      class_=AsyncSession
    )

async def get_session():
       async with async_session() as session:
           yield session

