import datetime
from pprint import pprint
from typing import Coroutine

import asyncio
import aiohttp

from models import Session, init_orm, SwapiPeople
from more_itertools import chunked

MAX_CHUNK = 10

async def get_people(session, person_id: int) -> Coroutine:
    async with session.get(f'https://swapi.py4e.com/api/people/{person_id}/') as response:
        json_data: dict = await response.json()

        if 'detail' not in json_data:
            json_data.pop('created')
            json_data.pop('edited')
            json_data.pop('url')

            return json_data
    
async def get_extra_items(session, people_json: dict, params: tuple) -> None:
    items = list()

    for item in people_json[params[0]]:
        async with session.get(item) as response:
            json_data: dict = await response.json()

            items.append(json_data[params[1]])
    
    people_json[params[0]] = ', '.join(items)

async def insert_people(list_people_json: list) -> None:
    orm_objects = [SwapiPeople(**people_json) for people_json in list_people_json]

    async with Session() as session:
        session.add_all(orm_objects)
        await session.commit()

async def main() -> None:
    await init_orm()
    
    async with aiohttp.ClientSession() as session:
        chunked_people_ids = chunked(range (1, 51), MAX_CHUNK)

        for people_ids in chunked_people_ids:
            people_coroutines = [get_people(session, people_id) for people_id in people_ids]

            list_people_json = await asyncio.gather(*people_coroutines)

            films_coroutines = list()
            species_coroutines = list()
            starships_coroutines = list()
            vehicles_coroutines = list()

            for people_json in list_people_json:
                if people_json is None:
                    list_people_json.remove(people_json)
                    continue
                
                films_coroutines.append(get_extra_items(session, people_json, ('films', 'title')))

                species_coroutines.append(get_extra_items(session, people_json, ('species', 'name')))

                starships_coroutines.append(get_extra_items(session, people_json, ('starships', 'name')))

                vehicles_coroutines.append(get_extra_items(session, people_json, ('vehicles', 'name')))

            coroutines = films_coroutines + species_coroutines + starships_coroutines + vehicles_coroutines
            await asyncio.gather(*coroutines)

            asyncio.create_task(insert_people(list_people_json))

        main_task = asyncio.current_task()
        currents_tasks = asyncio.all_tasks()
        currents_tasks.remove(main_task)
        await asyncio.gather(*currents_tasks)

if __name__ == '__main__':
    start = datetime.datetime.now()
    asyncio.run(main())
    print(datetime.datetime.now() - start)
