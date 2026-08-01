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
from .ledger_transaction import LedgerTransaction


class DataPreperation:
    """
    All data in the data and fiscal_year tables need to prepared before
    cached or saved to the database.
    """
    _ERR_MSG0 = ("If Transaction Type (Contribution) and Entry Reference ("
                 "Receipt) you must also enter Cash On Hand (Replenishment "
                 "and Amount) and Income (Local Fund and Amount).")
    _ERR_MSG1 = ("If Transaction Type (Contribution) and Entry Reference ("
                 "Receipt and Number) you must also enter Income (Contributed "
                 "Expense) and at least one expense.")
    _ERR_MSG2 = ("Missing either the Transaction Type (Contribution) and "
                 "Entry Reference (Receipt and Number)")
    _ERR_MSG3 = ("If Transaction Type->Contribution and Entry Reference->"
                 "OCS you must also enter Income (Local Fund and Amount).")
    _ERR_MSG4 = ("If Transaction Type (Distribution) you must also enter "
                 "Entry Reference (OCS) and Bank (Deposit and Amount).")
    _ERR_MSG5 = ("If Transaction Type (Distribution) you must also enter "
                 "Entry Reference (Deposit and Number) and Bank (Deposit and "
                 "Amount) and Cash-on-Hand (Disbursement and Amount).")
    _ERR_MSG6 = ("If Transaction Type->Expense you must also enter at "
                 "least one expense and either Entry Reference (Check and Nu"
                 "mber) and Bank (Withdrawal) or Entry Reference->OCS and "
                 "Bank->Withdrawal or Entry Reference (Receipt and Number) "
                 "and Cash-on-Hand->Disbursement.")
    _ERR_MSG7 = ("If Transaction Type->Other you must also enter a Memo "
                 "and Entry Reference->Receipt Number and Cash-on-Hand->"
                 "Replenishment and Income->Local Fund.")

    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tac = TomlAppConfig()
        self._log = logging.getLogger(self._tac.logger_name)
        self.db = db

    async def organization(self, data: dict, date: tuple) -> str | None:
        """
        Insert or update the organization data.

        :param dict data: The data to insert or update.
        :param tuple date: The current fiscal year date.
        :returns: An error message or None.
        :rtype: str or None
        """
        error = None
        f_year, f_month, f_day = date

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
                        # Update the fiscal both years.
                        if f_month != p_month or f_day != p_day:
                            wrong_fy = (f_year, f_month, f_day)
                            correct_fy = (p_year, p_month, p_day)
                            await self._fix_fiscal_years(wrong_fy, correct_fy)
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
        # Only the date is mandatory, and it always defaults to today.
        error = self._empty_fields('ledger', data)
        trans_id = data['panel']['transaction_id']
        data['panel']['purge'] = 0

        if not error:
            state = self._build_ledger_state(data)
            panel = state['panel']
            ref = state['reference']
            bank = state['bank']
            coh = state['coh']
            income = state['income']
            expenses = state['expenses']

            if state['transaction']['contribution']:
                receipt_stats = (ref['receipt'], ref['number'])

                if all(receipt_stats):
                    fund_stats = (coh['replenishment'], coh['amount'],
                              income['local_fund'], income['amount'])

                    if all(fund_stats):
                        error = None
                    else:
                        error = self._ERR_MSG0

                        if (income['contributed_expense'] and income['amount']
                            and expenses):
                            error = None
                        elif not any(fund_stats):
                            error = self._ERR_MSG1
                elif any(receipt_stats):
                    error = self._ERR_MSG2
                elif not (ref['ocs'] and income['local_fund']
                          and income['amount']):
                    error = self._ERR_MSG3
            elif state['transaction']['distribution']:
                if (ref['ocs'] and bank['deposit'] and bank['amount']):
                    error = None
                else:
                    error = self._ERR_MSG4

                    if (ref['deposit'] and ref['number']
                        and bank['deposit'] and bank['amount']
                        and coh['disbursement'] and coh['amount']):
                        error = None
                    elif not ref['ocs']:
                        error = self._ERR_MSG5
            elif state['transaction']['expense']:
                if not (ref['check'] and bank['withdrawal']
                        and bank['amount'] and expenses):
                    error = self._ERR_MSG6

                if not (ref['ocs'] and bank['withdrawal'] and bank['amount']
                        and expenses):
                    error = self._ERR_MSG6

                if not (ref['receipt'] and coh['disbursement']
                        and coh['amount'] and expenses):
                    error = self._ERR_MSG6
            elif state['transaction']['other']:
                if not (panel['memo'] and ref['receipt']
                        and coh['replenishment'] and coh['amount']
                        and income['local_fund'] and income['amount']):
                    error = self._ERR_MSG7

            if not error:
                self.lt = LedgerTransaction(self.db, data)

                if trans_id.isdigit():
                    rc = await self.lt.update_ledger_transaction(int(trans_id))
                    self._log.info("Updated %s rows of ledger data.", rc)
                else:
                    rc = await self.lt.insert_ledger_transaction(date[0])
                    self._log.info("Inserted %s rows of ledger data.", rc)

        return error

    def _build_ledger_state(self, data: dict) -> dict:
        """
        Build the boolean state matrix used to validate a ledger entry.
        """
        state = {
            'panel': {
                'memo': data['panel']['memo'] != '',
                },
            'transaction': {
                'contribution': data['transaction']['contribution'],
                'distribution': data['transaction']['distribution'],
                'expense': data['transaction']['expense'],
                'other': data['transaction']['other'],
                },
            'reference': {
                'ocs': data['reference']['ocs'],
                'check': data['reference']['check'],
                'receipt': data['reference']['receipt'],
                'deposit': data['reference']['deposit'],
                'number': data['reference']['number'] != ''
                },
            'bank': {
                'deposit': data['bank']['deposit'],
                'withdrawal': data['bank']['withdrawal'],
                'amount': data['bank']['amount'] is not None,
                },
            'coh': {
                'replenishment': data['coh']['replenishment'],
                'disbursement': data['coh']['disbursement'],
                'amount': data['coh']['amount'] is not None,
                },
            'income': {
                'local_fund': data['income']['local_fund'],
                'contributed_expense': data['income']['contributed_expense'],
                'other': data['income']['other'],
                'amount': data['income']['amount'] is not None,
                },
            'expenses': any(value for subcat in data['expenses'].values()
                            for value in subcat.values()),
            }

        return state

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
            if getattr(w0[2], 'mandatory', False):
                mandatory.append(w0[1])
            elif w1 and getattr(w1[2], 'mandatory', False):
                mandatory.append(w0[1])

        empty_fields = [field for field, value in data.items()
                        if value == '' and field in mandatory]

        if len(empty_fields) != 0:
            ef = ', '.join([f for f in empty_fields])
            error = f"The '{ef}' field(s) must not be empty."

        return error

    async def _first_run_initialization(self, year: int, month: int, day: int
                                        ) -> None:
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
            if name not in ('organization', 'budget'): continue
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

    async def _fix_fiscal_years(self, wrong_fy: tuple, correct_fy: tuple
                                ) -> int:
        """
        We need to fix the fiscal years if the month and/or day were
        entered wrong.

        :param tuple wrong_fy: A tuple indicating the year, mont, and day.
        :param tuple correct_fy: A tuple indicating the year, mont, and day.
        :returns: The number of DB rows affected.
        :rtype: int
        """
        rowcount = 0
        db_fy = self.db._T_FISCAL_YEAR
        w_year, w_month, w_day = wrong_fy
        c_year, c_month, c_day = correct_fy
        fy1 = self.db.cache.get(db_fy, year=w_year)
        fy2 = self.db.cache.get(db_fy, year=w_year + 1)

        if fy1:
            fy_years = [(c_year, c_month, c_day, *fy1[0][4:7])]

            if fy2:
                fy_years.append((c_year + 1, c_month, c_day, *fy2[0][4:7]))

            rowcount += await self.db.cache.update(db_fy, {'data': fy_years})

        return rowcount

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
        years = [fy[1] for fy in self.db.cache.all_fiscal_years]
        return min(years) if years else None

    @property
    def _latest_fiscal_year(self) -> tuple:
        """
        Get the latest year in the `fiscal_year` table.
        """
        years = [fy[1] for fy in self.db.cache.all_fiscal_years]
        return max(years) if years else None

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

    @property
    def ledger_data(self) -> dict:
        """
        This property get the ledger data.

        :returns: The ledger data as defined by {<field name>: <value>}.
        :rtype: dict
        """
        panel = self.db._mf.panels['ledger']
        data = self.db.collect_panel_values(panel)
        # *** TODO *** Make DB call to get the refreash data.
        return {}
