# -*- coding: utf-8 -*-
#
# src/bahai_database.py
#
__docformat__ = "restructuredtext en"

import sqlite3
import datetime
from zoneinfo import ZoneInfo

from .base_database import BaseDatabase
from .custom_widgits import ordered_month

import badidatetime
badidatetime.enable_geocoder()


def adapt_datetime(dt):
    """
    Adapter: datetime → ISO string
    """
    return dt.isoformat()


def custom_converter(value):
    """
    Converter: ISO string → datetime
    """
    if isinstance(value, bytes):
        value = value.decode("utf-8")

    return badidatetime.datetime.fromisoformat(value)


sqlite3.register_adapter(badidatetime.datetime, adapt_datetime)
sqlite3.register_converter('DATETIME', custom_converter)


class Database(BaseDatabase):
    """
    Create, and update the database for the Bahá'í Bookkeeping application.
    """
    _MONTHLY_FIELD_MAP = {'month_of_year': ('month', True),
                          'participation': ('participation', False),
                          'outstanding_bills': ('outstanding', False),
                          'end_of_month_cash_on_hand': ('coh', False),
                          'total_membership_this_month': ('membership', False),
                          'treasurer_this_month': ('treasurer', True),
                          'locality_prefix_month': ('locality', True)}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    #
    # Fiscal year SELECT, INSERT and UPDATE methods.
    #

    async def select_from_fiscal_year_table(self, *, year: int=None,
                                            month: int=None, day: int=None,
                                            current: int=None, audit: int=None,
                                            work_on: int=None,
                                            fiscal: bool=False
                                            ) -> list | tuple:
        """
        Select from the `fiscal_year` table. Only the year is needed to
        select the correct row of data.

        :param int year: The `year` is used to query for a given year.
        :param int month: The `month` is used to query a given month in
                          all years.
        :param int day: The `day` is used to query for a given day in
                        all years and months.
        :param int current: This will return the current fiscal year if `1`
                            or the next year if `0`. If set to `None`
                            (default) then do a query for the provided year.
        :param int audit: The `audit` is used to query all years audited or
                          not audited.
        :param int work_on: The `work_on` is used to switch the fiscal year
                            that is being worked on.
        :param bool fiscal: The current year and the one after.
        :returns: The `fiscal_year` table data for the year requested.
        :rtype: list or tuple
        """
        assert (year, month, day, current,
                work_on, audit).count(None) in (5, 6), (
            "Can only query for one of (year, month, day, current, audit, "
            "work_on) or none meaning all.")

        if year:       # Get by specific year.
            where = f"WHERE year={year}"
        elif month:    # Get all years with this month.
            where = f"WHERE month={month}"
        elif day:      # Get all years and month with this day.
            where = f"WHERE day={day}"
        elif current:  # Get the current fiscal year.
            where = f"WHERE current={current}"
        elif work_on:  # Switch years to work on.
            where = f"WHERE work_on={work_on}"
        elif audit:    # Get all years that have or have not been audited.
            where = f"WHERE audit={audit}"
        elif fiscal:   # Get the current and the year after.
            where = (f"WHERE year IN (SELECT year FROM {self._T_FISCAL_YEAR} "
                     "WHERE current = 1 UNION "
                     f"SELECT year + 1 FROM {self._T_FISCAL_YEAR} "
                     "WHERE current = 1) ORDER BY year ASC")
        else:          # Get all fiscal years.
            where = ""

        query = (f"SELECT * FROM {self._T_FISCAL_YEAR} {where};")
        data = await self._do_select_query(query)
        # Return the list of a single record or a list of all records
        # based on the query.
        return data[0] if len(data) == 1 else data

    async def insert_into_fiscal_year_table(self, data: list) -> int:
        """
        Insert a row of data into the `fiscal_year` table.

        :param list data: The data to be inserted.
        :returns: The insertion rowcount.
        :rtype: int
        """
        fields = "year, month, day, current, work_on, audit, ctime, mtime"

        if isinstance(data[0], tuple) and len(data[0]) == 9:
            items = data
            fields = "pk, " + fields
            values = "?, ?, ?, ?, ?, ?, ?, ?, ?"
        else:
            now = badidatetime.datetime.now(self.utc_tzinfo)
            items = [t + (now, now) for t in data]
            values = "?, ?, ?, ?, ?, ?, ?, ?"

        query = (f"INSERT INTO {self._T_FISCAL_YEAR} ({fields}) "
                 f"VALUES ({values});")
        return await self._do_insert_query(query, items)

    async def update_fiscal_year_table(self, data: list) -> int:
        """
        Update the `fiscal_year` table. Only the year and current values
        are needed to do updates.

        :param list data: The data to be updated.
        :returns: The rowcount of the update.
        :rtype: int

        .. note::

           Incoming data:

             1. From the fiscal year table:
                [(year, month, day, current, work_on, audit, current), ...]
             2. From the fiscal panel:
                [(current_fiscal_year, work_on_this_fiscal_year,
                  audit_complete), ...]
        """
        now = badidatetime.datetime.now(self.utc_tzinfo)
        query = (f"UPDATE {self._T_FISCAL_YEAR} "
                 "SET current = :current, work_on = :work_on, audit = :audit, "
                 "mtime = :mtime WHERE year = :year;")
        items = [{'year': item[0], 'current': item[3], 'work_on': item[4],
                  'audit': item[5], 'mtime': now} for item in data]
        return await self._do_update_query(query, items)

    #
    # Month SELECT and INSERT methods.
    #

    async def select_from_month_table(self, *, name: str=None, order: int=None,
                                      pk: int=None) -> list:
        """
        Select from the `month` table.
        """
        assert len([arg for arg in (name, order, pk) if arg is None]) >= 2, (
                "Cannot query for more than one or none of the arguments.")

        if name:
            where = f"WHERE month = {name}"
        elif order:
            where = f"WHERE ord = {order}"
        elif pk:
            where = f"WHERE pk = {pk}"
        else:
            where = ""

        query = (f"SELECT * FROM {self._T_MONTH} {where};")
        data = await self._do_select_query(query)
        return data[0] if len(data) == 1 else data

    async def insert_into_month_table(self, months: list) -> int:
        """
        Insert into the `month` table.

        :param list months: A list of tuples where the 1st value is the month
                            name and the 2nd value is the order of the month.
        :returns: The row count caused by the insert.
        :rtype: int
        """
        fields = "month, ord, ctime"

        if isinstance(months[0], tuple) and len(months[0]) == 4:
            data = months
            fields = "pk, " + fields
            values = "?, ?, ?, ?"
        else:
            now = badidatetime.datetime.now(self.utc_tzinfo)
            data = [(name, order, now) for name, order in months]
            values = "?, ?, ?"

        query = f"INSERT INTO {self._T_MONTH} ({fields}) VALUES ({values});"
        return await self._do_insert_query(query, data)

    #
    # Field Names SELECT, INSERT and, UPDATE methods.
    #

    async def select_from_field_type_table(self, data: list | None) -> list:
        """
        Select from the field_type table.

        :param list data: The field names for any data in this table or `None`
                          if all data is needed.
        :returns: The values read from the FieldType table in the form of
                  [(<pk>, <field>, <rids>, <ctime>, <mtime>), ...].
        :rtype: list of tuples
        """
        if data is not None:
            fields = '", "'.join(data)
            where = f' WHERE field IN ("{fields}");'
        else:
            where = ';'

        query = f'SELECT * FROM {self._T_FIELD_TYPE}' + where
        return await self._do_select_query(query)

    async def insert_into_field_type_table(self, data: list) -> int:
        """
        Insert fields into the field_type table.

        :param set or list data: The fields from any panel or a list for
                                 inserting all records.
        :returns: The row count caused by the insert.
        :rtype: int
        """
        if isinstance(data[0], tuple) and len(data[0]) == 4:
            items = data
            fields = 'pk, field, ctime, mtime'
            values = '?, ?, ?, ?'
        else:
            now = badidatetime.datetime.now(self.utc_tzinfo)
            items = [(field, now, now) for field in data]
            fields = 'field, ctime, mtime'
            values = '?, ?, ?'

        query = (f"INSERT INTO {self._T_FIELD_TYPE} ({fields}) "
                 f"VALUES ({values});")
        return await self._do_insert_query(query, items)

    #
    # Config data SELECT, INSERT and, UPDATE methods.
    #

    async def select_from_config_data_table(self, data: list, year: int=None
                                            ) -> list:
        """
        Reads a row or rows from the `data` table.

        :param dict data: The data from the any panel in the form of:
                          {<field name>: <value>,...}.
        :param int year: A Baha'i year used to select the current fiscal year.
        :returns: A list of rows from the Data table.
        :rtype: list

        .. note::

           Produces output as follows for the `organization` panel:
           [(1, 'locale_name', 'Some Community', 182, 183,
             '0182-02-12T05:26:40.963200+00:00',
             '0182-02-12T05:26:40.963200+00:00'),
            (2, 'locality_prefix', 0, 182, 183,
             '0182-02-12T05:26:40.963200+00:00',
             '0182-02-12T05:26:40.963200+00:00'),
            (3, 'location_city_name', 'Some City', 182, 183,
             '0182-02-12T05:27:17.251199+00:00',
             '0182-02-12T05:27:17.251199+00:00'),
            (4, 'start_of_fiscal_year', '0182-02-19', 182, 183,
             '0182-02-12T05:27:17.251199+00:00',
             '0182-02-12T05:27:17.251199+00:00'),
            (5, 'total_membership', '35', 182, 183,
             '0182-02-12T05:27:17.251199+00:00',
             '0182-02-12T05:27:17.251199+00:00'),
            (6, 'treasurer', 'Joe Shmow', 182, 183,
             '0182-02-12T05:27:17.251199+00:00',
             '0182-02-12T05:27:17.251199+00:00')
           ]
        """
        fields = '", "'.join(data)

        if year:
            params = (year, year+1)
            query = (
                "SELECT d.pk, f.field, d.value, y1.year, y2.year, "
                "       d.ctime, d.mtime "
                f"FROM {self._T_DATA} AS d "
                f"JOIN {self._T_FIELD_TYPE} AS f ON f.pk = d.ffk "
                f"     AND f.field IN (\"{fields}\") "
                f"JOIN {self._T_FISCAL_YEAR} AS y1 ON y1.pk = d.fy1fk "
                "      AND y1.year = ? "
                f"JOIN {self._T_FISCAL_YEAR} AS y2 ON y2.pk = d.fy2fk "
                "      AND y2.year = ? "
                )
        else:  # *** TODO *** May not be used anymore.
            print("IMPORTANT", fields)
            params = ()
            query = (
                "SELECT d.pk, f.field, d.value, d.ctime, d.mtime "
                f"FROM {self._T_DATA} AS d "
                f"JOIN {self._T_FIELD_TYPE} AS f ON f.pk = d.ffk "
                f"     AND f.field IN (\"{fields}\");"
                )

        return await self._do_select_query(query, params)

    async def insert_all_into_config_data_table(self, data: list) -> int:
        """
        Insert all values into the Data table.

        :param list data: Multi-row data.
        :returns: The row count caused by the insert.
        :rtype: int

        .. note::

           Incoming data: (pk, value, fy1fk, fy2fk, mfk, ffk, ctime, mtime)
        """
        query = (f"INSERT INTO {self._T_DATA} (pk, value, fy1fk, fy2fk, mfk, "
                 "ffk, ctime, mtime) VALUES (?, ?, ?, ?, ?, ?, ?, ?);")
        return await self._do_insert_query(query, data)

    async def insert_into_config_data_table(self, year: int, month: int,
                                            data: list) -> int:
        """
        Insert values into the Data table.

        :param int year: A Baha'i year of the transaction.
        :param int month: A Baha'i month of the transaction. This is the order
                          of the Baha'i month not the name.
        :param list data: The data from the any panel in the form of:
                          [(<field_name>, <value>), ...].
        :returns: The row count caused by the insert.
        :rtype: int
        """
        fy1 = await self.select_from_fiscal_year_table(current=1)
        items = dict(data)  # Convert a list of tuples into a dict.

        if fy1:
            now = badidatetime.datetime.now(self.utc_tzinfo)
            f_items = await self.select_from_field_type_table(items)
            f_month = await self.select_from_month_table(order=month)
            fy2 = await self.select_from_fiscal_year_table(year=fy1[1]+1)

            query = (
                f"INSERT INTO {self._T_DATA} (value, fy1fk, fy2fk, mfk, ffk, "
                "ctime, mtime) VALUES (:value, :fy1fk, :fy2fk, :mfk, :ffk, "
                ":ctime, :mtime);"
                )
            values = []

            for item in f_items:
                pk, field, ctime, mtime = item
                mfk = f_month[0]
                fy1fk = fy1[0]  # We want the FK not the year.
                fy2fk = fy2[0]  # We want the FK not the year.
                values.append({'value': items[field], 'fy1fk': fy1fk,
                               'fy2fk': fy2fk, 'mfk': mfk, 'ffk': pk,
                               'ctime': now, 'mtime': now})

            rowcount = await self._do_insert_query(query, values)
        else:
            self._log.error("No current fiscal_year data in the database.")
            rowcount = 0

        return rowcount

    async def update_config_data_table(self, data: list) -> int:
        """
        Update the `data` table.

        :param list data: The data from the any panel  in the form of:
                          [(<pk>, <value>), ...}.
        :returns: The row count caused by the update.
        :rtype: int
        """
        for item in data:
            assert isinstance(item[0], int), (
                f"The pk '{item[0]}' is not an integer.")
            assert isinstance(item[1], str), (
                f"The value '{item[1]}' is not a string.")

        mtime = badidatetime.datetime.now(self.utc_tzinfo)
        query = (f"UPDATE {self._T_DATA} SET value = :value, "
                 "mtime = :mtime WHERE pk = :pk;")
        items = [{'pk': pk, 'value': value, 'mtime': mtime}
                 for pk, value in data]
        return await self._do_update_query(query, items)

    #
    # Monthly SELECT, INSERT, and UPDATE methods.
    #

    async def select_from_monthly_table(self, year: int=None, month: int=None
                                        ) -> list:
        """
        Select values from the monthly table.

        :param int year: The fiscal year of the month needed.
        :param int month: The ordinal value of the month needed.
        :returns: The data for the given month.
        :rtype: list
        """
        if month is not None:
            where = " AND fy.month = :month;"
            data = {'year': year, 'month': month}
        else:
            where = ";"
            data = {'year': year}

        query = (f"SELECT m.*, mo.month, mo.ord FROM {self._T_MONTHLY} AS m "
                 f"JOIN {self._T_MONTHLY_PIVOT} AS mp ON mp.mlfk = m.pk "
                 f"JOIN {self._T_MONTH} AS mo ON mo.pk = mp.mfk "
                 f"JOIN {self._T_FISCAL_YEAR} AS fy ON fy.pk = mp.fyfk "
                 "WHERE  fy.year = :year")

        values = await self._do_select_query(query + where, data)
        return values[0] if len(values) == 1 else values

    async def insert_all_into_monthly_table(self, data: list) -> int:
        """
        Insert all data into the monthly table.

        :param list data: The data from the any panel  in the form of:
                          [(pk, participation, outstanding, coh, membership,
                            treasurer, locality, ctime, mtime), ...].
        """
        query = (f"INSERT INTO {self._T_MONTHLY} (pk, participation, "
                 "outstanding, coh, membership, treasurer, locality, ctime, "
                 "mtime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);")
        return await self._do_insert_query(query, data)

    async def insert_into_monthly_table(self, year: int, data: dict) -> int:
        """
        Insert values in the monthly table.

        :param int year: A Baha'i year of the transaction.
        :param dict data: The data from any panel in the form of:
                          {'participation': <value>, ...}.
        :returns: The row count caused by the update.
        :rtype: int
        """
        now = badidatetime.datetime.now(self.utc_tzinfo)
        data['ctime'] = data['mtime'] = now
        # Data for the monthly_pivot table.
        month = data.pop('month')
        data['mfk'] = (await self.select_from_month_table(order=month))[0]
        fiscal = await self.select_from_fiscal_year_table(year=year)
        data['fyfk'] = fiscal[0]
        query = (f"INSERT INTO {self._T_MONTHLY} (participation, outstanding, "
                 "coh, membership, treasurer, locality, ctime, mtime) VALUES ("
                 ":participation, :outstanding, :coh, :membership, "
                 ":treasurer, :locality, :ctime, :mtime);")
        query += (f"INSERT INTO {self._T_MONTHLY_PIVOT} (mfk, fyfk, mlfk) "
                  "VALUES (:mfk, :fyfk, last_insert_rowid());")
        return await self._do_insert_query(query, data)

    async def update_monthly_table(self, year: int, data: dict) -> int:
        """
        Update values in the monthly table.

        :param int year: A Baha'i year of the transaction.
        :param dict data: The data from the any panel  in the form of:
                          [(pk, <value>), ...}.
        :returns: The row count caused by the update.
        :rtype: int
        """
        data['year'] = year
        data['mtime'] = badidatetime.datetime.now(self.utc_tzinfo)
        query = (f"UPDATE {self._T_MONTHLY} AS m SET "
                 "participation = :participation, outstanding = :outstanding, "
                 "coh = :coh, membership = :membership, "
                 "treasurer = :treasurer, locality = :locality, "
                 f"mtime = :mtime FROM {self._T_MONTHLY_PIVOT} AS mp "
                 f"JOIN {self._T_MONTH} AS mo ON mo.pk = mp.mfk "
                 f"JOIN {self._T_FISCAL_YEAR} AS fy ON fy.pk = mp.fyfk "
                 "WHERE mp.mlfk = m.pk AND mo.ord = :month "
                 "AND fy.year = :year;")
        return await self._do_update_query(query, data)

    def convert_monthly_list_to_dict(self, items: tuple, data: dict={}):
        data['month_of_year'] = self.ordinal_month_to_widget(items[10])
        data['participation'] = items[1]
        data['outstanding_bills'] = items[2]
        data['end_of_month_cash_on_hand'] = items[3]
        data['total_membership_this_month'] = items[4]
        data['treasurer_this_month'] = items[5]
        data['locality_prefix_month'] = items[6]
        return data

    #
    # Miscellaneous methods and properties
    #

    def ordered_month(self):
        """
        Provides the order of the Badi months from the custom_widgets module.
        """
        return [(name, ord) for ord, name in ordered_month().items()]

    def _convert_date_to_yymmdd(self, value: str) -> badidatetime.date:
        """
        Converts the ISO date string to an instance of 'badidatetime.date'.

        :param str value: A ISO formatting date string.
        :returns: An instance of 'badidatetime.date'.
        :rtype: badidatetime.date
        """
        return badidatetime.date.fromisoformat(value)

    def _ymd_from_iso(self, iso: str) -> tuple:
        """
        Convert the ISO string to (year, month, day).

        :param str iso: The ISO date string.
        :returns: The year, month, and day from an ISO string.
        :rtype: tuple
        """
        return badidatetime.date.fromisoformat(iso).b_date

    def _today(self) -> badidatetime.date:
        """
        Return an instance of 'date' for today.

        :returns: Today as in instance.
        :rtype: badidatetime.date
        """
        return badidatetime.date.today()

    @property
    def utc_tzinfo(self):
        return badidatetime.UTC

    @property
    def tzinfo(self) -> badidatetime.TZWithCoords:
        lat = self.organization_data.get('latitude')
        lon = self.organization_data.get('longitude')
        iana_name = self.organization_data.get('iana_name')
        offset = self._get_standard_offset(iana_name)
        return badidatetime.TZWithCoords(lat, lon, offset/3600)

    def _get_standard_offset(self, iana_key: str) -> datetime.timedelta:
        assert iana_key, "The IANA key has not been set."
        tz = ZoneInfo(iana_key)
        now = datetime.datetime.now(tz)

        # Try every month and find the offset where DST is 0 (standard time)
        for month in range(1, 13):
            dt = datetime.datetime(now.year, month, 15, tzinfo=tz)

            # No DST active = standard time
            if dt.dst() == datetime.timedelta(0):
                return dt.utcoffset()

        # Zone has no DST at all — any offset is the standard offset
        return datetime.datetime(now.year, 1, 15, tzinfo=tz).utcoffset()

    def ordinal_month_to_widget(self, month):
        if month == 0:  # Ayyám-i-Há
            value = 19
        elif month == 19:  # 'Alá'
            value = 20
        else:
            value = month  # Should be 1 - 18

        return value
