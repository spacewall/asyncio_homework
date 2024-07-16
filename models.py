import os

import dotenv
from sqlalchemy import String, Text
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs

CONFIGURATION = dotenv.dotenv_values('.env')

POSTGRES_PASSWORD = CONFIGURATION['POSTGRES_PASSWORD']
POSTGRES_USER = CONFIGURATION['POSTGRES_USER']
POSTGRES_DB = CONFIGURATION['POSTGRES_DB']
POSTGRES_HOST = os.getenv('POSTGRES_HOST', '127.0.0.1')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5431')

PG_DSN = f'postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

engine = create_async_engine(PG_DSN)
Session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase, AsyncAttrs):
    pass


class SwapiPeople(Base):
    __tablename__ = 'swapi_people'

    id: Mapped[int] = mapped_column(primary_key=True)
    birth_year: Mapped[str] = mapped_column(String(50), nullable=True)
    eye_color: Mapped[str] = mapped_column(String(50), nullable=True)
    films: Mapped[str] = mapped_column(Text, nullable=True)
    gender: Mapped[str] = mapped_column(String(20), nullable=True)
    hair_color: Mapped[str] = mapped_column(String(30), nullable=True)
    height: Mapped[str] = mapped_column(String(30), nullable=True)
    homeworld: Mapped[str] = mapped_column(String(80), nullable=True)
    mass: Mapped[str] = mapped_column(String(30), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    skin_color: Mapped[str] = mapped_column(String(50), nullable=True)
    species: Mapped[str] = mapped_column(Text, nullable=True)
    starships: Mapped[str] = mapped_column(Text, nullable=True)
    vehicles: Mapped[str] = mapped_column(Text, nullable=True)


async def init_orm():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
