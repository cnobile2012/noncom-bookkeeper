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

    async def select_from_fiscal_year_table(self, *, year: int=None,
                                            month: int=None, day: int=None,
                                            current: int=None,
                                            work_on: int=None, audit: int=None
                                            ) -> list:
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
        :param int work_on: The `work_on` is used to switch the fiscal year
                            that is being worked on..
        :param int audit: The `audit` is used to query all years audited or
                          not audited.
        :returns: The `fiscal_year` table data for the year requested.
        :rtype: list
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
        else:          # Get all fiscal years.
            where = ""

        query = (f"SELECT * FROM {self._T_FISCAL_YEAR} {where};")
        data = await self._do_select_query(query)
        return data[0] if len(data) == 1 else data

    async def insert_into_fiscal_year_table(self, data: list) -> int:
        """
        Insert a row of data into the `fiscal_year` table.

        :param list data: The data to be inserted.
        :returns: The row count caused by the insert.
        :rtype: int
        """
        now = badidatetime.datetime.now(self.utc_tzinfo, short=True)
        items = [t + (now, now) for t in data]  # Add the times to the end.
        query = (f"INSERT INTO {self._T_FISCAL_YEAR} (year, month, day, "
                 "current, work_on, audit, ctime, mtime) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?, ?);")
        return await self._do_insert_query(query, items)

    async def update_fiscal_year_table(self, data: list) -> int:
        """
        Update the `fiscal_year` table. Only the year and current values
        are needed to do updates.

        :param list data: The data to be updated.
        :returns: The row count caused by the update.
        :rtype: int

        .. note::

           Incoming data:
           From the fiscal year table:
           [(year, month, day, current, work_on, audit, current), ...]
           From the fiscal panel:
           [(current_fiscal_year, work_on_this_fiscal_year,
             audit_complete), ...]
        """
        now = badidatetime.datetime.now(self.utc_tzinfo, short=True)
        query = (f"UPDATE {self._T_FISCAL_YEAR} "
                 "SET current = :current, work_on = :work_on, audit = :audit, "
                 "mtime = :mtime WHERE year = :year;")
        items = [{'year': item[0], 'current': item[3], 'work_on': item[4],
                  'audit': item[5], 'mtime': now} for item in data]
        return await self._do_update_query(query, items)

    #
    # Month SELECT and INSERT methods.
    #

    async def select_from_month_table(self, *, name: str=None, order: int=None
                                      ) -> list:
        """
        Select from the `month` table.
        """
        assert ((name and not order) or (not name and order)
                or (not name and not order)), (
                "Cannot query for both the 'name' and 'order'.")

        if name:
            where = f"WHERE month={name}"
        elif order:
            where = f"WHERE ord={order}"
        else:
            where = ""

        query = (f"SELECT * FROM {self._T_MONTH} {where};")
        data = await self._do_select_query(query)
        return data[0] if len(data) == 1 else data

    async def insert_into_month_table(self, months: dict) -> int:
        """
        Insert into the `month` table.

        :param list months: A dict where the key is the order of the month
                            and the value is the month name.
        :returns: The row count caused by the insert.
        :rtype: int
        """
        now = badidatetime.datetime.now(self.utc_tzinfo, short=True)
        data = [(name, order, now) for order, name in months.items()]
        query = (f"INSERT INTO {self._T_MONTH} (month, ord, ctime) "
                 "VALUES (?, ?, ?);")
        return await self._do_insert_query(query, data)

    #
    # Field Names SELECT, INSERT and, UPDATE methods.
    #

    async def select_from_field_type_table(self, data: dict) -> list:
        """
        Select from the field_type table.

        :param dict data: The data from the Organization Information panel in
                          the form of: {<field name>: <value>,...}.
        :returns: The values read from the FieldType table in the form of
                  [(<pk>, <field>, <rids>, <ctime>, <mtime>), ...].
        :rtype: list of tuples
        """
        assert data, f"There must be valid data, found '{data}'."
        fields = '", "'.join(data)
        query = (f'SELECT * FROM {self._T_FIELD_TYPE} WHERE field IN '
                 f'("{fields}");')
        return await self._do_select_query(query)

    async def insert_into_field_type_table(self, fields: set) -> int:
        """
        Insert fields into the field_type table.

        :param set fields: The fields from any panel in the form of:
                           {<field name>,...}.
        :returns: The row count caused by the insert.
        :rtype: int
        """
        now = badidatetime.datetime.now(self.utc_tzinfo, short=True)
        data = [(field, now, now) for field in fields]
        query = (f"INSERT INTO {self._T_FIELD_TYPE} (field, ctime, mtime) "
                 "VALUES (?, ?, ?);")
        return await self._do_insert_query(query, data)

    #
    # Data SELECT, INSERT and, UPDATE methods.
    #

    async def select_from_config_data_table(self, data: dict, year: int=None
                                            ) -> list:
        """
        Reads a row or rows from the `data` table.

        :param int year: A Baha'i year used to select the current fiscal year.
        :param dict data: The data from the any panel in the form of:
                          {<field name>: <value>,...}.
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
        field_names = list(data.keys())
        fields = '", "'.join(field_names)

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
        else:
            params = ()
            query = (
                "SELECT d.pk, f.field, d.value, d.ctime, d.mtime "
                f"FROM {self._T_DATA} AS d "
                f"JOIN {self._T_FIELD_TYPE} AS f ON f.pk = d.ffk "
                f"     AND f.field IN (\"{fields}\");"
                )

        return await self._do_select_query(query, params)

    async def insert_into_config_data_table(self, year: int, month: int,
                                            data: dict) -> int:
        """
        Insert values into the Data table.

        :param int year: A Baha'i year of the transaction.
        :param int month: A Baha'i month of the transaction. This is the order
                          of the Baha'i month not the name.
        :param dict data: The data from the any panel  in the form of:
                          {<field name>: <value>,...}.
        :returns: The row count caused by the insert.
        :rtype: int

        .. note::

           Incoming data:
           {<field_name>: value, ...}
        """
        fy1 = await self.select_from_fiscal_year_table(current=1)

        if fy1:
            now = badidatetime.datetime.now(self.utc_tzinfo, short=True)
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

    async def update_config_data_table(self, year: int, month: int, data: list
                                       ) -> int:
        """
        Update the `data` table.

        :param int year: A Baha'i year of the transaction.
        :param int month: A Baha'i month of the transaction. This is the order
                          of the Baha'i month not the name.
        :param list data: The data from the any panel  in the form of:
                          [(pk, <value>), ...}.
        :returns: The row count caused by the update.
        :rtype: int

        .. note::

           Incoming data:
           {pk: value, <field_name>: value, ...}
        """
        mtime = badidatetime.datetime.now(self.utc_tzinfo, short=True)
        query = (f"UPDATE {self._T_DATA} SET value = :value, "
                 "mtime = :mtime WHERE pk = :pk;")
        items = [{'pk': pk, 'value': value, 'mtime': mtime}
                 for pk, value in data]
        return await self._do_update_query(query, items)

    async def select_from_monthly_table(self, year: int=None, month: int=None
                                        ) -> list:
        """
        Select values from the monthly table.

        :param int year: The year of the month needed.
        :param int month: The numeric value of the month.
        :returns: The date for the given month.
        :rtype: list
        """
        query = (f"SELECT m.* FROM {self._T_MONTHLY} m "
                 f"JOIN {self._T_MONTHLY_PIVOT} mp ON mp.mlfk = m.pk "
                 f"JOIN {self._T_MONTH} mo ON mo.pk = mp.mfk "
                 f"JOIN {self._T_FISCAL_YEAR} fy ON fy.pk = mp.fyfk "
                 "WHERE mo.month = :month AND fy.year = :year;")
        data = {'year': year, 'month': month}
        return await self._do_select_query(query, data)

    async def insert_into_monthly_table(self, year: int, data: dict) -> int:
        """
        Insert values into the monthly table.

        :param int year: A Baha'i year of the transaction.
        :param list data: The data from the any panel  in the form of:
                          [(pk, <value>), ...}.
        :returns: The row count caused by the update.
        :rtype: int
        """
        # Data for the monthly table.
        now = badidatetime.datetime.now(self.utc_tzinfo, short=True)
        data['ctime'] = data['mtime'] = now
        # Data for the monthly_pivot table.
        month = data.pop('month')
        data['mfk'] = (await self.select_from_month_table(order=month))[0]
        fiscal = await self.select_from_fiscal_year_table(year=year)
        data['fyfk'] = fiscal[0]
        query = (f"WITH new_monthly AS (INSERT INTO {self._T_MONTHLY} ("
                 "participation, outstanding, coh, membership, treasurer, "
                 "locality, ctime, mtime)"
                 "VALUES (:participation, :outstanding, :coh, :membership,"
                 " :treasurer, :locality, :ctime, :mtime) RETURNING id) "
                 f"INSERT INTO {self._T_MONTHLY_PIVOT} (mfk, fyfk, mlfk) "
                 "SELECT :mfk, :fyfk, id FROM new_monthly;")
        print('POOP', query, data)
        return await self._do_insert_query(query, data)

    async def update_monthly_table(self, year: int, month: int, data: list
                                   ) -> int:
        pass

    #
    # Miscellaneous methods and properties
    #

    def _ordered_month(self):
        """
        Provides the order of the Badi months from the custom_widgets module.
        Called in the BaseBatabase class.
        """
        return ordered_month()

    def _convert_date_to_yymmdd(self, value: str) -> badidatetime.date:
        """
        Converts the ISO date string to an instance of 'badidatetime.date'.

        :param str value: A ISO formatting date string.
        :returns: An instance of 'badidatetime.date'.
        :rtype: badidatetime.date
        """
        return badidatetime.date.fromisoformat(value, short=True)

    def _ymd_from_iso(self, iso: str) -> tuple:
        """
        Convert the ISO string to (year, month, day).

        :param str iso: The ISO date string.
        :returns: The year, month, and day from an ISO string.
        :rtype: tuple
        """
        return badidatetime.date.fromisoformat(iso, short=True).b_date

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
