# -*- coding: utf-8 -*-
#
# src/bahai_database.py
#
__docformat__ = "restructuredtext en"

from .base_database import BaseDatabase
from .custom_widgits import ordered_month

import badidatetime
badidatetime.enable_geocoder()


class Database(BaseDatabase):
    """
    Create, and update the database for the Bahá'í Bookkeeping application.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #BaseDatabase.__init__(self)

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

        if year:       # Get just the one year.
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
        return await self._do_select_query(query)

    async def insert_into_fiscal_year_table(self, data: list) -> None:
        """
        Insert a row of data into the `fiscal_year` table.

        :param list data: The data to be inserted.
        """
        now = badidatetime.datetime.now(self.tzinfo, short=True).isoformat()
        items = [t + (now, now) for t in data]  # Add the times to the end.
        query = (f"INSERT INTO {self._T_FISCAL_YEAR} (year, month, day, "
                 "current, work_on, audit, c_time, m_time) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
        await self._do_insert_query(query, items)

    async def update_fiscal_year_table(self, data: list) -> None:
        """
        Update the `fiscal_year` table. Only the year and current values
        are needed to do updates.

        :param list data: The data to be updated.

        .. note::

           Incoming data:
           From the fiscal year table:
           [(year, month, day, current, work_on, audit, current), ...]
           From the fiscal panel:
           [(current_fiscal_year, work_on_this_fiscal_year,
             audit_complete), ...]
        """
        now = badidatetime.datetime.now(self.tzinfo, short=True).isoformat()
        query = (f"UPDATE {self._T_FISCAL_YEAR} "
                 "SET current = :current, work_on = :work_on, audit = :audit, "
                 "m_time = :m_time WHERE year = :year")
        items = [{'year': item[0], 'current': item[3], 'work_on': item[4],
                  'audit': item[5], 'm_time': now} for item in data]
        await self._do_update_query(query, items)

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

        query = (f"SELECT * FROM {self._T_MONTH} {where}")
        return await self._do_select_query(query)

    async def insert_into_month_table(self, months: dict) -> None:
        """
        Insert into the `month` table.

        :param list months: A dict where the key is the order of the month
                            and the value is the month name.
        """
        now = badidatetime.datetime.now(self.tzinfo, short=True).isoformat()
        data = [(name, order, now, now) for order, name in months.items()]
        query = (f"INSERT INTO {self._T_MONTH} (month, ord, c_time, m_time) "
                 "VALUES (?, ?, ?, ?)")
        await self._do_insert_query(query, data)

    #
    # Field Names SELECT, INSERT and, UPDATE methods.
    #

    async def select_from_field_type_table(self, data: dict) -> list:
        """
        Select from the field_type table.

        :param dict data: The data from the Organization Information panel in
                          the form of: {<field name>: <value>,...}.
        :returns: The values read from the FieldType table in the form of
                  [(<pk>, <field>, <rids>, <c_time>, <m_time>), ...].
        :rtype: list of tuples
        """
        assert data, f"There must be valid data, found '{data}'."
        fields = '", "'.join(data)
        query = (f'SELECT * FROM {self._T_FIELD_TYPE} WHERE field IN '
                 f'("{fields}");')
        return await self._do_select_query(query)

    async def insert_into_field_type_table(self, fields: set) -> None:
        """
        Insert fields into the field_type table.

        :param set fields: The fields from any panel in the form of:
                           {<field name>,...}.
        """
        now = badidatetime.datetime.now(self.tzinfo, short=True).isoformat()
        data = [(field, now, now) for field in fields]
        query = (f"INSERT INTO {self._T_FIELD_TYPE} (field, c_time, m_time) "
                 "VALUES (?, ?, ?)")
        await self._do_insert_query(query, data)

    #
    # Data SELECT, INSERT and, UPDATE methods.
    #

    async def select_from_data_table(self, data: dict, year: int=None) -> list:
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
                "       d.c_time, d.m_time "
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
                "SELECT d.pk, f.field, d.value, d.c_time, d.m_time "
                f"FROM {self._T_DATA} AS d "
                f"JOIN {self._T_FIELD_TYPE} AS f ON f.pk = d.ffk "
                f"     AND f.field IN (\"{fields}\");"
                )

        return await self._do_select_query(query, params)

    async def insert_into_data_table(self, year: int, month: int, data: dict
                                     ) -> None:
        """
        Insert values into the Data table.

        .. note::

           Incoming data:
           {<field_name>: value, ...}

        :param int year: A Baha'i year of the transaction.
        :param int month: A Baha'i month of the transaction. This is the order
                          of the Baha'i month not the name.
        :param dict data: The data from the any panel  in the form of:
                          {<field name>: <value>,...}.
        """
        fy1 = await self.select_from_fiscal_year_table(current=1)

        if fy1:
            now = badidatetime.datetime.now(self.tzinfo,
                                            short=True).isoformat()
            f_items = await self.select_from_field_type_table(data)
            f_month = await self.select_from_month_table(order=month)
            fy2 = await self.select_from_fiscal_year_table(year=fy1[0][1]+1)

            query = (
                f"INSERT INTO {self._T_DATA} (value, fy1fk, fy2fk, mfk, ffk, "
                "c_time, m_time) VALUES (:value, :fy1fk, :fy2fk, :mfk, :ffk, "
                ":c_time, :m_time);"
                )
            values = []

            for item in f_items:
                pk, field, c_time, m_time = item
                mfk = f_month[0][0]
                fy1fk = fy1[0][0]  # We want the FK not the year.
                fy2fk = fy2[0][0]  # We want the FK not the year.
                values.append({'value': data[field], 'fy1fk': fy1fk,
                               'fy2fk': fy2fk, 'mfk': mfk, 'ffk': pk,
                               'c_time': now, 'm_time': now})

            await self._do_insert_query(query, values)
        else:
            self._log.error("No current fiscal_year data in the database.")

    async def update_data_table(self, year: int, month: int, data: list
                                ) -> None:
        """
        Update the `data` table.

        .. note::

           Incoming data:
           {pk: value, <field_name>: value, ...}

        :param int year: A Baha'i year of the transaction.
        :param int month: A Baha'i month of the transaction. This is the order
                          of the Baha'i month not the name.
        :param list data: The data from the any panel  in the form of:
                          [(pk, <value>), ...}.
        """
        m_time = badidatetime.datetime.now(self.tzinfo, short=True).isoformat()
        query = (f"UPDATE {self._T_DATA} SET value = :value, "
                 "m_time = :m_time WHERE pk = :pk;")
        values = [(value, m_time, pk) for pk, value in data]
        await self._do_update_query(query, values)

    #
    # Miscellaneous methods
    #

    def _ordered_month(self):
        """
        Provides the order of the Badi months from the custom_widgets module.
        Called in the BaseBatabase class.
        """
        return ordered_month()

    def _convert_date_to_yymmdd(self, value):
        """
        Converts the ISO date string to a tuple containing the
        (year, month, day).

        :param str value: A ISO formatting date string.
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
