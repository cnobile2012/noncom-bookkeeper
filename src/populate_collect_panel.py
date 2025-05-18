# -*- coding: utf-8 -*-
#
# src/populate_collect_panel.py
#
__docformat__ = "restructuredtext en"

import wx

from .utilities import StoreObjects


class PopulateCollect:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mf = StoreObjects().get_object('MainFrame')

    @property
    def has_org_info_data(self) -> bool:
        """
        Check that the db has the Organization Information.

        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        return self._check_panels_for_entries('organization')

    @property
    def has_budget_data(self) -> bool:
        """
        Check that the db has the Yearly Budget Information.

        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        return self._check_panels_for_entries('budget')

    @property
    def has_month_data(self) -> bool:
        """
        Check that the db has the Month Information.

        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        return self._check_panels_for_entries('month')

    def _check_panels_for_entries(self, name: str) -> bool:
        """
        Check that the given panel name has entries.

        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        panel = self._mf.panels[name]
        data = self._collect_panel_values(panel)
        return all([item not in self._EMPTY_FIELDS for item in data.values()])

    def _collect_panel_values(self, panel: wx.Panel,
                              convert_tz: bool=False) -> dict:
        """
        Collects the data from the panel's widgets.

        :param wx.Panel panel: The panel to collect data from.
        :param convert_tz: If `True` convert to the local timezone and if False
                               do not to be convert (default is False).
        :returns: A dictonary of db field names and values as in
                  {<field name>: <value>}.
        :rtype: dict
        """
        data = {}

        for c_set in self._find_children(panel):
            if isinstance(c_set[0], wx.Panel):
                continue

            name0 = c_set[0].__class__.__name__
            field_name = self._make_field_name(c_set[0].GetLabelText())

            if name0 == 'RadioBox':
                data[field_name] = self._scrub_value(c_set[0].GetSelection())
            elif name0 == 'ComboBox':
                data[field_name] = c_set[0].GetSelection()
            elif name0 == 'StaticText':
                name1 = c_set[1].__class__.__name__ if c_set[1] else c_set[1]
                value = c_set[1].GetValue()

                if name1 == 'TextCtrl':
                    financial = True if c_set[1].financial else False
                    data[field_name] = self._scrub_value(value,
                                                         financial=financial)
                elif name1 in ('BadiDatePickerCtrl', 'DatePickerCtrl'):
                    data[field_name] = self._scrub_value(value, convert_tz)
                elif name1 in ('ColorCheckBox', 'CheckBox'):
                    data[field_name] = c_set[1].GetValue()

            if panel.__class__.__name__ == 'OrganizationPanel':
                data['iana_name'] = None
                data['latitude'] = None
                data['longitude'] = None

        return data

    def populate_panel_values(self, panel_name: str, panel: wx.Panel,
                              values: list) -> None:
        """
        Poplulate the named panel with the database values.

        :param str name: The name of the panel.
        :param wx.Panel panel: The panel object.
        :param list or dict values: The database values to be used to
                                    poplulate the panel.
        """
        data = {}

        if isinstance(values, list):
            data = {v[1]: v[2] for v in values}
        elif isinstance(values, dict):
            data = values

        if data:  # When run after first time.
            for c_set in self._find_children(panel):
                name0 = c_set[0].__class__.__name__
                name1 = c_set[1].__class__.__name__ if c_set[1] else c_set[1]
                field_name = self._make_field_name(c_set[0].GetLabelText())
                value = data[field_name]

                if name0 == 'RadioBox':
                    c_set[0].SetSelection(value)
                elif name0 == 'ComboBox':
                    if panel_name == 'fiscal':
                        self._add_fiscal_year_choices(c_set=c_set)

                    c_set[0].SetSelection(value)
                elif name0 == 'StaticText':
                    if name1 == 'TextCtrl':
                        value = (self._db_to_value_currency(value)
                                 if c_set[1].financial else value)

                        if panel_name == 'month':
                            if (not value
                                and field_name == 'total_membership_month'):
                                value = self._org_data['total_membership']
                            elif not value and field_name == 'treasurer_month':
                                value = self._org_data['treasurer']

                        c_set[1].SetValue(value)
                    elif name1 in ('BadiDatePickerCtrl', 'DatePickerCtrl'):
                        c_set[1].SetValue(self._convert_date_to_yymmdd(value))
        elif panel_name == 'fiscal':  # When run during first time.
            self._add_fiscal_year_choices(panel_name, panel)

    def _find_children(self, panel: wx.Panel) -> list:
        """
        Find the children in the panel that hold data.

        :param wx.Panel panel: The panel to collect data from.
        :returns: A list of child sets.
        :rtype: list
        """
        children = []

        for child in panel.GetChildren():
            add = False
            name = child.__class__.__name__

            if (name in ('StaticLine', 'StaticText', 'Panel')
                and not child.GetLabel().endswith(':')):
                continue
            elif name == 'ComboBox':
                add = True

            children.append(child)
            if add: children.append(None)

        return [children[i:i+2] for i in range(0, len(children), 2)]

    def _add_fiscal_year_choices(self, panel_name: str=None,
                                 panel: wx.Panel=None, *, c_set=None):
        assert (panel_name and panel) or c_set, (
            "Can only pass 'panel_name' and 'panel' or just 'c_set' alone.")

        if not c_set:  # First time run.
            all_c_sets = self._find_children(panel)
            c_set = [item[0] for item in all_c_sets
                     if item[0].__class__.__name__ == 'ComboBox']

        years = sorted([item[1] for item in self._fiscal_data])
        data = [(year, year+1) for year in years[:-1]]
        # Just get the title item, overwrite the rest.
        choices = [c_set[0].GetItems()[0]]
        c_set[0].SetItems(choices + [f"{t[0]}-{t[1]}" for t in data])
        c_set[0].SetSelection(0)

    def _make_field_name(self, name: str):
        name = name.replace('(', '').replace(')', '')
        return name.replace(' ', '_').replace(':', '').lower()

    # *** TODO *** make the inverse of _make_field_name() above.

    def _scrub_value(self, value, convert_tz: bool=False,
                     financial: bool=False):
        if financial:
            value = self._value_to_db(value) if value != '' else '0'
        elif isinstance(value, str):
            value = value.strip()
        elif isinstance(value, wx.DateTime):
            # We convert into an ISO 8601 format for the db in local time.
            # *** TODO *** Change to local time.
            if convert_tz: value = value.ToUTC()
            value = value.FormatISOCombined()
        # *** TODO *** Maybe need not sure yet.
        #elif isinatance(value, badidatetime.datetime): # Badi datetime package
        #elif isinatance(value, datetime.datetime):  # Python datetime package
        return value

    def _value_to_db(self, value: str) -> int:
        """
        Convert the text currency value to an integer.

        .. note::

           We store currency values as integers.
           Example $1952.14 in the db is 195214.

        :param str value: A currency value from a field.
        :returns: An integer value suttable for putting in the database.
        :rtype: int
        """
        assert isinstance(value, str), ("The argument 'value' can only be a "
                                        f"string found {type(value)}")
        return int(float(value)*100)

    def _db_to_value_currency(self, value: str) -> str:
        """
        Convert an integer from the database into a value sutable for
        displaying in a widget.

        :param int value: A currency value from the database.
        :returns: A string representation of a currency value.
        :rtype: str
        """
        value = int(value)
        return f"{value/100:.2f}"

    #
    # Methods called from panels
    #

    def populate_fiscal_panel(self, year: int=None):
        """
        Populate the fiscal panel. This is called by an event from the
        ComboBox widget.

        :param str panel_name: The internal panel name.
        """
        current = self._get_fiscal_year_value(year, current=True)
        audit = self._get_fiscal_year_value(year, audit=True)
        work_on = self._get_fiscal_year_value(year, work_on=True)

        for c_set in self._find_children(self._mf.panels['fiscal']):
            name1 = c_set[1].__class__.__name__ if c_set[1] else c_set[1]
            field_name = self._make_field_name(c_set[0].GetLabelText())

            if (field_name == 'current_fiscal_year'
                and name1 == 'ColorCheckBox'):
                c_set[1].SetValue(current)
            elif field_name == 'audit_complete' and name1 == 'ColorCheckBox':
                c_set[1].SetValue(audit)
            elif field_name == 'work_on' and name1 == 'ColorCheckBox':
                c_set[1].SetValue(work_on)

    def _get_fiscal_year_value(self, year: int, *, pk: bool=False,
                               date: bool=False, current: bool=False,
                               work_on: bool=False, audit: bool=False,
                               time: bool=False):
        """
        Return a specific value from the `fiscal_year` table.

        :param bool pk: Get the Primary Key.
        :param bool date: Get the date, (year, month, day).
        :param bool current: Get the current fiscal year.
        :param bool work_on: Get which fiscal year is being worked on.
        :param bool audit: Get the audit status for the gived year.
        :param bool time: Get the create and modified dates and times.
        :returns: The value asked for.
        :rtype: int or tuple
        """
        # Create dict from list of raw fiscal data.
        assert (pk, date, current, audit,
                work_on, time).count(True) == 1, (
                    f"Only one argument can be `True`, found ({date}, "
                    f"{current}, {audit}, {work_on}, {time}).")
        data = {item[1]: item for item in self._fiscal_data}
        items = data.get(year)
        assert items, f"Invalid year {year}, options are {list(data)}."

        if pk:
            result = items[0]
        elif date:
            result = (items[1], items[2], items[3])
        elif current:
            result = items[4]
        elif work_on:
            result = items[5]
        elif audit:
            result = items[6]
        elif time:
            result = (items[7], items[8])

        return result
