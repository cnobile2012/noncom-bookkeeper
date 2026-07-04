# -*- coding: utf-8 -*-
#
# src/base_database.py
#
__docformat__ = "restructuredtext en"

import os
import wx
import ast
import sqlite3
import aiosqlite

from .config import Settings
from .utilities import StoreObjects
from .populate_collect_panel import PopulateCollect
from .preperation import DataPreperation
from .cache import Cache


def adapt_tuple(value: tuple) -> str:
    """
    Adapt a tuple.
    """
    return repr(value)


def convert_tuple(value: bytes) -> tuple:
    """
    Converter: value → tuple
    """
    value = value.decode("utf-8")
    result = ast.literal_eval(value)

    if not isinstance(result, tuple):
        raise ValueError(f"Expected tuple, got {type(result).__name__}.")

    return result


sqlite3.register_adapter(tuple, adapt_tuple)
sqlite3.register_converter('TUPLE', convert_tuple)


class BaseDatabase(PopulateCollect, Settings):
    """
    This class provides the commonly used method for all basebase
    configurations.

    https://sqlite.org/
    https://www.w3schools.com/sql/
    https://docs.wxpython.org/
    """
    _T_FISCAL_YEAR = 'fiscal_year'
    _T_MONTH = 'month'
    _T_FIELD_TYPE = 'field_type'
    _T_DATA = 'config_data'
    _T_MONTHLY = 'monthly'
    _T_REPORT_PIVOT = 'report_pivot'
    _T_REPORT_TYPE = 'report_type'
    _T_LEDGER_DATA = 'ledget_data'
    _T_LEDGER_ENTRY_TYPE = 'ledger_entry_type'
    _T_LEDGER_DESC = 'ledger_desc'
    _T_LEDGER_BANK = 'ledger_bank'
    _T_LEDGER_INCOME = 'ledger_income'
    _T_LEDGER_EXPENSE_PIVOT = 'ledger_expense_pivot'
    _T_LEDGER_EXPENSE = 'ledger_expense'
    _SCHEMA_TABLES = {
        _T_FISCAL_YEAR: (
            'pk INTEGER NOT NULL PRIMARY KEY',  # fy1fk or fy2fk in data
            'year INTEGER UNIQUE NOT NULL',
            'month INTEGER NOT NULL',
            'day INTEGER NOT NULL',
            'current INTEGER NOT NULL',
            'work_on INTEGER NOT NULL',
            'audit INTEGER NOT NULL',
            'ctime DATETIME NOT NULL',
            'mtime DATETIME NOT NULL'),
        _T_MONTH: (
            'pk INTEGER NOT NULL PRIMARY KEY',  # mfk in data
            'month TEXT UNIQUE NOT NULL',
            'ord INTEGER UNIQUE NOT NULL',
            'ctime DATETIME NOT NULL'),
        _T_FIELD_TYPE: (
            'pk INTEGER NOT NULL PRIMARY KEY',  # ffk in data
            'field TEXT UNIQUE NOT NULL',
            'ctime DATETIME NOT NULL',
            'mtime DATETIME NOT NULL'),
        _T_DATA: (
            'pk INTEGER NOT NULL PRIMARY KEY',  # cfk in report_pivot
            'value TEXT NOT NULL',
            'fy1fk INTEGER NOT NULL',
            'fy2fk INTEGER NOT NULL',
            'mfk INTEGER NOT NULL',
            'ffk INTEGER NOT NULL',
            'ctime DATETIME NOT NULL',
            'mtime DATETIME NOT NULL'),
        _T_MONTHLY: (
            'pk INTEGER NOT NULL PRIMARY KEY',
            'fyfk INTEGER NOT NULL',
            'cal_year_month TUPLE',
            'participation INTEGER',
            'outstanding INTEGER',
            'coh INTEGER',
            'membership INTEGER',
            'treasurer TEXT NOT NULL',
            'locality INTEGER NOT NULL',
            'ctime DATETIME NOT NULL',
            'mtime DATETIME NOT NULL'),
        _T_REPORT_TYPE: (
            'pk INTEGER NOT NULL PRIMARY KEY',  # rfk in report_pivot
            'report TEXT UNIQUE NOT NULL',
            'ctime DATETIME NOT NULL',
            'mtime DATETIME NOT NULL'),
        _T_REPORT_PIVOT: (
            'rfk INTEGER NOT NULL',
            'cfk INTEGER NOT NULL',
            f'FOREIGN KEY (rfk) REFERENCES {_T_REPORT_TYPE} (pk)',
            f'FOREIGN KEY (cfk) REFERENCES {_T_DATA} (pk)'),
        _T_LEDGER_DATA: (
            'pk INTEGER NOT NULL PRIMARY KEY',
            'date DATETIME NOT NULL',
            'purged INTEGER default 0',
            'ctime DATETIME NOT NULL',
            'mtime DATETIME NOT NULL'),
        _T_LEDGER_DESC: (
            'pk INTEGER NOT NULL PRIMARY KEY',
            'type INTEGER NOT NULL',
            'other TEXT NULL'),
        _T_LEDGER_ENTRY_TYPE: (
            'pk INTEGER NOT NULL PRIMARY KEY',
            'ck_num INTEGER NULL',
            'rcpt_num INTEGER NULL',
            'value INTEGER'),
        _T_LEDGER_BANK: (
            'pk INTEGER NOT NULL PRIMARY KEY',
            'type INTEGER NOT NULL',
            'value INTEGER'),
        _T_LEDGER_INCOME: (
            'pk INTEGER NOT NULL PRIMARY KEY',
            'type INTEGER NOT NULL',
            'value INTEGER'),
        _T_LEDGER_EXPENSE_PIVOT: (
            'lfk INTEGER NOT NULL',
            'efk INTEGER NOT NULL',
            f'FOREIGN KEY (lfk) REFERENCES {_T_LEDGER_DATA} (pk)',
            f'FOREIGN KEY (efk) REFERENCES {_T_LEDGER_EXPENSE} (pk)'),
        _T_LEDGER_EXPENSE: (
            'pk INTEGER NOT NULL PRIMARY KEY',
            'ffk INTEGER NOT NULL',
            'type INTEGER NOT NULL',
            'expense INTEGER NOT NULL',
            f'FOREIGN KEY (ffk) REFERENCES {_T_FIELD_TYPE} (pk)'),
        }
    _SCHEMA_EXTRA = {
        }
    _SCHEMA_INDICES = (
        ('idx_month_month ON month(month);'),
        ('idx_month_ord ON month(ord);'),
        ('idx_fiscal_year_year ON fiscal_year(year);'),
        )
    _TABLES = list(_SCHEMA_TABLES.keys())
    _TABLES.sort()
    _INDICES = [name.split()[0] for name in _SCHEMA_INDICES]
    _INDICES.sort()
    _EXCLUDE_PANELS = ('fiscal', 'monthly')
    _MAX_FIELD_LEN = 50  # Max length of fields allowed in the field_table.
    _DETECT_TYPES = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dp = DataPreperation(self)
        self._mf = StoreObjects().get_object('MainFrame')
        self._cache = Cache(self)

    def set_local_coordinates(self, lat: float=None, lon: float=None) -> None:
        raise NotImplementedError(
            "The 'set_local_coordinates' must be implemented.")

    @property
    def cache(self):
        return self._cache

    #
    # Schema methods
    #

    async def create_db(self) -> None:
        """
        Create the database based on the fields currently defined.
        """
        if (not os.path.exists(self.user_data_fullpath) or
            not await self.has_schema):
            async with aiosqlite.connect(self.user_data_fullpath) as db:
                for table, params in self._SCHEMA_TABLES.items():
                    fields = ', '.join([field for field in params])
                    query = f"CREATE TABLE IF NOT EXISTS {table} ({fields});"

                    if self._SCHEMA_EXTRA:  # pragma: no cover
                        extra = self._SCHEMA_EXTRA.get(table)
                        query = query.rstrip(");")
                        query = f', {extra});'

                    self._log.info("Created table: %s", query)
                    await db.execute(query)
                    await db.commit()

                for index in self._SCHEMA_INDICES:
                    query = 'CREATE INDEX IF NOT EXISTS ' + index
                    self._log.info("Created index: %s", query)
                    await db.execute(query)
                    await db.commit()

                if self._SCHEMA_EXTRA:  # pragma: no cover
                    for view, params in self._SCHEMA_VIEWS.items():
                        fields = ', '.join([field for field in params])
                        query = f"CREATE VIEW IF NOT EXISTS {view} ({fields})"
                        extra = self._SCHEMA_EXTRA.get(view)
                        query += f' {extra};' if extra else ';'
                        self._log.info("Created view: %s", query)
                        await db.execute(query)
                        await db.commit()

    @property
    async def has_schema(self) -> bool:
        """
        Checks that the schema has been created.

        :returns: True if the schema has been created and False if it has not
                  been created.
        :rtype: bool
        """
        query = "SELECT type, name FROM sqlite_master;"
        data = await self._do_select_query(query)
        table_names = [name for type, name in data if type == 'table']
        table_names.sort()
        t_check = table_names == self._TABLES
        index_names = [name for type, name in data
                       if type == 'index' and not name.startswith('sqlite_')]
        index_names.sort()
        i_check = index_names == self._INDICES

        if not t_check:
            msg = ("Database table count is wrong it should be "
                   f"'{self._TABLES}' found '{table_names}'")
            self._log.error(msg)
            self._mf.statusbar_error = msg

        if not i_check:
            msg = ("Database index count is wrong it should be "
                   f"'{self._INDICES}' found '{index_names}'")
            self._log.error(msg)
            self._mf.statusbar_error = msg

        return t_check + i_check == 2

    #
    # Initialization methods
    #

    async def populate_panels(self) -> None:
        """
        Populate all panels that have data in the database.
        """
        fy = self.get_work_on_fiscal_year()
        year, month = (None, None) if fy is None else fy[1:3]

        if None not in (year, month):
            self._log.info("Populating all panels in %04d-%02d.", year, month)
            await self._populate_config_data_panels(year, self._mf.panels)
            await self._populate_month(fy)
            self._populate_fiscal()

    async def _populate_config_data_panels(self, year: int, panels: dict
                                           ) -> None:
        """
        Populate all panels that use the config data table.

        :param int year: The current fiscal year.
        :param dict panels: A dict of all non-excluded panels.
        """
        for panel_name, panel in panels.items():
            if panel_name not in self._EXCLUDE_PANELS:
                data = self.collect_panel_values(panel)
                items = self.cache.get(self._T_DATA, year=year,
                                       r_type=panel_name)
                # Add any new fields to the database.
                await self._add_fields_to_field_type_table(data)
                panel.initializing = True
                values = {item[1]: item[2] for item in items}
                self.populate_panel_values(panel_name, panel, values)
                panel.initializing = False

            if panel_name == 'organization':
                # Set the lat and lon for the badidatetime package is used.
                self.set_local_coordinates()

    async def _populate_month(self, fy: tuple) -> None:
        """
        Populate the currently chosen month with that month's data.

        :params tuple fy: The fiscal year being worked on.
        """
        fy_year = fy[1]
        today = self.today()
        date = (today.year, today.month)
        mon_idx = self.index_of_calendar_year(date, fy_year)
        panel = self._mf.panels.get('monthly')
        data = self.collect_panel_values(panel)
        values = ()  # Used when all monthly panels are empty.

        for item in self.cache.get(self._T_MONTHLY, year=fy_year):
            if item[2] == date and fy[0] == item[1]:
                values = item
                break

        data = self.populate_monthly_data(mon_idx, values, data)
        panel.initializing = True
        self.populate_panel_values('monthly', panel, data)
        panel.initializing = False

    def _populate_fiscal(self) -> None:
        """
        Populate the fiscal panel.
        """
        panel = self._mf.panels.get('fiscal')
        panel.initializing = True
        self.populate_panel_values('fiscal', panel, {})
        panel.initializing = False

    async def save_to_database(self, panel_name: str, panel: wx.Panel) -> None:
        """
        Save the given panel data to the database.

        :param str panel_name: The internal name of the current panel.
        :param wx.Panel panel: Any of the panels that have collected data.
        :returns: None if no errors, otherwise the error message.
        :rtype: None or str

        .. note::

           Empty (default) organization data:
              {'locality_prefix': 0, 'locale_name': '', 'total_membership': '',
               'treasurer': '', 'start_of_fiscal_year': '<today>',
               'location_city_name': ''}
        """
        error = None
        fy = self.get_work_on_fiscal_year()
        f_year, f_month = (None, None) if fy is None else fy[1:3]
        data = self.collect_panel_values(panel)

        if panel_name == 'organization':
            error = await self.dp.organization(data, f_year, f_month)
        elif panel_name == 'budget':
            if f_year and f_month:
                error = await self.dp.budget(data, f_year, f_month)
        elif panel_name == 'monthly':
            if data:
                error = await self.dp.monthly(data, f_year)
        elif panel_name == 'fiscal':
            data = await self.dp.fiscal(data, f_year, f_month)
            f_year = f_month = None
        elif panel_name == 'fiscal_settings':
            f_year = f_month = None

        await self.populate_panels()
        return error

    def get_work_on_fiscal_year(self) -> tuple:
        """
        Get the fical year that is being worked on.

        :returns: The fical year data.
        :rtype: tuple
        """
        fy = None

        for fy in self.cache.get_all_fiscal_years():
            if fy[5]:  # work_on
                break

        return fy

    #
    # Database access methods.
    #

    async def _add_fields_to_field_type_table(self, data: dict) -> int:
        """
        Add fields to the field_type table if they don't already exist.

        :param dict data: The data from the Organization or Budget panels in
                          the form of: {<field name>: <value>,...}.
        :returns: The insertion rowcount.
        :rtype: int
        """
        long = [field for field in data.keys()  # Test new key length.
                if len(field) > self._MAX_FIELD_LEN]

        if long:
            self._log.warning("Found field(s) that are longer than %s, %s.",
                              self._MAX_FIELD_LEN, long)

        fields = list(set(data.keys()) - set(self.cache.fields))
        fields.sort()
        rowcount = 0

        if fields:
            rowcount = await self.cache.insert(self._T_FIELD_TYPE,
                                               {'data': fields})

        return rowcount

    async def _do_select_query(self, query: str, params: tuple=()) -> list:
        """
        Do the actual query and return the results.

        :param str query: The SQL query to do.
        :params tuple params: Parameters to query.
        :returns: A list of the data.
        :rtype: list
        """
        async with aiosqlite.connect(self.user_data_fullpath,
                                     detect_types=self._DETECT_TYPES) as db:
            async with db.execute(query, params) as cursor:
                values = await cursor.fetchall()

        return values

    async def _do_insert_query(self, query: str, data: list) -> None:
        """
        Do the insert query.

        :param str query: The SQL query to execute.
        :param list or tuple data: Data to insert into the Data table.
        :returns: Number of rows affected by the query or 'None' of an
                  exception was raised.
        :rtype: int or None
        """
        return await self._do_query(query, data)

    async def _do_update_query(self, query: str, data: list) -> None:
        """
        Do the update query.

        :param str query: The SQL query to do.
        :param list or tuple data: Data to update into the Data table.
        :returns: Number of rows affected by the query or 'None' of an
                  exception was raised.
        :rtype: int or None
        """
        return await self._do_query(query, data)

    async def _do_delete_query(self, query: str, data: list) -> int:
        """
        Do the delete query.

        :param str query: The SQL query to do.
        :param list or tuple data: Data used to delete items from a table.
        :returns: Number of rows affected by the query or 'None' of an
                  exception was raised.
        :rtype: int or None
        """
        return await self._do_query(query, data)

    async def _do_query(self, query: str, data: list) -> int:
        """
        Do the INSERT, UPDATE, or DELETE queries.

        :param str query: The SQL query to execute.
        :param list or tuple data: Data used to insert, update, or delete
                                   items from a table.
        :returns: Number of rows affected by the query or '0' if an
                  exception was raised.
        :rtype: int or None
        """
        assert ';' in query, f"The query {query} does not end with a ';'."

        # Normalize: single row -> list of one row
        if data and (isinstance(data, dict) or not
                     isinstance(data, (list, tuple)) or
                     (isinstance(data, (list, tuple)) and data and not
                      isinstance(data[0], (list, tuple, dict)))):
            data = [data]

        async with aiosqlite.connect(self.user_data_fullpath,
                                     detect_types=self._DETECT_TYPES) as db:
            queries = [q.strip() for q in query.split(";") if q.strip()]
            rowcount = 0

            try:
                if len(queries) > 1:
                    await db.execute("BEGIN;")

                for stmt in queries:
                    if not stmt:  # pragma: no cover
                        continue

                    # Put the ; back on the query.
                    cursor = await db.executemany(stmt + ';', data)
                    rowcount += cursor.rowcount

                await db.commit()
            except Exception as e:
                await db.rollback()
                self._log.error("Error with data %s, %s", data, e,
                                exc_info=True)

        return rowcount
