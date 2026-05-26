# %load ipython_start.py
# %load_ext autoreload
import asyncio
from src.bahai_database import Database

db = Database()

async def start():
    db.debug = True
    db.create_dirs()
    await db.create_db()

await start()
print(f"DB Path: {db.user_data_fullpath}")

org_data = {'longitude': 0.0, 'location_city_name': '', 'latitude': 0.0,
            'locality_prefix': 0, 'start_of_fiscal_year': '', 'locale_name': '',
            'treasurer': '', 'total_membership': 0, 'iana_name': ''}
await db._cache.load(183, org_data)
#print(db._cache._store)
