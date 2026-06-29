# -*- coding: utf-8 -*-
#
# src/bahai_database.py
#
__docformat__ = "restructuredtext en"

import sqlite3
import datetime
import badidatetime

from zoneinfo import ZoneInfo

from .base_database import BaseDatabase
from .custom_widgits import ordered_month


def adapt_datetime(dt: badidatetime.datetime) -> str:
    """
    Adapter: datetime → ISO string
    """
    return dt.isoformat()


def convert_datetime(value: str) -> badidatetime.datetime:
    """
    Converter: ISO string → datetime
    """
    if isinstance(value, bytes):
        value = value.decode("utf-8")

    return badidatetime.datetime.fromisoformat(value)


sqlite3.register_adapter(badidatetime.datetime, adapt_datetime)
sqlite3.register_converter('DATETIME', convert_datetime)


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

    def set_local_coordinates(self, lat: float=None, lon: float=None) -> None:
        if None in (lat, lon):
            for rec in self.cache.get(self._T_DATA, r_type='organization'):
                if rec[1] == 'latitude':
                    lat = rec[2]
                elif rec[1] == 'longitude':
                    lon = rec[2]

        badidatetime.set_local_coordinates(lat, lon)

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
        Reads a row or rows from the config data table.

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
            print(f"IMPORTANT--fields: {fields}")
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
        Insert all values into the config data table.

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
                                            data: dict) -> int:
        """
        Insert values into the config data table.

        :param int year: A Baha'i year of the transaction.
        :param int month: A Baha'i month of the transaction. This is the order
                          of the Baha'i month not the name.
        :param dict data: The data from the any panel in the form of:
                          {<field_name>: <value>, ...}.
        :returns: The row count caused by the insert.
        :rtype: int
        """
        fy1 = await self.select_from_fiscal_year_table(current=1)

        if fy1:
            now = badidatetime.datetime.now(self.utc_tzinfo)
            f_items = await self.select_from_field_type_table(data)
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
                values.append({'value': data[field], 'fy1fk': fy1fk,
                               'fy2fk': fy2fk, 'mfk': mfk, 'ffk': pk,
                               'ctime': now, 'mtime': now})

            rowcount = await self._do_insert_query(query, values)
        else:
            self._log.error("No current fiscal_year data in the database.")
            rowcount = 0

        return rowcount

    async def update_config_data_table(self, data: list) -> int:
        """
        Update the config data table.

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

    async def select_from_monthly_table(self, year: int, year_month: tuple=None
                                        ) -> list:
        """
        Select values from the monthly table.

        :param int year: The fiscal year of the month needed.
        :param tuple year_month: The year and month of the calendar year.
        :returns: The data for the given month.
        :rtype: list

        .. note::

           The result is:
           [(pk, cal_year_month, participation, outstanding, coh, membership,
            '<treasurer>', locality, <ctime>, <mtime>, <year>, '<month name>',
             <month ordinal>), ...]
        """
        data = {'year': year}

        if year_month is None:
            where = ";"
        else:
            where = ", AND m.cal_year_month = :cal_year_month;"
            data.update({'cal_year_month': year_month})

        query = ("SELECT m.pk, fy.pk, m.cal_year_month, m.participation, "
                 "m.outstanding, m.coh, m.membership, m.treasurer, "
                 f"m.locality, m.ctime, m.mtime FROM {self._T_MONTHLY} AS m "
                 f"JOIN {self._T_FISCAL_YEAR} AS fy ON fy.pk = m.fyfk "
                 "WHERE fy.year = :year")
        return await self._do_select_query(query + where, data)

    async def insert_all_into_monthly_table(self, data: list) -> int:
        """
        Insert all data into the monthly table.

        :param list data: The data from the any panel  in the form of:
                          [(pk, fyfk, participation, outstanding, coh,
                            membership, treasurer, locality, ctime,
                            mtime), ...].
        """
        query = (f"INSERT INTO {self._T_MONTHLY} (pk, fyfk, cal_year_month, "
                 "participation, outstanding, coh, membership, treasurer, "
                 "locality, ctime, mtime) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);")
        return await self._do_insert_query(query, data)

    async def insert_into_monthly_table(self, year: int, data: dict) -> int:
        """
        Insert values in the monthly table.

        :param int year: The Badi year of the transaction.
        :param dict data: The data from any panel in the form of:
                          {'participation': <value>, ...}.
        :returns: The rowcount caused by the update.
        :rtype: int
        """
        now = badidatetime.datetime.now(self.utc_tzinfo)
        data['ctime'] = data['mtime'] = now
        fiscal = await self.select_from_fiscal_year_table(year=year)
        data['fyfk'] = fiscal[0]
        query = (f"INSERT INTO {self._T_MONTHLY} (fyfk, cal_year_month, "
                 "participation, outstanding, coh, membership, treasurer, "
                 "locality, ctime, mtime) VALUES (:fyfk, :cal_year_month, "
                 ":participation, :outstanding, :coh, :membership, "
                 ":treasurer, :locality, :ctime, :mtime);")
        return await self._do_insert_query(query, data)

    async def update_monthly_table(self, year: int, data: dict) -> int:
        """
        Update values in the monthly table.

        :param int year: A fiscal year of the transaction.
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
                 "mtime = :mtime "
                 f"JOIN {self._T_FISCAL_YEAR} AS fy ON fy.pk = m.fyfk "
                 "WHERE fy.year = :year AND "
                 "m.cal_year_month = :cal_year_month;")
        return await self._do_update_query(query, data)

    #
    # Miscellaneous methods and properties
    #

    def ordered_month(self) -> list:
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

    def today(self) -> badidatetime.date:
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
        """
        Get the UTC offset.

        :param str iana_key: The IANA key for the desired area.
        :returns: The UTC offset.
        :rtype: datetime.timedelta
        """
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

    def index_of_calendar_year(self, date: tuple, year: int=None) -> int:
        """
        Get the index of the calendar year.

        :param tuple date: The calendar date of the monthly record.
        :returns: The index of the calendar year in the fiscal year.
        :rtype: int
        """
        index = 0

        for idx, year, month, name in self.full_fiscal_year_data(year):
            if (year, month) == date:
                index = idx

        return index

    def full_fiscal_year_data(self, year: int=None) -> list:
        """
        Get all months in the current fiscal year.

        :returns: A list of data for the months in the fiscal year.
        :rtype: list
        """
        year_month = []
        year = self.cache.year if not year else year

        if year:
            fy0 = self.cache.get(self._T_FISCAL_YEAR, year=year)
            fy1 = self.cache.get(self._T_FISCAL_YEAR, year=year+1)

            if fy0 and fy1:
                year_month = self.fiscal_year_months(fy0[0], fy1[0])

        return year_month

    def fiscal_year_months(self, start_rec: tuple, end_rec: tuple) -> list:
        """
        Create a list of tuples that are in sequential order of the Badi
        calendar year and month for the entire fiscal year.

        :param tuple start_rec: A tuple of the fiscal year data.
        :param tuple end_rec: A tuple of the fiscal year data.
        :returns: A list of tuples of the year, ordinal, month name.
        :rtype: list

        .. note::

           Result assuming the fiscal year starts 183-03-05:
           [(0, 183, 3, 'Jamál'),
            (1, 183, 4, "'Aẓamat"),
            (2, 183, 5, 'Núr'),
            ...
            (18, 184, 1, 'Bahá'),
            (19, 184, 2, 'Jalál'),
            (20, 184, 3, 'Jamál')]
        """
        months = self.ordered_month()
        order = [o for m, o in months]
        next_month = {m: order[i + 1] for i, m in enumerate(order[:-1])}
        rank = {o: i for i, (m, o) in enumerate(months)}
        name = {o: m for m, o in months}

        def badi_ym_sequence(year, month):
            while True:
                yield (year, month)

                if month == 19:
                    year += 1
                    month = 1
                else:
                    month = next_month[month]

        end_key = (end_rec[1], rank[end_rec[2]])
        result = []

        for i, (y, o) in enumerate(badi_ym_sequence(start_rec[1],
                                                    start_rec[2])):
            if (y, rank[o]) > end_key:
                break

            result.append((i, y, o, name[o]))

        return result

    def populate_monthly_data(self, month_idx: int,  item: tuple,
                              data: dict={}) -> dict:
        # month_idx sets the dropdown to the current month.
        data['month_of_year'] = month_idx

        if item:
            data['participation'] = item[3]
            data['outstanding_bills'] = item[4]
            data['end_of_month_cash_on_hand'] = item[5]
            data['total_membership_this_month'] = item[6]
            data['treasurer_this_month'] = item[7]
            data['locality_prefix_month'] = item[8]
        else:
            data['participation'] = 0
            data['outstanding_bills'] = 0.0
            data['end_of_month_cash_on_hand'] = 0.0
            data['locality_prefix_month'] = 0

        if data['treasurer_this_month'] == "" and self._dp.organization_data:
            data['treasurer_this_month'] = self._dp.organization_data[
                'treasurer']
            data['total_membership_this_month'] = self._dp.organization_data[
                'total_membership']

        return data

    def convert_str_date(self, date_str: str) -> tuple:
        return tuple([int(d) for d in date_str.split(' ')[0].split('-')])
