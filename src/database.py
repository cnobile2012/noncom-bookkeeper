# -*- coding: utf-8 -*-
#
# src/database.py
#
__docformat__ = "restructuredtext en"

import time
import datetime as dtime
import copy
import wx

from .config import TomlMetaData
from .base_database import BaseDatabase

from zoneinfo import ZoneInfo
import badidatetime
badidatetime.enable_geocoder()


class Database(TomlMetaData, BaseDatabase):
    """
    Create, and update the database for the Bahá'í Bookkeeping application.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        BaseDatabase.__init__(self)

    def _ordered_month(self):
        """
        Numerically order Badí' months.

        :returns: A list of tuples in the form of
                  [(<month name>, <order>), ...]]
        :rtype: list
        """
        numbers = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
                   12, 13, 14, 15, 16, 17, 18, 0, 19)
        return [(month, numbers[idx])
                for idx, month in enumerate(badidatetime.MONTHNAMES)]

    async def populate_panels(self):
        """
        Populate all panels that have data in the database.
        """
        for name, panel in self._mf.panels.items():
            data = self._collect_panel_values(panel)
            await self._add_fields_to_field_type_table(data)
            await self._insert_into_month_table()
            dt = badidatetime.datetime.now(badidatetime.UTC, short=True)
            values = await self.select_from_data_table(data, dt.year, dt.month)

            if name == 'organization':
                self._update_organization_constants(values)

            self.populate_panel_values(name, panel, values)

    async def save_to_database(self, name: str, panel: wx.Panel) -> None:
        """
        Save the given panel data to the database.

        :param str name: The internal name of the current panal.
        :param wx.Panel panel: Any of the panels that have collected data.

        .. note::

           1. Empty organization data:
              {'locality_prefix': 0, 'locale_name': 'Harrnett',
               'total_membership': '', 'treasurer': '',
               'start_of_fiscal_year': '<today>',
               'location_city_name': ''}
        """
        data = self._collect_panel_values(panel)
        data_copy = copy.deepcopy(data)

        for field, value in data_copy.items():
            if value in self._EMPTY_FIELDS:
                msg = f"The '{field}' field must have data in it."
                self._log.warning(msg)
                self._mf.statusbar_warning = msg

            if name == 'organization' and self.config_type == 'bahai':
                location_city_name = data_copy['location_city_name']
                start_of_fiscal_year = data_copy['start_of_fiscal_year']

                if location_city_name:
                    iana, lat, lon = self._find_timezone(location_city_name)

                if start_of_fiscal_year:
                    if start_of_fiscal_year[10] in (' ', 'T'):
                        start_of_fiscal_year = start_of_fiscal_year[:10]

                    year = int(start_of_fiscal_year[:4])

                    if year > 1800:  # Must be a Gregorian date.
                        gdt = dtime.date.fromisoformat(start_of_fiscal_year)
                        bc = badidatetime.BahaiCalendar()
                        b_date = bc.badi_date_from_gregorian_date(
                            (gdt.year, gdt.month, gdt.day), short=True)[:3]
                        bdt = badidatetime.date(*b_date)
                        data['start_of_fiscal_year'] = bdt.isoformat()
                    else:
                        bdt = badidatetime.date.fromisoformat(
                            start_of_fiscal_year, short=True)
                        b_date = (bdt.year, bdt.month, bdt.day)

                # Create or update the current and next year.
                b_date += (1,)
                await self._insert_update_fiscal_year_table(b_date)
                next_date = (b_date[0]+1, b_date[1], b_date[2], 0)
                await self._insert_update_fiscal_year_table(next_date)
            else:
                bdt = badidatetime.datetime.now(badidatetime.UTC, short=True)
                b_date = bdt.b_date0

        await self._insert_update_data_table(b_date[0], b_date[1], data)
        panel.dirty = False

    async def select_from_fiscal_year_table(self, *, year: int=None,
                                            month: int=None, day: int=None,
                                            current: bool=None) -> list:
        """
        Select from the `fiscal_year` table. Only the year is needed to
        select the correct row of data.

        :param int year: The year is used to query if the `current`
                         argument is `None`.
        :param bool current: This will return the current fiscal year if
                             `True` or the next year if `False`. If set to
                             `None` (default) then do a query for the
                             provided year.
        :returns: A list of the `fiscal_year` table data for the year
                  requested.
        :rtype: list
        """
        assert (year, month, day, current).count(None) == 3, (
            "Can only query for one of (year, month, day, current)")

        if year:
            where = f"WHERE year={year}"
        elif month:
             where = f"WHERE month={month}"
        elif day:
            where = f"WHERE day={day}"
        else:
            where = f"WHERE current={int(current)}"

        query = (f"SELECT * FROM {self._T_FISCAL_YEAR} {where};")
        return await self._do_select_query(query)

    async def insert_into_fiscal_year_table(self, field_data: tuple) -> None:
        """
        Insert a row of data into the `fiscal_year` table.

        :param tuple field_data: This is the year, month, day, and current
                                 values (year, month, day, current).
        """
        now = badidatetime.datetime.now(badidatetime.UTC,
                                        short=True).isoformat()
        data = [field_data + (now, now),]
        query = (f"INSERT INTO {self._T_FISCAL_YEAR} (year, month, day, "
                 "current, c_time, m_time) VALUES (?, ?, ?, ?, ?, ?)")
        await self._do_insert_query(query, data)

    async def update_fiscal_year_table(self, year: int, current: int) -> None:
        """
        Update the `fiscal_year` table. Only the year and current values
        are needed to do updates.

        :param int year: The year indicating the start of the fiscal year.
        :param int current: The `current` field data.
        """
        now = badidatetime.datetime.now(badidatetime.UTC,
                                        short=True).isoformat()
        query = (f"UPDATE {self._T_FISCAL_YEAR} "
                 "SET current = :current, m_time = :m_time WHERE year = :year")
        data = [{'year': year, 'current': current, 'm_time': now}]
        await self._do_update_query(query, data)

    async def select_from_month_table(self, *, name: str=None, order: int=None
                                      ) -> list:
        """
        Select from the `month` table.
        """
        assert ((name and not order) or (not name and order)
                or (not name and not order)), (
                f"Cannot query for both the 'name' and 'order'.")

        if name:
            where = f"WHERE month={name}"
        elif order:
            where = f"WHERE ord={order}"
        else:
            where = ""

        query = (f"SELECT * FROM {self._T_MONTH} {where};")
        return await self._do_select_query(query)

    async def insert_into_month_table(self, field_data: list) -> None:
        """
        Insert into the `month` table.

        :param list month: A list of tuples where the tuple represents the
                           [(month, order), ...] used when transactions are
                           made.
        """
        now = badidatetime.datetime.now(badidatetime.UTC,
                                        short=True).isoformat()
        data = [data + (now, now) for data in field_data]
        query = (f"INSERT INTO {self._T_MONTH} (month, ord, c_time, m_time) "
                 "VALUES (?, ?, ?, ?)")
        await self._do_insert_query(query, data)

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
        now = badidatetime.datetime.now(badidatetime.UTC,
                                        short=True).isoformat()
        data = [(field, now, now) for field in fields]
        query = (f"INSERT INTO {self._T_FIELD_TYPE} (field, c_time, m_time) "
                 "VALUES (?, ?, ?)")
        await self._do_insert_query(query, data)

    async def select_from_data_table(self, data: dict, year: int=None,
                                     month: int=None,) -> list:
        """
        Reads a row or rows from the `data` table.

        :param int year: A Baha'i year used to select the current fiscal year.
        :param dict data: The data from the any panel in the form of:
                          {<field name>: <value>,...}.
        :param int month: A Baha'i month defined by the numeric designation.
                          Used to select the current month for the data.
        :returns: A list of rows from the Data table.
        :rtype: list

        .. note::

           Produces output as follows for the `organization` panel:
           [(1, 'locale_name', 'Some Community',
             '0182-02-12T05:26:40.963200+00:00',
             '0182-02-12T05:26:40.963200+00:00', 182, 183),
            (2, 'locality_prefix', 0,
             '0182-02-12T05:26:40.963200+00:00',
             '0182-02-12T05:26:40.963200+00:00', 182, 183),
            (3, 'location_city_name', 'Some City',
             '0182-02-12T05:27:17.251199+00:00',
             '0182-02-12T05:27:17.251199+00:00', 182, 183),
            (4, 'start_of_fiscal_year', '0182-02-19',
             '0182-02-12T05:27:17.251199+00:00',
             '0182-02-12T05:27:17.251199+00:00', 182, 183),
            (5, 'total_membership', '35',
             '0182-02-12T05:27:17.251199+00:00',
             '0182-02-12T05:27:17.251199+00:00', 182, 183),
            (6, 'treasurer', 'Joe Shmow',
             '0182-02-12T05:27:17.251199+00:00',
             '0182-02-12T05:27:17.251199+00:00', 182, 183)
           ]
        """
        fields = '", "'.join(data)

        if month:
            params = (year, year+1, month)
            query = (
                "SELECT d.pk, f.field, d.value, d.c_time, d.m_time, "
                "       y1.year, y2.year "
                f"FROM {self._T_DATA} AS d "
                f"JOIN {self._T_FIELD_TYPE} AS f ON f.pk = d.ffk "
                f"     AND f.field IN (\"{fields}\")"
                f"JOIN {self._T_FISCAL_YEAR} AS y1 ON y1.year = ?"
                f"JOIN {self._T_FISCAL_YEAR} AS y2 ON y2.year = ?"
                f"JOIN {self._T_MONTH} AS m ON m.pk = d.mfk AND m.ord = ?;"
                )
        else:
            params = ()
            query = (
                "SELECT d.pk, f.field, d.value, d.c_time, d.m_time, "
                f"FROM {self._T_DATA} AS d "
                f"JOIN {self._T_FIELD_TYPE} AS f ON f.pk = d.ffk "
                f"     AND f.field IN (\"{fields}\");"
                )

        return await self._do_select_query(query, params)

    async def insert_into_data_table(self, year: int, month: int, data: dict
                                     ) -> None:
        """
        Insert values into the Data table.

        :param int year: A Baha'i year of the transaction.
        :param int month: A Baha'i month of the transaction. This is the order
                          of the Baha'i month not the name.
        :param dict data: The data from the any panel  in the form of:
                          {<field name>: <value>,...}.
        """
        now = badidatetime.datetime.now(badidatetime.UTC,
                                        short=True).isoformat()
        f_items = await self.select_from_field_type_table(data)
        f_month = await self.select_from_month_table(order=month)
        fy1 = await self.select_from_fiscal_year_table(current=1)
        fy2 = await self.select_from_fiscal_year_table(year=fy1[0][1]+1)
        query = (
            f"INSERT INTO {self._T_DATA} (value, c_time, m_time, mfk, "
            "ffk, fy1fk, fy2fk) VALUES (:value, :c_time, :m_time, :mfk, "
            ":ffk, :fy1fk, :fy2fk);"
            )
        values = []

        for item in f_items:
            pk, field, c_time, m_time = item
            mfk = f_month[0][0]
            fy1fk = fy1[0][0]
            fy2fk = fy2[0][0]
            values.append({'value': data[field], 'c_time': now,
                           'm_time': now, 'mfk': mfk, 'ffk': pk,
                           'fy1fk': fy1fk, 'fy2fk': fy2fk})

        await self._do_insert_query(query, values)

    async def update_data_table(self, year: int, month: int, data: dict
                                ) -> None:
        """
        Update the `data` table.

        :param int year: A Baha'i year of the transaction.
        :param int month: A Baha'i month of the transaction. This is the order
                          of the Baha'i month not the name.
        :param dict data: The data from the any panel  in the form of:
                          {<field name>: (pk, <value>),...}.
        """
        m_time = badidatetime.datetime.now(badidatetime.UTC,
                                           short=True).isoformat()
        query = (f"UPDATE {self._T_DATA} SET value = :value, "
                 "m_time = :m_time WHERE pk = :pk;")
        values = []

        for field, (pk, value) in data.items():
            values.append((value, m_time, pk))

        await self._do_update_query(query, values)

    def _convert_date_to_yymmdd(self, value):
        """
        Converts the ISO date string to a tiple contaning the
        (year, month, day).

        :param str value: A ISO formatting date string.
        """
        return badidatetime.date.fromisoformat(value, short=True).b_date
