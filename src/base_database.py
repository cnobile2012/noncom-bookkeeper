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
    Adapt a tuple → value.
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
    _T_LEDGER_HEADER = 'ledger_header'
    _T_LEDGER_TRANSACTION = 'ledger_transaction'
    _T_LEDGER_REFERENCE = 'ledger_reference'
    _T_LEDGER_BANK = 'ledger_bank'
    _T_LEDGER_COH = 'ledger_coh'
    _T_LEDGER_INCOME = 'ledger_income'
    _T_LEDGER_EXPENSE = 'ledger_expense'
    _V_LEDGER_HEADER = 'vw_ledger_header'
    _V_LEDGER_EXPENSE = 'vw_ledger_expense'
    _SCHEMA_TABLES = {
        _T_FISCAL_YEAR: (
            'pk INTEGER NOT NULL PRIMARY KEY',  # fy1fk or fy2fk in data
            'year INTEGER UNIQUE NOT NULL',
            'month INTEGER NOT NULL',
            'day INTEGER NOT NULL',
            'current INTEGER NOT NULL DEFAULT 0 CHECK (current IN (0, 1))',
            'work_on INTEGER NOT NULL DEFAULT 0 CHECK (work_on IN (0, 1))',
            'audit INTEGER NOT NULL DEFAULT 0 CHECK (audit IN (0, 1))',
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
            'mtime DATETIME NOT NULL',
            f'FOREIGN KEY (fy1fk) REFERENCES {_T_FISCAL_YEAR} (pk)',
            f'FOREIGN KEY (fy2fk) REFERENCES {_T_FISCAL_YEAR} (pk)',
            f'FOREIGN KEY (mfk) REFERENCES {_T_MONTH} (pk)',
            f'FOREIGN KEY (ffk) REFERENCES {_T_FIELD_TYPE} (pk)'),
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
            'mtime DATETIME NOT NULL',
            'CONSTRAINT unq UNIQUE (fyfk, cal_year_month)',
            f'FOREIGN KEY (fyfk) REFERENCES {_T_FISCAL_YEAR} (pk)'),
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
        _T_LEDGER_HEADER: (
            'pk INTEGER NOT NULL PRIMARY KEY',
            'fy1fk INTEGER NOT NULL',
            'fy2fk INTEGER NOT NULL',
            'ltfk INTEGER NOT NULL',
            'lrfk INTEGER NOT NULL',
            'trans_id INTEGER NOT NULL',
            'date DATE NOT NULL',
            'memo TEXT NULL',
            'purge INTEGER default 0',
            'ctime DATETIME NOT NULL',
            'mtime DATETIME NOT NULL',
            'CONSTRAINT unq UNIQUE (fy1fk, trans_id)',
            f'FOREIGN KEY (fy1fk) REFERENCES {_T_FISCAL_YEAR} (pk)',
            f'FOREIGN KEY (fy2fk) REFERENCES {_T_FISCAL_YEAR} (pk)',
            f'FOREIGN KEY (ltfk) REFERENCES {_T_LEDGER_TRANSACTION} (pk)',
            f'FOREIGN KEY (lrfk) REFERENCES {_T_LEDGER_REFERENCE} (pk)'),
        _T_LEDGER_TRANSACTION: (
            'pk INTEGER NOT NULL PRIMARY KEY',
            't_type INTEGER NOT NULL'),
        _T_LEDGER_REFERENCE: (
            'pk INTEGER NOT NULL PRIMARY KEY',
            'r_type INTEGER',
            'number TEXT NULL'),
        _T_LEDGER_BANK: (
            'pk INTEGER NOT NULL PRIMARY KEY',
            'lhfk INTEGER NOT NULL UNIQUE',
            't_type INTEGER NOT NULL',
            'amount INTEGER',
            'balance INTEGER',
            f'FOREIGN KEY (lhfk) REFERENCES {_T_LEDGER_HEADER} (pk)'),
        _T_LEDGER_COH: (
            'pk INTEGER NOT NULL PRIMARY KEY',
            'lhfk INTEGER NOT NULL UNIQUE',
            't_type INTEGER NOT NULL',
            'amount INTEGER',
            'balance INTEGER',
            f'FOREIGN KEY (lhfk) REFERENCES {_T_LEDGER_HEADER} (pk)'),
        _T_LEDGER_INCOME: (
            'pk INTEGER NOT NULL PRIMARY KEY',
            'lhfk INTEGER NOT NULL UNIQUE',
            't_type INTEGER NOT NULL',
            'amount INTEGER',
            'balance INTEGER',
            f'FOREIGN KEY (lhfk) REFERENCES {_T_LEDGER_HEADER} (pk)'),
        _T_LEDGER_EXPENSE: (
            'lhfk INTEGER NOT NULL',
            'ftfk INTEGER NOT NULL',
            'amount INTEGER',
            f'FOREIGN KEY (lhfk) REFERENCES {_T_LEDGER_HEADER} (pk)',
            f'FOREIGN KEY (ftfk) REFERENCES {_T_FIELD_TYPE} (pk)'),
        }
    _SCHEMA_VIEWS = {
        _V_LEDGER_HEADER: (
            'pk', 'trans_id', 'date', 'memo', 'fy1_year', 'fy1_month',
            'fy1_day', 'fy2_year', 'fy2_month', 'fy2_day', 't_type', 'r_type',
            'number', 'purge', 'ctime', 'mtime'),
        _V_LEDGER_EXPENSE: ('lhfk', 'field', 'amount'),
        }
    _SCHEMA_VIEW_QUERY = {
        _V_LEDGER_HEADER: (
            'SELECT ld.pk, ld.trans_id, ld.date, ld.memo, fy1.year, '
            'fy1.month, fy1.day, fy2.year, fy2.month, fy2.day, lt.t_type, '
            'lr.r_type, lr.number, ld.purge, ld.ctime, ld.mtime '
            f'FROM {_T_LEDGER_HEADER} AS ld '
            f'JOIN {_T_FISCAL_YEAR} AS fy1 ON ld.fy1fk = fy1.pk '
            f'JOIN {_T_FISCAL_YEAR} AS fy2 ON ld.fy2fk = fy2.pk '
            f'JOIN {_T_LEDGER_TRANSACTION} AS lt ON ld.ltfk = lt.pk '
            f'JOIN {_T_LEDGER_REFERENCE} AS lr ON ld.lrfk = lr.pk;'),
        _V_LEDGER_EXPENSE: (
            'SELECT le.lhfk, ft.field, le.amount '
            f'FROM {_T_LEDGER_HEADER} AS lh '
            f'JOIN {_T_LEDGER_EXPENSE} AS le ON le.lhfk = lh.pk '
            f'JOIN {_T_FIELD_TYPE} AS ft ON le.ftfk = ft.pk;')
        }
    _SCHEMA_INDICES = (
        ('idx_month_month ON month(month);'),
        ('idx_month_ord ON month(ord);'),
        ('idx_fiscal_year_year ON fiscal_year(year);'),
        ('one_current_fiscal_year ON fiscal_year(current) WHERE current = 1'),
        ('one_work_on_fiscal_year ON fiscal_year(work_on) WHERE work_on = 1'),
        )
    _TABLES = list(_SCHEMA_TABLES)
    _TABLES.sort()
    _VIEWS = list(_SCHEMA_VIEWS)
    _VIEWS.sort()
    _INDICES = [name.split()[0] for name in _SCHEMA_INDICES]
    _INDICES.sort()
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

    def get_db_columns(self, table: str) -> list:
        """
        Get the column names for the specified table.

        :param str table: The table name.
        :returns: a list of column names.
        :rtype: list
        """
        columns = []
        rows = self._SCHEMA_TABLES.get(table)

        if rows:
            for row in rows:
                column = row.split(' ')[0]
                if column in ('CONSTRAINT', 'FOREIGN'): continue
                columns.append(column)

        return columns

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
                    self._log.info("Created table: %s", query)
                    await db.execute(query)
                    await db.commit()

                for index in self._SCHEMA_INDICES:
                    query = 'CREATE INDEX IF NOT EXISTS ' + index
                    self._log.info("Created index: %s", query)
                    await db.execute(query)
                    await db.commit()

                for view, params in self._SCHEMA_VIEWS.items():
                    fields = ', '.join([field for field in params])
                    query = f"CREATE VIEW IF NOT EXISTS {view} ({fields}) AS "
                    query += self._SCHEMA_VIEW_QUERY.get(view)
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
        view_names = [name for type, name in data if type == 'view']
        view_names.sort()
        v_check = view_names == self._VIEWS

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

        if not v_check:
            msg = ("Database view count is wrong it should be "
                   f"'{self._VIEWS}' found '{view_names}'")
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
        fy = self.cache.work_on_fiscal_year
        year, month = (None, None) if fy == () else fy[1:3]

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
            if panel_name in ('organization', 'budget'):
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
        fy = self.cache.work_on_fiscal_year
        f_year, f_month, f_day = (None, None, None) if fy == () else fy[1:4]
        data = self.collect_panel_values(panel)

        if panel_name == 'organization':
            error = await self.dp.organization(data, (f_year, f_month, f_day))
        elif panel_name == 'budget':
            error = await self.dp.budget(data, f_year, f_month)
        elif panel_name == 'monthly':
            error = await self.dp.monthly(data, f_year)
        elif panel_name == 'fiscal':
            error = await self.dp.fiscal(data, (f_year, f_month, f_day))
        elif panel_name == 'ledger':
            error = await self.dp.ledger(data, (f_year, f_month, f_day))
        # elif panel_name == 'fiscal_settings':
        #     f_year = f_month = None

        await self.populate_panels()
        return error

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
        long = [field for field in data  # Test new key length.
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
        :returns: One or more rows of data.
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
            await db.execute('PRAGMA foreign_keys=ON;')
            queries = [q.strip() for q in query.split(';') if q.strip()
                       if q.strip()]
            rowcount = 0

            try:
                if len(queries) > 1:
                    await db.execute("BEGIN;")

                for stmt in queries:
                    # Put the ; back on the query.
                    cursor = await db.executemany(stmt + ';', data)
                    rowcount += cursor.rowcount

                await db.commit()
            except Exception as e:
                await db.rollback()
                self._log.error("Error with queries %s and data %s, %s",
                                queries, data, e, exc_info=True)

        return rowcount
