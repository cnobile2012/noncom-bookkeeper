# -*- coding: utf-8 -*-
#
# src/populate_collect_panel.py
#
__docformat__ = "restructuredtext en"

import re
import wx

import datetime
import badidatetime

from .utilities import StoreObjects, make_name


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
        return self._check_panels_for_entries('monthly')

    @property
    def open_ledger_entry(self) -> bool:
        pass




    def _check_panels_for_entries(self, name: str) -> bool:
        """
        Check that the given panel name has entries.

        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        panel = self._mf.panels[name]
        data = self._collect_panel_values(panel)
        return all([item not in self._EMPTY_FIELDS for item in data.values()])

    def _collect_panel_values(self, panel: wx.Panel, convert_tz: bool=False
                              ) -> dict:
        """
        Collects the data from the panel widgets and convert if necessary to
        DB appropriate values.

        :param wx.Panel panel: The panel to collect data from.
        :param convert_tz: If `True` convert to the local timezone and if
                              `False` (default) do not convert.
        :returns: A dictonary of db field names and values as in
                  {<field name>: <value>}.
        :rtype: dict
        """
        data = {}

        for c_set in self._find_child_sets(panel):
            name0 = c_set[0].__class__.__name__
            field_name = make_name(c_set[0].GetLabelText())

            if name0 in ('RadioBox', 'ComboBox'):
                data[field_name] = c_set[0].GetSelection()
            elif name0 == 'StaticText':
                name1 = c_set[1].__class__.__name__
                value = c_set[1].GetValue()

                if name1 == 'TextCtrl':
                    data[field_name] = self._value_to_db(
                        value, financial=c_set[1].financial)
                elif name1 in ('BadiDatePickerCtrl', 'DatePickerCtrl'):
                    data[field_name] = self._value_to_db(value)
                elif name1 in ('ColorCheckBox', 'CheckBox'):
                    data[field_name] = value
                else:
                    msg = f"Invalid widget type '{name1}'."
                    self._log.error(msg)
                    self._mf.statusbar_error = msg
            else:
                msg = f"Invalid widget type '{name0}'."
                self._log.error(msg)
                self._mf.statusbar_error = msg

        # Add fields that are not in the GUI.
        if panel.__class__.__name__ == 'OrganizationPanel':
            data['iana_name'] = data.get('iana_name', None)
            data['latitude'] = data.get('latitude', None)
            data['longitude'] = data.get('longitude', None)

        return data

    def populate_panel_values(self, panel_name: str, panel: wx.Panel,
                              data: dict) -> None:
        """
        Poplulate the named panel with the database values.

        .. note:::

           1. Used when cancel is pressed--data is from db.organization_data.
           2. Used in BaseDatabase.populate_panels() which is used in
              BaseDatabase.save_to_database() and in MainFrame.start().

        :param str name: The name of the panel.
        :param wx.Panel panel: The panel object.
        :param dict data: The database values to be used to poplulate
                          the panel.
        """
        if data:  # When run after first time.
            for c_set in self._find_child_sets(panel):
                name0 = c_set[0].__class__.__name__
                name1 = c_set[1].__class__.__name__ if c_set[1] else None
                field_name = make_name(c_set[0].GetLabelText())
                value = data[field_name]

                if name0 == 'RadioBox':
                    value = self._str_to_int(value)
                    c_set[0].SetSelection(value)
                elif name0 == 'ComboBox':
                    if panel_name == 'fiscal':
                        self._add_fiscal_year_choices(c_set=c_set)

                    c_set[0].SetSelection(self._str_to_int(value))
                elif name0 == 'StaticText':
                    if name1 == 'TextCtrl':
                        if panel_name == 'monthly':
                            if not value:  # Populate yearly values.
                                if field_name == 'total_membership_this_month':
                                    value = self._org_data['total_membership']
                                elif field_name == 'treasurer_this_month':
                                    value = self._org_data['treasurer']
                        elif c_set[1].financial:
                            panel_value = c_set[1].GetValue()

                            if (panel_value
                                and self._str_to_int(panel_value) != 0):
                                value = self._panel_to_financial_panel(
                                    panel_value)
                            else:
                                value = self._db_fiancial_to_panel(value)
                        elif not c_set[1].financial:
                            panel_value = c_set[1].GetValue()
                            value = panel_value if panel_value else value
                        else:
                            msg = (f"Invalid widget type, found {name0} "
                                   f"with value {value}.")
                            self._log.error(msg)
                            self._mf.statusbar_error = msg
                            continue
                    elif name1 in ('BadiDatePickerCtrl', 'DatePickerCtrl'):
                        value = self._convert_date_to_yymmdd(value)

                    self._set_value(c_set[1], value)
                else:
                    msg = f"Invalid widget type, found {name0}"
                    self._log.error(msg)
                    self._mf.statusbar_error = msg
        elif panel_name == 'fiscal':  # First time run only.
            self._add_fiscal_year_choices(panel_name, panel)

    def _find_child_sets(self, panel: wx.Panel) -> list:
        """
        Find the children in the panel that hold data.

        :param wx.Panel panel: The panel to collect data from.
        :returns: A list of child sets.
        :rtype: list

        .. note::

           1. Panels are always rejected.
           2. Returns these lists:
              [RadioBox, TextCtrl], [StaticText, TextCtrl], [ComboBox, None],
              [StaticText, ColorCheckBox], [StaticText, BadiDatePickerCtrl]
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
            all_c_sets = self._find_child_sets(panel)
            c_set = [item[0] for item in all_c_sets
                     if item[0].__class__.__name__ == 'ComboBox']

        years = sorted([item[1] for item in self._fiscal_data])
        data = [(year, year+1) for year in years[:-1]]
        # Just get the title item, overwrite the rest.
        choices = [c_set[0].GetItems()[0]]
        c_set[0].SetItems(choices + [f"{t[0]}-{t[1]}" for t in data])
        c_set[0].SetSelection(0)

    def _value_to_db(self, value, financial: bool=False) -> str:
        """
        Convert the text currency value to an integer.

        .. note::

           We store currency values as integers converted to strings.
           Example $1952.14 in the db is 195214.

        :param value: A currency value from a field.
        :type value: str or badidatetime.date or datetime.date
        :returns: An integer value suttable for putting in the database.
        :rtype: str
        """
        neg = False

        if isinstance(value, int):
            value = str(value)

        if financial and value != '':
            if value[0] == '-':
                neg = True
                value = value[1:]
            elif value[0] == '+':
                value = value[1:]

            value = value.replace('.', '')
        elif self.is_badi_date_object(value) or isinstance(value, wx.DateTime):
            value = str(value)
        else:
            value = value.strip()

        return value

    def _db_fiancial_to_panel(self, value: str) -> str:
        """
        Convert a fiancial value from the database into a value sutable for
        displaying in a widget.

        :param int value: A currency value from the database.
        :returns: A string representation of a currency value.
        :rtype: str
        """
        try:
            value = f"{int(value)/100:.2f}"
        except ValueError:
            try:
                value = f"{float(value):.2f}"
            except ValueError:
                value = "0.00"

        return value

    def _panel_to_financial_panel(self, value: str) -> str:
        """
        Convert a financial value from the panel into a value sutable for
        displaying in a panel widget.

        :param str value: A financial value from a panel.
        :returns: A string representation of a currency value.
        :rtype: str
        """
        try:
            value = f"{int(value):.2f}"
        except ValueError:
            try:
                value = f"{float(value):.2f}"
            except ValueError:
                value = "0.00"

        return value

    def _str_to_int(self, value: str) -> int:
        """
        Convert a string to an integer.

        :param str value: Value to convert.
        :returns: Converted value or zero if value was not numeric.
        :rtype: int
        """
        if not isinstance(value, int):
            if value.isdigit():
                value = int(value)
            elif value.count('.'):
                try:
                    value = int(re.sub(r'\.', '', value))
                except ValueError as e:
                    msg = f"Expected a numeric value found '{value}'."
                    self._mf.statusbar_warning = msg
                    self._log.warning(msg[:-1] + ", %s", e)
                    value = 0
            else:
                msg = f"Expected a numeric value found '{value}'."
                self._mf.statusbar_warning = msg
                self._log.warning(msg)
                value = 0

        return value

    def _set_value(self, obj, value):
        if obj.GetValue != value:
            obj.SetValue(value)

    def is_badi_date_object(self, obj):
        return (obj.__class__.__name__ == 'date' and
                obj.__class__.__module__.endswith("badidatetime.datetime"))

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
        work_on = self._get_fiscal_year_value(year, work_on=True)
        audit = self._get_fiscal_year_value(year, audit=True)
        self.set_fiscal_panel(current, work_on, audit)

    def set_fiscal_panel(self, current, work_on, audit):
        for c_set in self._find_child_sets(self._mf.panels['fiscal']):
            name1 = c_set[1].__class__.__name__ if c_set[1] else c_set[1]
            field_name = make_name(c_set[0].GetLabelText())

            if (field_name == 'current_fiscal_year'
                and name1 == 'ColorCheckBox'):
                self._set_value(c_set[1], current)
            elif (field_name == 'work_on_this_fiscal_year'
                  and name1 == 'ColorCheckBox'):
                self._set_value(c_set[1], work_on)
            elif field_name == 'audit_complete' and name1 == 'ColorCheckBox':
                self._set_value(c_set[1], audit)

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
