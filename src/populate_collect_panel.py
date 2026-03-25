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
from .config import TomlMetaData, TomlCreatePanel

class PopulateCollect:
    _EMPTY_FIELDS = ('', '0')
    _tmd = TomlMetaData()
    _tcp = TomlCreatePanel()

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
        items = []

        for w0, w1 in self._find_child_sets(panel):
            if (w1 is None or not hasattr(w1[2], 'mandatory')
                or not w1[2].mandatory):
                continue

            items.append(data[w0[1]])

        return all([item not in self._EMPTY_FIELDS for item in items])

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
        #print('POOP', self._find_child_sets(panel))

        for w0, w1 in self._find_child_sets(panel):
            name0 = w0[0]
            field_name = w0[1]
            widget0 = w0[2]

            if name0 in ('RadioBox', 'ComboBox'):
                data[field_name] = widget0.GetSelection()
            elif name0 == 'StaticText':
                name1 = w1[0]
                widget1 = w1[2]
                value = widget1.GetValue()

                if name1 == 'TextCtrl':
                    data[field_name] = self._value_to_db(
                        value, financial=widget1.financial)
                elif name1 in ('BadiDatePickerCtrl', 'DatePickerCtrl',
                               'ColorCheckBox', 'CheckBox'):
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
            for w0, w1 in self._find_child_sets(panel):
                name0 = w0[0]
                field_name = w0[1]
                widget0 = w0[2]
                value = data[field_name]

                if name0 == 'RadioBox':
                    value = self._process_value(widget0, field_name, value)
                elif name0 == 'ComboBox':
                    if panel_name == 'fiscal':
                        self._add_fiscal_year_choices(w0=w0)

                    value = self._process_value(widget0, field_name, value)
                elif name0 == 'StaticText':
                    name1 = w1[0]
                    widget1 = w1[2]

                    if name1 == 'TextCtrl':
                        if widget1.financial:
                            panel_value = widget1.GetValue()

                            if panel_value != '':
                                panel_value = self._panel_to_financial_panel(
                                    panel_value)
                                value = (panel_value if panel_value != value
                                         else value)
                            else:
                                value = self._db_fiancial_to_panel(value)
                        elif not widget1.financial:
                            panel_value = widget1.GetValue()
                            value = panel_value if panel_value != '' else value
                        else:
                            msg = (f"Invalid widget type, found {name0} "
                                   f"with value {value}.")
                            self._log.error(msg)
                            self._mf.statusbar_error = msg
                            continue
                    elif value and name1 in ('BadiDatePickerCtrl',
                                             'DatePickerCtrl'):
                        iso_today = self._today().isoformat()
                        panel_value = widget1.GetValue()

                        if iso_today == panel_value.isoformat():
                            value = self._convert_date_to_yymmdd(value)
                        else:
                            value = panel_value

                    self._set_value(widget1, value)
                else:
                    msg = f"Invalid widget type, found {name0}"
                    self._log.error(msg)
                    self._mf.statusbar_error = msg
        elif panel_name == 'fiscal':  # First time run only.
            self._add_fiscal_year_choices(panel_name, panel)

    def _process_value(self, widget, field_name, value):
        """
        Scrup values for RadioBox and ComboBox widgets.
        """
        if value != '':
            value, error = self._str_to_int(value)

            if value is not None:
                widget.SetSelection(value)
            else:
                error = error.format(field_name)
                self._log.warning(error)
                self._mf.statusbar_warning = error

        return value

    def _find_child_sets(self, panel: wx.Panel) -> list:
        """
        Find the children in the panel that hold data.

        :param wx.Panel panel: The panel to collect data from.
        :returns: A list of child sets.
        :rtype: list

        .. note::

           1. Panels are always rejected.
           2. Example result lists:
              [
               [('RadioBox', 'locality_prefix', <wx._core.RadioBox>),
                ('TextCtrl', '', <wx._core.TextCtrl>)],
               [('StaticText', 'locale_name', <wx._core.StaticText>),
                ('TextCtrl', '', <wx._core.TextCtrl>)],
               [('StaticText', 'total_membership', <wx._core.StaticText>),
                ('TextCtrl', '', <wx._core.TextCtrl>)],
               [('StaticText', 'treasurer', <wx._core.StaticText>),
                ('TextCtrl', '', <wx._core.TextCtrl>)],
               [('StaticText', 'start_of_fiscal_year', <wx._core.StaticText>),
                ('BadiDatePickerCtrl', '',
                 <src.custom_widgits.BadiDatePickerCtrl>)],
               [('StaticText', 'location_city_name', <wx._core.StaticText>),
                ('TextCtrl', '', <wx._core.TextCtrl>)]
              ]
        """
        children = []

        for child in panel.GetChildren():
            add = False
            name = child.__class__.__name__
            label = child.GetLabel()

            if (name in ('StaticLine', 'StaticText', 'Panel')
                and not label.endswith(':')):
                continue
            elif name == 'ComboBox':
                add = True

            children.append((name, make_name(label), child))
            if add: children.append(None)

        return [children[i:i+2] for i in range(0, len(children), 2)]

    def _add_fiscal_year_choices(self, panel_name: str=None,
                                 panel: wx.Panel=None, *, w0=None):
        assert (panel_name and panel) or c_set, (
            "Can only pass 'panel_name' and 'panel' or just 'w_set' alone.")

        if not w0:  # First time run.
            widgets = [w0[2] for w0, w1 in self._find_child_sets(panel)
                  if w0[0] == 'ComboBox']
            widget0 = widgets[0]
        else:
            widget0 = w0[2]

        years = sorted([item[1] for item in self._fiscal_data])
        data = [(year, year+1) for year in years[:-1]]
        # Just get the title, overwrite the rest.
        choices = [widget0.GetItems()[0]]
        widget0.SetItems(choices + [f"{t[0]}-{t[1]}" for t in data])
        widget0.SetSelection(0)

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
                value = ''

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
                value = ''

        return value

    def _str_to_int(self, value: str) -> int:
        """
        Convert a string to an integer.

        :param str value: Value to convert.
        :returns: Converted value or zero if value was not numeric.
        :rtype: int
        """
        error = f"Expected a numeric value in field '{{}}' found {value}."

        if not isinstance(value, int):
            if value.isdigit():
                value = int(value)
                error = None
            elif value.count('.'):
                try:
                    value = int(re.sub(r'\.', '', value))
                    error = None
                except ValueError as e:
                    error = error[:-1] + str(e)
                    value = None
            else:
                value = None
        else:
            error = None

        return value, error

    def _set_value(self, obj, value):
        if obj.GetValue() != value:
            obj.SetValue(value)

    def is_badi_date_object(self, obj):
        return (obj.__class__.__name__ == 'date' and
                obj.__class__.__module__.endswith("badidatetime.datetime"))

    def _get_field_name(self, panel_name):
        items = self._tmd.panel_config.get(panel_name, {}).get('widgets', {})
        self._tcp.current_panel = items
        return [make_name(field) for field in self._tcp.field_names]

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
            if c_set[1] is None:  # Only on a ComboBox
                continue

            w_label = c_set[0][1]
            name1 = c_set[1].__class__.__name__

            if w_label == 'current_fiscal_year' and name1 == 'ColorCheckBox':
                self._set_value(c_set[1], current)
            elif (w_label == 'work_on_this_fiscal_year'
                  and name1 == 'ColorCheckBox'):
                self._set_value(c_set[1], work_on)
            elif w_label == 'audit_complete' and name1 == 'ColorCheckBox':
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
