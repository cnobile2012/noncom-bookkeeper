# -*- coding: utf-8 -*-
#
# src/base_database.py
#
__docformat__ = "restructuredtext en"

import os
import wx
import sqlite3
import aiosqlite

from geopy.geocoders import Nominatim
from geopy import exc
from timezonefinder import TimezoneFinder

from .config import Settings
from .utilities import StoreObjects
from .populate_collect_panel import PopulateCollect
from .prep_and_cache import DataPreperation, Cache
import tracemalloc
tracemalloc.start()


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
    _T_MONTHLY_PIVOT = 'monthly_pivot'
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
            'pk INTEGER NOT NULL PRIMARY KEY',  # mlfk in monthly_pivot
            'participation INTEGER',
            'outstanding INTEGER',
            'coh INTEGER',
            'membership INTEGER',
            'treasurer TEXT NOT NULL',
            'locality INTEGER NOT NULL',
            'ctime DATETIME NOT NULL',
            'mtime DATETIME NOT NULL'),
        _T_MONTHLY_PIVOT: (
            'mfk INTEGER NOT NULL',
            'fyfk INTEGER NOT NULL',
            'mlfk INTEGER NOT NULL',
            'UNIQUE(mfk, fyfk)',
            f'FOREIGN KEY (mfk) REFERENCES {_T_MONTH} (pk)',
            f'FOREIGN KEY (fyfk) REFERENCES {_T_FISCAL_YEAR} (pk)',
            f'FOREIGN KEY (mlfk) REFERENCES {_T_MONTHLY} (pk)'),
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
        ('idx_monthly_pivot_month ON monthly_pivot(mfk);'),
        ('idx_monthly_pivot_fy ON monthly_pivot(fyfk);'),
        ('idx_monthly_pivot_month_fy ON monthly_pivot(mfk, fyfk);')
        )
    _TABLES = list(_SCHEMA_TABLES.keys())
    _TABLES.sort()
    _INDICES = [name.split()[0] for name in _SCHEMA_INDICES]
    _INDICES.sort()
    _EXCLUDE_PANELS = ('fiscal', 'monthly')
    _MAX_FIELD_LEN = 40  # Max length of fields allowed in the field_table.
    _DETECT_TYPES = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mf = StoreObjects().get_object('MainFrame')
        self._dp = DataPreperation(self)
        self._cache = Cache(self)

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
                    # extra = self._SCHEMA_EXTRA.get(table)
                    # Remove ; from query above if extra is used.
                    # query += f' {extra};' if extra else ';'
                    self._log.info("Created table: %s", query)
                    await db.execute(query)
                    await db.commit()

                for index in self._SCHEMA_INDICES:
                    query = 'CREATE INDEX IF NOT EXISTS ' + index
                    self._log.info("Created index: %s", query)
                    await db.execute(query)
                    await db.commit()

                # The for loop below and a few lines above would be used
                # if there are views in the schema.
                # for view, params in self._SCHEMA_VIEWS.items():
                #     fields = ', '.join([field for field in params])
                #     query = f"CREATE VIEW IF NOT EXISTS {view} ({fields})"
                #     extra = self._SCHEMA_EXTRA.get(view)
                #     query += f' {extra};' if extra else ';'
                #     self._log.info("Created view: %s", query)
                #     await db.execute(query)
                #     await db.commit()

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

    async def populate_panels(self) -> tuple:
        """
        Populate all panels that have data in the database.
        """
        if not self.cache.has_cache:
            await self.cache.load()

        fiscal_years = self.cache.get(self._T_FISCAL_YEAR)

        if len(fiscal_years):
            # Find the start year
            year, month = min([(item[1], item[2]) for item in fiscal_years])
        else:  # Only for first time use.
            year = month = None

        if None not in (year, month):
            self._log.info("Populating all panels in %04d-%02d.", year, month)
            pcdp = {name: panel for name, panel in self._mf.panels.items()
                    if name not in self._EXCLUDE_PANELS}
            await self._populate_config_data_panels(year, pcdp)
            monthly = self._mf.panels.get('monthly')
            await self._populate_monthly_panel(year, month, monthly)
            # *** TODO *** Populate the fiscal panel

        return year, month

    async def _populate_config_data_panels(self, year, panels) -> None:
        """
        Populate all panels that use the config data table.

        :param int year: The current fiscal year.
        :param dict panels: A dict of all non-excluded panels.
        """
        for panel_name, panel in panels.items():
            data = self.collect_panel_values(panel)
            keys = list(data.keys())
            values = await self.select_from_config_data_table(keys, year)

            # Needed when the app has been run at least one time before.
            if panel_name == 'organization' and values:
                # This stores and converts a list to a dict.
                items = self._dp.organization_data
            else:
                items = {value[1]: value[2] for value in values}

            # Add any new fields to the database.
            await self._add_fields_to_field_type_table(data)
            panel.initializing = True
            self.populate_panel_values(panel_name, panel, items)
            panel.initializing = False

    async def _populate_monthly_panel(self, fy_year: int, fy_month: int,
                                      panel: wx.Panel) -> None:
        """
        Populate the monthly panel.

        :param int fy_year: The fiscal year.
        :param int fy_month: The ordinal for the month in the current fiscal
                             year.
        :param wx.Panel panel: The panel object.
        """
        fiscal_years = self.cache.get(self._T_FISCAL_YEAR)

        if len(fiscal_years):
            years_months = [(item[1], item[2]) for item in fiscal_years]

        data = self.collect_panel_values(panel)
        widget_ord = data['month_of_year']

        if widget_ord == 0:  # "Choose Current Month" default message.
            month = -1
        elif widget_ord == 19:  # Ayyám-i-Há
            month = 0
        elif widget_ord == 20:  # 'Alá'
            month = 19
        elif widget_ord < fy_month:
            month = widget_ord
            fy_year += 1
            data['month_of_year'] = 0  # Placeholder
        else:  # Should be fy_month - 18
            month = widget_ord

        values = await self.select_from_monthly_table(fy_year, month)

        if data['treasurer_this_month'] == "" and self._dp.organization_data:
            data['treasurer_this_month'] = self._dp.organization_data[
                'treasurer']
            data['total_membership_this_month'] = self._dp.organization_data[
                'total_membership']

        if values:
            data = self.convert_monthly_list_to_dict(values, data)

        if month > -1:
            panel.initializing = True
            panel.date = (fy_year, month)
            self.populate_panel_values('monthly', panel, data)
            panel.initializing = False

    async def save_to_database(self, name: str, panel: wx.Panel) -> None:
        """
        Save the given panel data to the database.

        :param str name: The internal name of the current panel.
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
        f_year, f_month = await self.populate_panels()
        data = self.collect_panel_values(panel)

        if name == 'organization':
            error = await self._dp.organization(data, f_year, f_month)
        elif name == 'fiscal':
            data = await self._dp.fiscal(data, f_year, f_month)
            f_year = f_month = None
        elif name == 'fiscal_settings':
            f_year = f_month = None
        elif name == 'budget':
            if f_year and f_month:
                error = await self._insert_update_config_data_table(
                    f_year, month=f_month, data=data)
        elif name == 'monthly':
            if data:
                empty_fields = []
                values = {}

                for field, value in data.items():
                    f_name, manditory = self._MONTHLY_FIELD_MAP.get(
                        field, ('unknown', True))
                    assert f_name != 'unknown', ("An unknown field was found "
                                                 "in the monthly panel.")
                    values[f_name] = value if value else 0

                    if manditory and value in self._EMPTY_FIELDS:
                        empty_fields.append(field)

                if len(empty_fields) != 0:
                    ef = ', '.join([f for f in empty_fields])
                    error = f"The '{ef}' field(s) must not be empty."
                    self._log.warning(error)
                else:
                    await self._insert_update_monthly_table(
                        f_year, values['month'], values)

        return error

    #
    # Database access methods.
    #

    async def _add_fields_to_field_type_table(self, data: dict) -> None:
        """
        Add fields to the field_type table if they don't already exist.

        :param dict data: The data from the Organization Information panel in
                          the form of: {<field name>: <value>,...}.
        """
        keys = list(data.keys())
        current_fields = self.cache.fields
        new_fields = [fd for fd in data if (len(fd) <= self._MAX_FIELD_LEN)]
        fields = set(new_fields) - set(current_fields)

        if fields:
            await self.insert_into_field_type_table(fields)

    async def _insert_update_config_data_table(
        self, year: int, *, month: int=None, data: dict={}) -> None:
        """
        Insert or update `data` table.

        :param int year: A Baha'i year of the transaction.
        :param int month: A Baha'i month of the transaction. This is the order
                          of the Baha'i month not the name.
        :param dict data: The data from the any panel  in the form of:
                          {<field name>: <value>,...}.
        :returns: None if no errors. If an error a, error message.
        :rtype: None or str
        """
        error = None
        keys = list(data.keys())
        values = await self.select_from_config_data_table(keys, year)

        if not values:  # Do insert
            await self.insert_into_config_data_table(year, month, data)
            self._log.info("Inserted %s table data: %s.", self._T_DATA, data)
        else:
            insert_data = {}
            update_data = []
            #        field,    pk,      y1
            items = {item[1]: (item[0], item[3]) for item in values}

            for field, value in data.items():  # Loop through incoming data.
                pk, y1 = items.get(field, (None, None))  # Selected data

                if not pk or not y1:           # Error condition
                    error = f"Could not find field {field} in {data}."
                    self._mf.statusbar_error = error
                    self._log.error(error)
                    break

                if year != y1:                 # Insert
                    insert_data[field] = value
                else:                          # Update
                    update_data.append((pk, value))

            if insert_data:                    # Do insert
                rowcount = await self.insert_into_config_data_table(
                    year, month, insert_data)

            if update_data:                    # Do update
                rowcount = await self.update_config_data_table(year, month,
                                                               update_data)

        return error

    # async def _select_monthly_table(self, year: int, month: int=None) -> list:
    #     """
    #     Select data from the monthly table.

    #     :param int year: Year of insert or update.
    #     :param int month: Month of insert or update.
    #     :returns: Monthly data.
    #     :rtype: list
    #     """
    #     months = await self.select_from_monthly_table(year, month)
    #     return months

    async def _insert_update_monthly_table(self, year: int, month: int,
                                           data: dict) -> int:
        """
        Insert or update the monthly table.

        :param int year: Year of insert or update.
        :param int month: Month of insert or update.
        :param dict data: The data to be inserted.
        :returns: The row count caused by the insert or update.
        :rtype: int
        """
        values = await self.select_from_monthly_table(year, month)

        if values:  # Do update
            rowcount = await self.update_monthly_table(year, data)
            self._log.info("Updated %s table data: %s.", self._T_MONTHLY, data)
        else:  # Do insert
            rowcount = await self.insert_into_monthly_table(year, data)
            self._log.info("Inserted %s table data: %s.", self._T_MONTHLY,
                           data)

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

                    # Put the ; back on the quert.
                    cursor = await db.executemany(stmt + ';', data)
                    rowcount += cursor.rowcount

                await db.commit()
            except Exception as e:
                await db.rollback()
                self._log.error("Error with data %s, %s", data, e,
                                exc_info=True)

        return rowcount
