# -*- coding: utf-8 -*-
#
# src/bahai_database.py
#
__docformat__ = "restructuredtext en"

import wx

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
        BaseDatabase.__init__(self)
        self._fiscal_data = None

    def _ordered_month(self):
        return ordered_month()

    async def populate_panels(self):
        """
        Populate all panels that have data in the database.
        """
        year, month = await self._get_current_fiscal_year()

        if None not in (year, month):
            self._fiscal_data = await self.select_from_fiscal_year_table()

            for name, panel in self._mf.panels.items():
                data = self._collect_panel_values(panel)
                values = await self.select_from_data_table(name, data, year,
                                                           month)

                # Needed when the app has been run at least one time before.
                if name == 'organization' and values:
                    self.organization_data = values

                # Add any new fields to the database.
                await self._add_fields_to_field_type_table(data)
                panel.initializing = True
                self.populate_panel_values(name, panel, values)
                panel.initializing = False

    async def save_to_database(self, name: str, panel: wx.Panel) -> None:
        """
        Save the given panel data to the database.

        :param str name: The internal name of the current panel.
        :param wx.Panel panel: Any of the panels that have collected data.
        :returns: None if no errors, otherwise the error message.
        :rtype: None or str

        .. note::

           1. Empty (default) organization data:
              {'locality_prefix': 0, 'locale_name': '',
               'total_membership': '', 'treasurer': '',
               'start_of_fiscal_year': '<today>',
               'location_city_name': ''}
        """
        error = None
        data = self._collect_panel_values(panel)
        # Make sure all fields were entered.
        empty_list = [field for field, value in data.items()
                      if value in self._EMPTY_FIELDS]

        if len(empty_list) != 0:
            ef = ', '.join([f for f in empty_list])
            error = f"The '{ef}' field(s) must not be empty."
            self._log.warning(error)
        else:
            year, month = await self._get_current_fiscal_year()
            seq_flag = False

            if name == 'organization':
                data = self._add_location_data(data)
                start_of_fiscal_year = data['start_of_fiscal_year']
                entered_date = start_of_fiscal_year.b_date
                # Need ISO date for the DB.
                data['start_of_fiscal_year'] = start_of_fiscal_year.isoformat()

                if not year or not month:            # First ever entry
                    self.organization_data = data
                    await self.first_run_initialization(entered_date)
                    year, month, day = entered_date
                elif (year + 1) == entered_date[0]:  # Next Current Year
                    self.organization_data = data
                    await self.entered_next_year(entered_date)
                    year, month, day = entered_date
                elif (year - 1) == entered_date[0]:  # Previous year.
                    await self.entered_previous_year(entered_date)
                    year, month, day = entered_date
                else:
                    year = month = None
                    seq_flag = True
                    error = ("Cannot enter a year that is not sequentially "
                             "before or after the current year.")

            if year and month:
                await self.populate_panels()
                await self._insert_update_data_table(name, year, month, data)
            elif seq_flag:
                self._log.warning(error)
            else:  # If no org data was entered.
                error = ("Cannot enter Fiscal Year data before the "
                         "Organization Information has been entered.")
                self._log.warning(error)

        return error

    async def first_run_initialization(self, date: tuple):
        """
        The first run of the application.

        :param tuple date: This is the UI entered date.
        """
        year, month, day = date
        # year, month, day, current, audit, work_on
        data = [(year, month, day, 1, 1, 0), (year+1, month, day, 0, 0, 0)]
        await self.insert_into_fiscal_year_table(data)
        # Populate the Badí months in the database.
        await self._insert_into_month_table()

        # Populate all panel fields in the database.
        for name, panel in self._mf.panels.items():
            panel_data = self._collect_panel_values(panel)
            await self._add_fields_to_field_type_table(panel_data)

    async def entered_next_year(self, date: tuple):
        """
        Follow up years.

        .. note::

           1. Update the previous current year.
           2. Update the previous next year to the current year.
           3. Insert a new next year.

        :param tuple date: This is the UI entered date.
        """
        year, month, day = date
        data = [(year-1, month, day, 0, 0, 0), (year, month, day, 1, 1, 0)]
        await self.update_fiscal_year_table(data)
        await self.insert_into_fiscal_year_table(
            [(year+1, month, day, 0, 0, 0)])

    async def entered_previous_year(self, date: tuple):
        """
        Previous up years.

        :param tuple date: This is the UI entered date.
        """
        year, month, day = date
        await self.insert_into_fiscal_year_table([(year, month, day, 0, 0, 0)])

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

        :param dict data: The data to be updated.

        .. note::

           Incoming data:
           [(year, month, day, current, work_on, audit, current), ...]
        """
        now = badidatetime.datetime.now(self.tzinfo, short=True).isoformat()
        query = (f"UPDATE {self._T_FISCAL_YEAR} "
                 "SET current = :current, audit = :audit, work_on = :work_on "
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

        query = (f"SELECT * FROM {self._T_MONTH} {where};")
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

    async def select_from_data_table(self, name: str, data: dict,
                                     year: int=None, month: int=None,) -> list:
        """
        Reads a row or rows from the `data` table.

        :param str name: Panel name.
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
        field_names = list(data.keys())

        if name == 'fiscal':
            fields = '", "'.join([f"y1.{fn}" for fn in field_names])
        else:
            fields = '", "'.join(field_names)

        if month:
            params = (year, year+1, month)
            query = (
                "SELECT d.pk, f.field, d.value, y1.year, y2.year, "
                "       d.c_time, d.m_time "
                f"FROM {self._T_DATA} AS d "
                f"JOIN {self._T_FIELD_TYPE} AS f ON f.pk = d.ffk "
                f"     AND f.field IN (\"{fields}\") "
                f"JOIN {self._T_FISCAL_YEAR} AS y1 ON y1.year = ? "
                f"JOIN {self._T_FISCAL_YEAR} AS y2 ON y2.year = ? "
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
        f_items = await self.select_from_field_type_table(data)
        f_month = await self.select_from_month_table(order=month)
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
        m_time = badidatetime.datetime.now(self.tzinfo, short=True).isoformat()
        query = (f"UPDATE {self._T_DATA} SET value = :value, "
                 "m_time = :m_time WHERE pk = :pk;")
        values = []

        for field, (pk, value) in data.items():
            values.append((value, m_time, pk))

        await self._do_update_query(query, values)

    #
    # Miscellaneous methods
    #

    def _convert_date_to_yymmdd(self, value):
        """
        Converts the ISO date string to a tuple containing the
        (year, month, day).

        :param str value: A ISO formatting date string.
        """
        return badidatetime.date.fromisoformat(value, short=True)

    async def _get_current_fiscal_year(self):
        """
        Get the current fiscal year.
        """
        fy = await self.select_from_fiscal_year_table(current=1)

        if len(fy):
            year = fy[0][1]
            month = fy[0][2]
        else:  # Only for first time use.
            year = month = None

        return year, month

    def _add_location_data(self, data: dict) -> dict:
        """
        Add the location data `iana_name`, `latitude` and, `longitude` to
        the organization data.

        :param dict data: The `organization` data.
        :returns: The updated `organization` data.
        :rtype: dict
        """
        location_city_name = data['location_city_name']

        if location_city_name:
            iana, lat, lon = self._find_timezone(location_city_name)
            data['iana_name'] = iana
            data['latitude'] = lat
            data['longitude'] = lon
        else:
            self._log.warning("The 'location_city_name' field was not found, "
                              "this will cause some dates to be set to the "
                              "wrong timezone, most likely UTC:00:00.")
            data = None

        return data
