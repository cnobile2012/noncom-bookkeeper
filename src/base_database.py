# -*- coding: utf-8 -*-
#
# src/base_database.py
#
__docformat__ = "restructuredtext en"

import os
import aiosqlite

from zoneinfo import ZoneInfo

from geopy.geocoders import Nominatim
from geopy import exc
from timezonefinder import TimezoneFinder

from .config import Settings
from .populate_collect_panel import PopulateCollect


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
    _T_REPORT_TYPE = 'report_type'
    _T_DATA = 'data'
    _T_REPORT_PIVOT = 'report_pivot'
    _SCHEMA = (
        (_T_FISCAL_YEAR,
         'pk INTEGER NOT NULL PRIMARY KEY',  # fy1fk or fy2fk in data
         'year INTEGER UNIQUE NOT NULL',
         'month INTEGER NOT NULL',
         'day INTEGER NOT NULL',
         'current INTEGER NOT NULL',
         'work_on INTEGER NOT NULL',
         'audit INTEGER NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (_T_MONTH,
         'pk INTEGER NOT NULL PRIMARY KEY',  # mfk in data
         'month TEXT UNIQUE NOT NULL',
         'ord INTEGER UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (_T_FIELD_TYPE,
         'pk INTEGER NOT NULL PRIMARY KEY',  # ffk in data
         'field TEXT UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (_T_DATA,
         'pk INTEGER NOT NULL PRIMARY KEY',  # dfk in report_pivot
         'value NOT NULL',
         'fy1fk INTEGER NOT NULL',
         'fy2fk INTEGER NOT NULL',
         'mfk INTEGER NULL',
         'ffk INTEGER NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (_T_REPORT_TYPE,
         'pk INTEGER NOT NULL PRIMARY KEY',  # rfk in report_pivot
         'report TEXT UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (_T_REPORT_PIVOT,
         'rfk INTERGER NOT NULL', 'dfk INTEGER NOT NULL',
         f'FOREIGN KEY (rfk) REFERENCES {_T_REPORT_TYPE} (pk)',
         f'FOREIGN KEY (dfk) REFERENCES {_T_DATA} (pk)'),
        )
    _TABLES = [table[0] for table in _SCHEMA]
    _TABLES.sort()
    _EMPTY_FIELDS = ('', '0')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._org_data = None

    async def create_db(self):
        """
        Create the database based on the fields currently defined.
        """
        if (not os.path.exists(self.user_data_fullpath) or
            not await self.has_schema):
            async with aiosqlite.connect(self.user_data_fullpath) as db:
                for params in self._SCHEMA:
                    table = params[0]
                    fields = ', '.join([field for field in params[1:]])
                    query = f"CREATE TABLE IF NOT EXISTS {table}({fields})"
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
        query = "SELECT name FROM sqlite_master"
        table_names = [table[0]
                       for table in await self._do_select_query(query)
                       if not table[0].startswith('sqlite_')]
        table_names.sort()
        check = table_names == self._TABLES

        if not check:
            msg = ("Database table count is wrong it should be "
                   f"'{self._TABLES}' found '{table_names}'")
            self._log.error(msg)
            self._mf.statusbar_error = msg

        return check

    #
    # Database access methods.
    #

    async def _add_fields_to_field_type_table(self, data: dict) -> None:
        """
        Add fields to the field_type table if they don't already exist.

        :param dict data: The data from the Organization Information panel in
                          the form of: {<field name>: <value>,...}.
        """
        items = await self.select_from_field_type_table(data)
        old_fields = [item[1] for item in items]
        fields = self._find_fields(data, old_fields)

        if fields:
            await self.insert_into_field_type_table(fields)

    async def _insert_into_month_table(self) -> None:
        """
        Populate the `month` table with all months.
        """
        items = await self.select_from_month_table()
        months = self._ordered_month()

        if not items:  # Insert all months and their order.
            await self.insert_into_month_table(months)
        else:  # Insert only months and their order if not in the database.
            data = [item[1:3] for item in items]
            con_months = [(month, order) for order, month in months.items()]

            for item in data:
                if item not in con_months:
                    await self.insert_into_month_table(item)

    async def _insert_update_data_table(self, name: str, year: int, month: int,
                                        data: dict) -> None:
        """
        Insert or update `data` table.

        :param str name: Panel name.
        :param int year: A Baha'i year of the transaction.
        :param int month: A Baha'i month of the transaction. This is the order
                          of the Baha'i month not the name.
        :param dict data: The data from the any panel  in the form of:
                          {<field name>: <value>,...}.
        """
        values = await self.select_from_data_table(name, data, year, month)

        if not values:  # Do insert
            await self.insert_into_data_table(year, month, data)
        else:
            items = dict([(pk, (field, value))
                          for pk, field, value, y1, y2, c, m in values])
            insert_data = {}
            update_data = {}

            for pk, (field, value) in items.items():
                if field in data:  # Field value already exists.
                    update_data[field] = (pk, data[field])
                else:  # Field value does not exist.
                    insert_data[field] = data[field]

            if insert_data:  # Do insert
                await self.insert_into_data_table(year, month, insert_data)

            if update_data:  # Do update
                await self.update_data_table(year, month, update_data)

    async def _do_select_query(self, query: str, params: tuple=()) -> list:
        """
        Do the actual query and return the results.

        :param str query: The SQL query to do.
        :returns: A list of the data.
        :rtype: list
        """
        async with aiosqlite.connect(self.user_data_fullpath) as db:
            async with db.execute(query, params) as cursor:
                values = await cursor.fetchall()

        return values

    async def _do_insert_query(self, query: str, data: list) -> None:
        """
        Do the insert query.

        :param str query: The SQL query to do.
        :param list data: Data to insert into the Data table.
        """
        async with aiosqlite.connect(self.user_data_fullpath) as db:
            try:
                await db.executemany(query, data)
            except Exception as e:
                self._log.error(str(e), exc_info=True)
            else:
                await db.commit()

    async def _do_update_query(self, query: str, data: list) -> None:
        """
        Do the update query.

        :param str query: The SQL query to do.
        :param list data: Data to update into the Data table.
        """
        async with aiosqlite.connect(self.user_data_fullpath) as db:
            try:
                await db.executemany(query, data)
            except Exception as e:
                self._log.error(str(e), exc_info=True)
            else:
                await db.commit()

    #
    # Utilitu methods
    #

    def _find_fields(self, new: list, old: list) -> set:
        """
        Find the fields to select or insert.

        :param list or dict new: The new fields in the form of:
                                 [<field name>,...].
        :param list old: The old fields in the form of: [<field name>,...].
        :returns: A list of fields.
        :rtype: list
        """
        new_fields = set(new)  # Just get the keys if a dict.
        old_fields = set(old)
        return new_fields - old_fields

    def _find_timezone(self, address: str):
        """
        Find the IANA timezone name, latitude, and longitude.

        :param str address: The address, City, or town used to find the
                            required information.
        :returns: The IANA timezone name, latitude, and longitude.
        :rtype: tuple
        """
        error = None
        geolocator = Nominatim(user_agent='nc-bookkeeper')

        try:
            location = geolocator.geocode(address)
        except exc.GeocoderError as e:
            self._log.error("Could not get information on %s, %s", address, e)
            error = str(e)
        else:
            error = None

        if location:
            lat = location.latitude
            lon = location.longitude
            tf = TimezoneFinder()
            iana = tf.timezone_at(lng=lon, lat=lat)
        elif error:
            iana = lat = lon = None
            self._mf.statusbar_error = f"{error}"
        else:
            iana = lat = lon = None
            msg = f"Cannot find the timezone for '{address}'."
            self._mf.statusbar_error = msg

        return iana, lat, lon

    #
    # Properties
    #

    @property
    def organization_data(self) -> dict:
        """
        This property gets the organization data that are used throughout
        the application without having to do a select on the DB everytime.

        :returns: The organization data as defined by {<field name>: <value>}.
        :rtype: dict
        """
        return self._org_data

    @organization_data.setter
    def organization_data(self, values: list) -> None:
        """
        This property sets the organization constants that are used throughout
        the application without having to do a select on the DB everytime.

        .. note::

           1. It is used in the `bahai_database.populate_panels`, and
              `generic_database.populate_panels` methods.
           2. Only the second and three fields are stored when the incoming
              values are a list otherwise the dict is used as is.

        :param list or dict values: A list of tuples where each tuple is the
                                    raw data for one field in the form of
                                    (PK, <field name>, <value>, <fiscal year>,
                                    <next year>, <c_time>, <m_time>).
        """
        if isinstance(values, list):
            self._org_data = {value[1]: value[2] for value in values}
        else:
            self._org_data = values

    @property
    def tzinfo(self):
        iana_name = self.organization_data.get('iana_name')
        return ZoneInfo(iana_name if iana_name else 'UTC')
