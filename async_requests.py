import datetime
from typing import Coroutine

import asyncio
import aiohttp

from models import Session, init_orm, SwapiPeople
from more_itertools import chunked

MAX_CHUNK = 10
BUFFER = dict()
HEADERS = {
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)\
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.167 YaBrowser/22.7.3.799 Yowser/2.5 Safari/537.36"
    }

async def get_extra_items_by_list(session, people_json: dict, params: tuple, headers: dict=HEADERS) -> None:
    items = list()

    for item in people_json[params[0]]:
        if item in BUFFER:
            items.append(BUFFER[item])

        else:
            async with session.get(item, headers=headers) as response:
                json_data: dict = await response.json()

                items.append(json_data[params[1]])
                BUFFER[item] = items[-1]
    
    people_json[params[0]] = ', '.join(items)

async def get_extra_items_by_string(session, people_json: dict, params: tuple, headers: dict=HEADERS) -> None:
    item = people_json[params[0]]

    if item in BUFFER:
        people_json[params[0]] = BUFFER[item]

    else:
        async with session.get(item, headers=headers) as response:
            json_data: dict = await response.json()

            people_json[params[0]] = json_data[params[1]]
            BUFFER[item] = json_data[params[1]]
    
async def get_people(session, person_id: int) -> Coroutine:
    async with session.get(f'https://swapi.py4e.com/api/people/{person_id}/') as response:
        json_data: dict = await response.json()

        if 'detail' not in json_data:
            json_data.pop('created')
            json_data.pop('edited')
            json_data.pop('url')

            films_coroutines = list()
            homeworld_coroutines = list()
            species_coroutines = list()
            starships_coroutines = list()
            vehicles_coroutines = list()

            films_coroutines.append(get_extra_items_by_list(session, json_data, ('films', 'title')))

            homeworld_coroutines.append(get_extra_items_by_string(session, json_data, ('homeworld', 'name')))

            species_coroutines.append(get_extra_items_by_list(session, json_data, ('species', 'name')))

            starships_coroutines.append(get_extra_items_by_list(session, json_data, ('starships', 'name')))

            vehicles_coroutines.append(get_extra_items_by_list(session, json_data, ('vehicles', 'name')))

            coroutines = films_coroutines + species_coroutines + starships_coroutines + vehicles_coroutines + homeworld_coroutines
            await asyncio.gather(*coroutines)

            return json_data

async def insert_people(list_people_json: list) -> None:
    orm_objects = [SwapiPeople(**people_json) for people_json in list_people_json if people_json is not None]

    async with Session() as session:
        session.add_all(orm_objects)
        await session.commit()

async def main() -> None:
    await init_orm()
    
    async with aiohttp.ClientSession() as session:
        chunked_people_ids = chunked(range (1, 101), MAX_CHUNK)

        for people_ids in chunked_people_ids:
            people_coroutines = [get_people(session, people_id) for people_id in people_ids]

            list_people_json = await asyncio.gather(*people_coroutines)

            asyncio.create_task(insert_people(list_people_json))

        main_task = asyncio.current_task()
        currents_tasks = asyncio.all_tasks()
        currents_tasks.remove(main_task)
        await asyncio.gather(*currents_tasks)

if __name__ == '__main__':
    start = datetime.datetime.now()
    asyncio.run(main())
    print(f'Время выполнения кода: {datetime.datetime.now() - start}')
