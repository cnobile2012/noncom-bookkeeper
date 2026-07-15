# -*- coding: utf-8 -*-
#
# src/preperation.py
#
__docformat__ = "restructuredtext en"

import logging

from geopy.geocoders import Nominatim
from geopy import exc
from timezonefinder import TimezoneFinder

from .config import TomlAppConfig


class DataPreperation:
    """
    All data in the data and fiscal_year tables need to prepared before
    cached or saved to the database.
    """
    _EXCLUDE_PANELS = ('fiscal', 'monthly')

    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tac = TomlAppConfig()
        self._log = logging.getLogger(self._tac.logger_name)
        self.db = db

    async def organization(self, data: dict, f_year: int, f_month: int
                           ) -> str | None:
        """
        Insert or update the organization data.

        :param dict data: The data to insert or update.
        :param int f_year: The fiscal year.
        :param int f_month: The month that the fiscal year starts.
        :returns: An error message or None.
        :rtype: str or None
        """
        error = None

        if data:
            error = self._empty_fields('organization', data)

            if not error:
                data, error = self._add_location_data(data)

                if data:  # Adding location can have errors.
                    sofy = data['start_of_fiscal_year']
                    p_year = sofy.year
                    p_month = sofy.month
                    p_day = sofy.day
                    # Need ISO date for the DB.
                    data['start_of_fiscal_year'] = sofy.isoformat()
                    earliest_fy = self._earliest_fiscal_year
                    latest_fy = self._latest_fiscal_year

                    if None in (f_year, f_month):
                        await self._first_run_initialization(
                            p_year, p_month, p_day)
                        f_year = p_year
                        f_month = p_month
                    elif earliest_fy and (earliest_fy - 1) == p_year:
                        await self._enter_previous_year(
                            p_year, p_month, p_day)
                    elif latest_fy and latest_fy == p_year:
                        await self._enter_next_year(p_year, p_month, p_day)
                    elif f_year == p_year:  # This is an update
                        pass
                    else:
                        error = ("Cannot enter a year that is not immediately "
                                 "before or after the earliest or latest "
                                 f"year. Found {p_year} with earliest: "
                                 f"{earliest_fy}, and latest: {latest_fy}.")
                        self._log.warning(error)

                    if not error:
                        error, rc = (
                            await self._insert_update_config_data_table(
                                f_year, month=f_month, r_type='organization',
                                data=data))
        else:
            # If no organization data was entered.
            error = ("Organization Information data must be entered before "
                    "any other data can be entered.")

        error and self._log.warning(error)
        return error

    async def budget(self, data: dict, f_year: int, f_month: int
                     ) -> str | None:
        """
        Converts panel data to data appropreate for updating the budget data
        in the config data table, then update it.

        :param dict data: Panel data.
        :param int f_year: The current fiscal year.
        :param int f_month: The current fiscal year month.
        :returns: Any errors or None.
        :rtype: str or None
        """
        error = None

        if f_year and f_month:
            error = self._empty_fields('budget', data)

            if not error:
                error, rowcount = await self._insert_update_config_data_table(
                    f_year, month=f_month, r_type='budget', data=data)
                self._log.debug("Inserted or updated %s row(s) of "
                                "budget data.", rowcount)

            error and self._log.warning(error)

        return error

    async def monthly(self, data: dict, year: int) -> str | None:
        """
        Inserts or updates panel data.

        :param dict data: Panel data.
        :param int year: The current fiscal year.
        :returns: Any errors or None with no errors.
        :rtype: str or None
        """
        if data:
            error = self._empty_fields('monthly', data)

            if not error:
                # empty_fields = []
                mapping = {field: self.db.MONTHLY_FIELD_MAP.get(
                    field, 'unknown') for field in data}
                items = {mapping[field]: val for field, val in data.items()}
                date = self.db.convert_str_date(data['month_index'])
                items['cal_year_month'] = date
                record = ()

                for value in self.db.cache.get(self.db._T_MONTHLY, year=year):
                    if value[2] == date:
                        record = value
                        break

                if record:
                    values = {'year': year, 'data': items}
                    rowcount = await self.db.cache.update(
                        self.db._T_MONTHLY, values)
                    self._log.info("Updated %s table data: %s.",
                                self.db._T_MONTHLY, values)
                else:
                    values = {'year': year, 'data': items}
                    rowcount = await self.db.cache.insert(
                        self.db._T_MONTHLY, values)
                    self._log.info("Inserted %s table data: %s.",
                                self.db._T_MONTHLY, values)

        return error

    async def fiscal(self, data: dict, date: tuple) -> str | None:
        """
        Converts panel data to data appropreate for updating the fiscal year
        table in the database, then update it.

        :param dict data: Panel data.
        :param tuple date: The current fiscal year date.
        :returns: Any errors or None with no errors.
        :rtype: str or None
        """
        error = None

        if data:
            items = [(*date, data['current_fiscal_year'],
                      data['work_on_this_fiscal_year'],
                      data['audit_complete'])]
            values = {'year': date[0], 'data': items}
            rowcount = await self.db.cache.update(self.db._T_FISCAL_YEAR,
                                                  {'data': items})
            self._log.debug("Updated %s row(s) of fiscal year data.", rowcount)

            if rowcount != 1:
                error = "Failed to update any fiscal year data."
        else:
            error = "No data submitted."

        error and self._log.error(error)
        return error

    async def ledger(self, data: dict, date: tuple) -> str | None:
        """
        Inserts and updates ledger data.

        :param dict data: Panel data.
        :param tuple date: The current fiscal year date.
        :returns: Any errors or None with no errors.
        :rtype: str or None
        """
        pass

    def _empty_fields(self, panel_name: str, data: dict) -> str | None:
        """
        Find the fields that are mandatory then create an error report.

        :param str: panel_name: The name of the panel.
        :param dict data: The date to check.
        :returns: The error report.
        :rtype: str or None
        """
        error = None
        mandatory = []

        for w0, w1 in self.db.find_child_sets(self.db._mf.panels[panel_name]):
            if hasattr(w0[2], 'mandatory') and w0[2].mandatory:
                mandatory.append(w0[1])
            elif w1 and hasattr(w1[2], 'mandatory') and w1[2].mandatory:
                mandatory.append(w0[1])

        empty_fields = [field for field, value in data.items()
                        if value == '' and field in mandatory]

        if len(empty_fields) != 0:
            ef = ', '.join([f for f in empty_fields])
            error = f"The '{ef}' field(s) must not be empty."

        return error

    async def _first_run_initialization(self, year: int, month: int, day: int):
        """
        The first run of the application.

        .. note::

           1. Insert a fiscal year marked as current.
           2. Insert the next fiscal year.
           3. Insert all months.
           4. Insert fields from all current panels.

        :param int year: This is the UI entered year.
        :param int month: This is the UI entered month.
        :param int day: This is the UI entered day.
        """
        # year, month, day, current, audit, work_on
        data = {'data': [(year, month, day, 1, 1, 0),
                         (year+1, month, day, 0, 0, 0)]}
        await self.db.cache.insert(self.db._T_FISCAL_YEAR, data)
        # Populate the Badí months in the database.
        data = {'data': self.db.ordered_month()}
        await self.db.cache.insert(self.db._T_MONTH, data)

        # Populate all panel fields in the database.
        for name, panel in self.db._mf.panels.items():
            if name in self._EXCLUDE_PANELS: continue
            panel_data = self.db.collect_panel_values(panel)
            await self.db._add_fields_to_field_type_table(panel_data)

    async def _enter_next_year(self, year: int, month: int, day: int) -> int:
        """
        Update the current fiscal year to be the previous fiscal year then
        updated the following year to be the current fiscal year then inserted
        the next fiscal year.

        .. note::

           1. Update the previous current year making it not current.
           2. Update the previous next year to the current year.
           3. Insert a new next year.

        :param int year: This is the UI entered year.
        :param int month: This is the UI entered month.
        :param int day: This is the UI entered day.
        :returns: The number of DB rows affected.
        :rtype: int
        """
        rowcount = await self.db.cache.update(
            self.db._T_FISCAL_YEAR, {'data': [(year-1, month, day, 0, 0, 0),
                                              (year, month, day, 1, 1, 0)]})
        rowcount += await self.db.cache.insert(
            self.db._T_FISCAL_YEAR, {'data': [(year+1, month, day, 0, 0, 0)]})
        return rowcount

    async def _enter_previous_year(self, year: int, month: int, day: int
                                   ) -> int:
        """
        Enter the next year.

        :param int year: This is the UI entered year.
        :param int month: This is the UI entered month.
        :param int day: This is the UI entered day.
        :returns: The number of DB rows affected.
        :rtype: int
        """
        return await self.db.cache.insert(
            self.db._T_FISCAL_YEAR, {'data': [(year, month, day, 0, 0, 0)]})

    def _add_location_data(self, data: dict) -> tuple:
        """
        Add the location data `iana_name`, `latitude` and, `longitude` to
        the organization data.

        :param dict data: The `organization` data.
        :returns: The updated `organization` data and any error that may
                  have happened.
        :rtype: tuple

        .. note::

           Organization data structure:
           {'iana_name': 'America/New_York', 'latitude': '<your latutude>',
            'locale_name': '<your locale>', 'locality_prefix': '0',
            'location_city_name': '<your city name>',
            'longitude': '<your longitude>',
            'start_of_fiscal_year': '0183-03-05', 'total_membership': '20',
            'treasurer': '<your treasurer>'}
        """
        location_city_name = data['location_city_name']

        if location_city_name:
            iana, lat, lon, error = self._find_timezone(location_city_name)

            if error is None:
                data['iana_name'] = iana
                data['latitude'] = lat
                data['longitude'] = lon
                # This makes badidatetime happy.
                self.db.set_local_coordinates(lat, lon)
            else:
                data = None
        else:
            error = ("The 'location_city_name' field was not found, this "
                     "will cause some dates to be set to the wrong timezone, "
                     "most likely to UTC:00:00.")
            data = None

        return data, error

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
        except exc.GeocoderError as e:  # pragma: no cover
            error = f"Could not get information on {address}"
            self._log.error(error + ", %s", e)
        else:
            error = None

        if location:
            lat = location.latitude
            lon = location.longitude
            tf = TimezoneFinder()
            iana = tf.timezone_at(lng=lon, lat=lat)
        elif error:  # pragma: no cover
            iana = lat = lon = None
        else:
            iana = lat = lon = None
            error = f"Cannot find the timezone for '{address}'."

        return iana, lat, lon, error

    async def _insert_update_config_data_table(
        self, year: int, *, month: int=None, r_type: str=None, data: dict={}
        ) -> tuple:
        """
        Insert or update `data` table.

        :param int year: A Baha'i fiscal year of the transaction.
        :param int month: A Baha'i fiscal month of the transaction. This
                          is the order of the Baha'i month not the name.
        :param dict data: The data from the any panel  in the form of:
                          {<field name>: <value>, ...}.
        :returns: (<error or None>, rowcount)
        :rtype: tuple
        """
        error = None
        values = self.db.cache.get(self.db._T_DATA, year=year, r_type=r_type)
        rc = 0  # Row count

        if not values:  # Do insert
            items = {'year': year, 'month': month, 'data': data}
            rc = await self.db.cache.insert(self.db._T_DATA, items)
            self._log.info("Inserted %s table data: %s, rowcount %s.",
                           self.db._T_DATA, data, rc)
        else:
            update_data = {}
            # See select_from_config_data_table() for the mapping.
            #        value,    pk,      fy1.year
            items = {item[1]: item[0] for item in values}

            for field, value in data.items():  # Loop through incoming data
                pk = items.get(field, None)  # pk

                if pk is None:      # Error condition
                    error = f"Could not find field {field} in {data}."
                    self.db._mf.statusbar_error = error
                    self._log.error(error)
                    break

                update_data.setdefault('data', []).append((pk, str(value)))

            if update_data:                    # Do update
                rc = await self.db.cache.update(self.db._T_DATA, update_data)

        return error, rc

    @property
    def _earliest_fiscal_year(self) -> tuple:
        """
        Get the earliest year in the `fiscal_year` table.
        """
        years = self.__get_all_fiscal_years()
        return min(years) if years else None

    @property
    def _latest_fiscal_year(self) -> tuple:
        """
        Get the latest year in the `fiscal_year` table.
        """
        years = self.__get_all_fiscal_years()
        return max(years) if years else None

    def __get_all_fiscal_years(self) -> list:
        years = []

        for year in self.db.cache.available_years:
            fy = self.db.cache.get(self.db._T_FISCAL_YEAR, year=year)
            if not fy: break
            years.append(fy[0][1])

        return years

    @property
    def organization_data(self) -> dict:
        """
        This property gets the organization data.

        :returns: The organization data as defined by {<field name>: <value>}.
        :rtype: dict
        """
        items = self.db.cache.get(self.db._T_DATA, r_type='organization')
        return {item[1]: item[2] for item in items}

    @property
    def budget_data(self) -> dict:
        """
        This property gets the budget data.

        :returns: The budget data as defined by {<field name>: <value>}.
        :rtype: dict
        """
        items = self.db.cache.get(self.db._T_DATA, r_type='budget')
        return {item[1]: item[2] for item in items}

    @property
    def monthly_data(self) -> dict:
        """
        This property gets the monthly data.

        :returns: The monthly data as defined by {<field name>: <value>}.
        :rtype: dict
        """
        panel = self.db._mf.panels['monthly']
        data = self.db.collect_panel_values(panel)
        date = self.db.convert_str_date(data['month_index'])
        items = self.db.cache.get(self.db._T_MONTHLY, r_type=date)
        values = {}

        if items:
            items = items[0]
            columns = self.db.get_db_columns(self.db._T_MONTHLY)

            for idx, key in enumerate(columns):
                if key in ('pk', 'fyfk', 'cal_year_month', 'ctime', 'mtime'):
                    continue

                if key == 'outstanding':
                    pass

                values[key] = items[idx]

        return values
