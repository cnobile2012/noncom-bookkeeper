# %load ipython_start.py
# %load_ext autoreload
from src.bahai_database import Database
from src.config import (TomlMetaData, TomlPanelConfig, TomlAppConfig,
                        TomlCreatePanel)

db = Database()
tmd = TomlMetaData()
tpc = TomlPanelConfig()
tac = TomlAppConfig()
tcp = TomlCreatePanel()

async def start():
    db.debug = True
    db.create_dirs()
    await db.create_db()

await start()


org_data = {'longitude': 0.0, 'location_city_name': '', 'latitude': 0.0,
            'locality_prefix': 0, 'start_of_fiscal_year': '',
            'locale_name': '', 'treasurer': '', 'total_membership': 0,
            'iana_name': ''}
await db._cache.load(183, org_data)
