# %load ipython_start.py
# %load_ext autoreload
import wx
import badidatetime
badidatetime.set_local_coordinates(35.388093, -78.8624963)
from src.custom_widgits import (BadiDatePickerCtrl, ColorCheckBox,
                                FlatArrowButton)
from src.bahai_database import Database
from src.config import (TomlMetaData, TomlPanelConfig, TomlAppConfig,
                        TomlCreatePanel)
from src.ledger_transaction import LedgerTransaction

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
await db.cache.load()
