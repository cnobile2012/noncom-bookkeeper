# -*- coding: utf-8 -*-
#
# src/populate_collect_panel.py
#
__docformat__ = "restructuredtext en"

import re
import wx
from string import ascii_letters, punctuation, whitespace

import datetime
import badidatetime

from .utilities import make_name, AsyncEventLoop

from .config import TomlMetaData, TomlCreatePanel
from .custom_widgits import ordered_month
from .ledger_transaction import LedgerTransaction


class PopulateCollect(AsyncEventLoop):
    _EMPTY_FIELDS = ('', '0')
    _EXCLUDE_WIDGETS = ('FlatArrowButton',)
    _tmd = TomlMetaData()
    _tcp = TomlCreatePanel()
    _BAD_CHRS = [c for c in ascii_letters + punctuation + whitespace
                 if c != '-']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
    def open_ledger_entry(self) -> bool:
        """
        Check that the db has the ledger Information.

        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        return self._check_panels_for_entries('ledger')

    def _check_panels_for_entries(self, name: str) -> bool:
        """
        Check that the given panel name has entries.

        :param str name: The panel name.
        :returns: True if data has been saved in the DB and False if not saved.
        :rtype: bool
        """
        panel = self._mf.panels[name]
        data = self.collect_panel_values(panel)
        items = []

        for w0, w1 in self.find_child_sets(panel):
            if (w1 is None or not hasattr(w1[2], 'mandatory')
                or not w1[2].mandatory):
                continue

            items.append(data[w0[1]])

        return all([item not in self._EMPTY_FIELDS for item in items])

    def _lde_push(self, key: str, value: str, panel: wx.Panel, data: dict
                  ) -> None:
        """
        Push LedgerDataEntry panel data to a dictionary object.

        :param str key: The panel compound category.field_name.
        :param str value: The pane value for the field name.
        :param wx.Panel panel: The LedgerDataEntry panel object.
        :param dict data: The dictionary object to push the value into.
        """
        category, field_name = key.split('.')

        for cat, labels in panel.ledger_labels.items():
            if isinstance(labels, list) and category == cat:
                if field_name in labels:
                    data.setdefault(cat, {})[field_name] = value
            elif isinstance(labels, dict):
                for sub_cat, sub_labels in labels.items():
                    if field_name in sub_labels and category == sub_cat:
                        tmp = data.setdefault(cat, {})
                        tmp.setdefault(sub_cat, {})[field_name] = value

    def _lde_pop(self, key: str, panel: wx.Panel, data: dict) -> str:
        """
        Pop values off the dictionary object.

        :param str key: The panel field name.
        :param wx.Panel panel: The LedgerDataEntry panel object.
        :param dict data: The dictionary object to push the value into.
        :returns: The value of the panel's field name.
        :rtype: str
        """
        result = ""
        category, field_name = key.split('.')

        for cat, labels in panel.ledger_labels.items():
            if isinstance(labels, list) and category == cat:
                if field_name in labels:
                    result = data[cat][field_name]
            elif isinstance(labels, dict):
                for sub_cat, sub_labels in labels.items():
                    if field_name in sub_labels:
                        result = data[cat][sub_cat][field_name]

        return result

    def collect_panel_values(self, panel: wx.Panel) -> dict:
        """
        Collects the data from the panel widgets and convert if necessary to
        DB appropriate values.

        :param wx.Panel panel: The panel to collect data from.
        :returns: A dictonary of db field names and values as in
                  {<field name>: <value>}.
        :rtype: dict
        """
        data = {}
        panel_name = panel.__class__.__name__

        if panel_name == 'LedgerDataEntry':
            def push(key, value): self._lde_push(key, value, panel, data)
        else:
            def push(key, value): data[key] = value

        for w0, w1 in self.find_child_sets(panel):
            name0, field_name, widget0 = w0
            if name0 in self._EXCLUDE_WIDGETS: continue

            if name0 in ('RadioBox', 'ComboBox'):
                if field_name == 'month_index':
                    push(field_name, widget0.GetStringSelection())
                else:
                    push(field_name, widget0.GetSelection())
            elif name0 == 'StaticText':
                name1, _, widget1 = w1
                value = widget1.GetValue()

                if hasattr(widget1, 'category'):
                    field_name = f"{widget1.category}.{field_name}"

                if name1 == 'TextCtrl':
                    financial = getattr(widget1, 'financial', False)
                    push(field_name, self._value_to_db(
                        value, financial=financial))
                elif name1 in ('BadiDatePickerCtrl', 'DatePickerCtrl',
                               'ColorCheckBox', 'CheckBox'):
                    push(field_name, value)
                else:  # pragma: no cover
                    self._set_statusbar(name1)
            else:  # pragma: no cover
                msg = f", panel '{panel_name}', widgets: {w0} and {w1}."
                self._set_statusbar(name0, add_msg=msg)

        # Add fields that are not in the UI.
        if panel_name == 'OrganizationPanel':
            push('iana_name', None)
            push('latitude', None)
            push('longitude', None)

        return data

    def populate_panel_values(self, panel_name: str, panel: wx.Panel,
                              data: dict) -> None:
        """
        Poplulate the named panel with the database values.

        :param str name: The name of the panel.
        :param wx.Panel panel: The panel object.
        :param dict data: The database values to be used to poplulate
                          the panel.
        """
        if panel_name == 'ledger':
            def pop(key): return self._lde_pop(key, panel, data)
        else:
            def pop(key): return data.get(key)

        if data:  # When run after first time.
            for w0, w1 in self.find_child_sets(panel):
                name0, field_name, widget0 = w0

                if w1:
                    name1, _, widget1 = w1

                    if hasattr(widget1, 'category'):
                        field_name = f"{widget1.category}.{field_name}"

                if name0 in self._EXCLUDE_WIDGETS: continue
                value = pop(field_name)
                if value is None: continue

                if name0 in ('RadioBox', 'ComboBox'):
                    if panel_name == 'fiscal':
                        self._add_fiscal_year_choices(w0=w0)

                    value = self._process_box_value(widget0, field_name, value)
                elif name0 == 'StaticText':
                    if name1 == 'TextCtrl':
                        financial = getattr(widget1, 'financial', False)

                        if financial:
                            value = self._panel_to_financial_panel(value)
                        elif not financial:
                            p_value = widget1.GetValue()
                            value = value if p_value == value else str(value)
                        else:  # pragma: no cover
                            self._set_statusbar(name1, f" with value {value}.")
                            continue
                    elif value and name1 in ('BadiDatePickerCtrl',
                                             'DatePickerCtrl'):
                        value = self.convert_date_to_yymmdd(value)

                    widget1.SetValue(value)
                else:  # pragma: no cover
                    self._set_statusbar(name0, f" with value {value}.")
        elif panel_name == 'fiscal':  # First time run only.
            self._add_fiscal_year_choices(panel=panel)

    def _set_statusbar(self, name: str, add_msg: str='.') -> None:
        """
        Log and send an error message to the panel status bar.

        :param str, name: Invalid widgit name.
        "param str add_msg: An additional message to add to the out
                            going messgage.
        """
        msg = f"Invalid widget type, found '{name}'"

        if '(' in add_msg:
            lg_msg = msg + add_msg
            sb_msg = msg + '.'
        else:
            lg_msg = msg + add_msg
            sb_msg = lg_msg

        self._log.error(lg_msg)
        self._mf.statusbar_error = sb_msg

    def _process_box_value(self, widget, field_name: str, value: str | int
                           ) -> str:
        """
        Process values from the RadioBox and ComboBox widgets.

        :param widget: Either a RadioBox or ComboBox widget.
        :param str field_name: The name of the widget.
        :param str or int value: The value to convert to an integer if
                                 not already an integer.
        :returns: An integer value of the incoming string.
        :rtype: int
        """
        if value != '':
            value, error = self._str_to_int(value)

            if value is None:
                error = error.format(field_name)
                self._log.warning(error)
                self._mf.statusbar_warning = error
            else:
                widget.SetSelection(value)

        return value

    def find_child_sets(self, panel: wx.Panel) -> list:
        """
        Find the children in the panel that have data.

        :param wx.Panel panel: The panel to collect data from.
        :returns: A list of child tuples.
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
                ('TextCtrl', '', <wx._core.TextCtrl>)],
               [('ComboBox', 'fiscal_year_choice', <wx._core.ComboBox>), None]
              ]
        """
        children = []

        for child in panel.GetChildren():
            add = False
            name = child.__class__.__name__
            label = child.GetLabel()

            if name in ('StaticLine', 'Panel', 'Button', 'FlatArrowButton'):
                continue
            if name in ('StaticText',) and not label.endswith(':'):
                continue
            elif name in ('ComboBox',):
                add = True
            elif name in ('ColorCheckBox',):
                label = child.GetLabelText()

            children.append((name, make_name(label), child))
            if add: children.append(None)

        result = [children[i:i+2] for i in range(0, len(children), 2)]
        assert all([len(item) == 2 for item in result]), (
            "Warning must be two children in all tuples.")
        return result

    def _add_fiscal_year_choices(self, *, panel: wx.Panel=None, w0=None
                                 ) -> None:
        """
        Add the fiscal years to the ComboBox choices.

        :param wx.Panel panel: The panel object.
        :param tuple w0: Widget information.
        """
        assert (panel, w0).count(None) == 1, (
            "Can only pass the 'panel' or the 'w0' arguments.")

        if not w0:  # First time run.
            widget = [w0[2] for w0, w1 in self.find_child_sets(panel)
                      if w0[0] == 'ComboBox'][0]
        else:
            widget = w0[2]

        years = sorted([item[1] for item in self.cache.all_fiscal_years])
        data = [(year, year+1) for year in years[:-1]]
        # Just get the title, overwrite the rest.
        choices = [widget.GetItems()[0]]
        widget.SetItems(choices + [f"{t[0]}-{t[1]}" for t in data])
        widget.SetSelection(0)

    def _value_to_db(self, value, financial: bool=False) -> str:
        """
        Convert a currency value to an integer.

        .. note::

           We store currency values as integers converted to strings.
           Example $1952.14 in the db is 195214.

        :param value: A currency value from a field.
        :type value: str, int or badidatetime.date or wx.DateTime.
        :returns: A string value suitable for inserting in the database.
        :rtype: str
        """
        if isinstance(value, (int, float)):
            value = str(value)

        if financial and value != '':
            if value[0] in self._BAD_CHRS:
                value = value[1:]

            value = value.replace('.', '').replace(',', '')
        elif isinstance(value, (badidatetime.datetime, datetime.datetime,
                                wx.DateTime)):
            value = str(value)
        else:
            value = value.strip()

        return value

    def _panel_to_financial_panel(self, value: str) -> str:
        """
        Convert a financial value from the panel into a value sutable for
        displaying in a panel widget.

        :param str value: An unformatted financial value from a panel.
        :returns: A string representation of a currency value.
        :rtype: str
        """
        if isinstance(value, int):
            value = f"{value/100:.2f}"
        elif isinstance(value, float):
            value = f"{value:.2f}"
        elif value.isdecimal():
            value = f"{int(value)/100:.2f}"
        elif self.isfloat(value):
            value = f"{float(value):.2f}"
        else:
            value = ''

        return value

    def _str_to_int(self, value: str | int) -> tuple:
        """
        Convert a numeric string to an integer.

        :param str or int value: Value to convert.
        :returns: Converted value or to 0 (zero) if value was not numeric and
                  an error or None.
        :rtype: tuple
        """
        error = f"Expected a numeric value in field '{{}}' found {value}."

        if not isinstance(value, int):
            if value.isdigit():
                value = int(value)
                error = None
            elif self.isfloat(value):
                value = int(re.sub(r'\.', '', value))
                error = None
            else:
                value = None
        else:
            error = None

        return value, error

    def isfloat(self, value: str) -> bool:
        return False if re.match(r'^-?\d+(?:\.\d+)$', value) is None else True

    # MONTHS = list(ordered_month().keys())
    # MONTH_INDEX = {m: i for i, m in enumerate(MONTHS)}

    # def get_prev_and_next(self, direction, year, month):
    #     """
    #     Get the previous and next year and month.
    #     """
    #     idx = self.MONTH_INDEX[month]

    #     if direction == 'RIGHT':  # Next month
    #         idx += 1

    #         if idx > 19:
    #             idx = 0
    #             year += 1
    #     else:  # LEFT -- previous month
    #         idx -= 1

    #         if idx < 0:
    #             idx = 19
    #             year -= 1

    #     return year, self.MONTHS[idx]

    #
    # Methods called from panels
    #

    def populate_fiscal_panel(self, year: int=None) -> None:
        """
        Populate the fiscal panel. This is called by an event from the
        ComboBox widget.

        :param int year: The fiscal year required.
        """
        fy = self.cache.get(self._T_FISCAL_YEAR, year=year)
        fy = fy[0] if fy else None
        self.set_fiscal_panel(fy[4], fy[5], fy[6])

    def set_fiscal_panel(self, current: bool, work_on: bool, audit: bool
                         ) -> None:
        for w0, w1 in self.find_child_sets(self._mf.panels['fiscal']):
            if w1 is None:  # Only on a ComboBox
                continue

            w_label = w0[1]
            name1 = w1[0]
            obj = w1[2]

            if w_label == 'current_fiscal_year' and name1 == 'ColorCheckBox':
                obj.SetValue(current)
            elif (w_label == 'work_on_this_fiscal_year'
                  and name1 == 'ColorCheckBox'):
                obj.SetValue(work_on)
            elif w_label == 'audit_complete' and name1 == 'ColorCheckBox':
                obj.SetValue(audit)

    def update_monthly_panel(self, date_str: str) -> None:
        """
        Update the 'monthly' panel data.

        :param str date_str: The string value from the ComboBox.
        """
        panel = self._mf.panels['monthly']
        date = self.convert_str_date(date_str)
        mon_idx = self.index_of_calendar_year(date)
        values = ()  # Used when no monthly data has been generated.

        for item in self.cache.get(self._T_MONTHLY):
            if item[2] == date:
                values = item
                break

        data = {'treasurer_this_month': ""}
        data = self.populate_monthly_data(mon_idx, values, data)
        panel.initializing = True
        self.populate_panel_values('monthly', panel, data)
        panel.initializing = False

    def ledger_search_panel(self, panel: wx.Panel):
        """
        Do the ledger search for the ledger panel.

        :param  wx.Panel panel: The ledger panel.
        """
        data = self.collect_panel_values(panel)
        valid = [v != '' for v in data.values()].count(True) == 1

        if valid:
            fy = self.cache.work_on_fiscal_year
            lt = LedgerTransaction(self)
            date = data['date']
            trans_num = data['transaction_id']
            ck_num = data['check_number']
            rcpt_num = data['receipt_number']
            memo = data['memo']
            rows = self.run_async(lt.select_ledger_transaction(
                fy[1], date=date, trans_num=trans_num, ck_num=ck_num,
                rcpt_num=rcpt_num, memo=memo))
            # *** TODO *** Do something with rows.
        else:
            rows = []

        return valid
