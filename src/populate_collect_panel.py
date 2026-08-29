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
    def has_ledger_data(self) -> bool:
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

            name0, field_name, widget0 = w0

            if name == 'ledger':
                for cat, subcat in data.items():
                    for fn, val in subcat.items():
                        if fn == 'date' or not val: continue
                        items.append(val)
            else:
                items.append(data[field_name])

        valid = all([item not in self._EMPTY_FIELDS for item in items])
        return valid if items else False

    def _lde_push(self, key: str, value: str, panel: wx.Panel, data: dict
                  ) -> None:
        """
        Push LedgerDataEntry panel data to a dictionary object and flatten and
        remove empty expenses so they are all in the 'expenses' category.

        :param str key: The panel compound category.field_name.
        :param str value: The pane value for the field name.
        :param wx.Panel panel: The LedgerDataEntry panel object.
        :param dict data: The dictionary object to push the value into.
        """
        category, field_name = key.split('.')

        for cat, labels in panel.ledger_labels.items():
            if category == cat and field_name in labels:
                data.setdefault(cat, {})[field_name] = value

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
            if category == cat and field_name in labels:
                result = data[cat].get(field_name, '')

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
            to_int = True
            def push(key, value): self._lde_push(key, value, panel, data)
        else:
            to_int = False
            def push(key, value): data[key] = value

        for w0, w1 in self.find_child_sets(panel):
            name0, field_name, widget0 = w0

            if name0 in self._EXCLUDE_WIDGETS:
                continue
            elif name0 in ('RadioBox', 'ComboBox'):
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
                        value, financial=financial, to_int=to_int))
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
            balances = self._get_balances()

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
                            if (balances and 'balance' in field_name
                                and value == ''):
                                value = balances[widget1.category]

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

                    if (panel_name == 'ledger' and name1 == 'ColorCheckBox'
                        and value):
                        widget1.Notify()

                else:  # pragma: no cover
                    self._set_statusbar(name0, f" with value {value}.")
        elif panel_name == 'fiscal':  # First time run only.
            self._add_fiscal_year_choices(panel=panel)

    def clear_panel(self, panel: wx.Panel) -> None:
        """
        Clear all fields in a panel.

        :param wx.Panel panel: The panel object.
        """
        balances = self._get_balances()

        for w0, w1 in self.find_child_sets(panel):
            name0, field_name, widget0 = w0

            if w1:
                name1, _, widget1 = w1

            if name0 in self._EXCLUDE_WIDGETS:
                continue
            elif name0 == 'RadioBox':
                widget0.SetSelection(0)
            elif name0 == 'ComboBox':
                widget0.SetSelection(-1)
                widget0.SetValue('')
            elif name0 == 'StaticText':
                if name1 == 'TextCtrl':
                    if balances and field_name == 'balance':
                        widget1.SetValue(str(balances[widget1.category]))
                    else:
                        widget1.SetValue('')
                elif name1 == 'BadiDatePickerCtrl':
                    widget1.SetValue(badidatetime.date.today())
                elif name1 == 'DatePickerCtrl':
                    widget1.SetValue(wx.DateTime.Today())
                elif name1 == 'ColorCheckBox':
                    widget1.SetValue(False)

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
        panel_class_name = panel.__class__.__name__

        for child in panel.GetChildren():
            add = False
            name = child.__class__.__name__
            label = child.GetLabel()

            if name in ('StaticLine', 'Panel', 'Button', 'FlatArrowButton',
                        'ConfirmationDialog', 'Frame'):
                continue
            if name in ('StaticText',) and not label.endswith(':'):
                continue
            elif name in ('ComboBox',):
                add = True
            elif name in ('ColorCheckBox',):
                label = child.GetLabelText()
            elif name in ('BadiDatePickerCtrl',):
                label = child.GetName()

            children.append((name, make_name(label), child))
            if add: children.append(None)

        result = [children[i:i+2] for i in range(0, len(children), 2)]

        for idx, item in enumerate(result):  # pragma: no cover
            if len(item) != 2:
                assert False, (
                    "Warning must have two children in all tuples, found error"
                    f" in item {idx} '{item}' from class {panel_class_name}.")

        return result

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

    def _add_fiscal_year_choices(self, *, panel: wx.Panel=None, w0=None
                                 ) -> None:
        """
        Add the fiscal years to the ComboBox choices.

        :param wx.Panel panel: The panel object.
        :param tuple w0: Widget information.
        """
        assert (panel, w0).count(None) == 1, (
            "Can only pass the 'panel' or the 'w0' argument.")

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

    def _value_to_db(self, value, *, financial: bool=False, to_int: bool=False
                     ) -> str:
        """
        Convert a currency value to an integer.

        .. note::

           We store currency values as integers converted to strings.
           Example 1952.14 in the db is 195214.

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

            if to_int:
                value = int(value.strip()) if value.isdecimal() else None
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

    def _get_balances(self) -> dict:
        """
        Get the balances and return a dict.
        """
        names = {1: 'bank', 2: 'coh', 3: 'income', 4: 'expenses'}
        lt = LedgerTransaction(self)
        balances = self.run_async(lt.select_transaction_balances(
            self.cache.year))
        return {names[bal[1]]: f"{bal[2]/100:.2f}" for bal in balances}

    def isfloat(self, value: str) -> bool:
        return False if re.match(r'^-?\d+(?:\.\d+)$', value) is None else True

    def convert_db_to_panel(self, row: tuple) -> dict:
        """
        Convert a row from the ledger tables to data usable for populating
        the ledger panel.

        .. note::

           1. Incoming data:
              ((5, 183, badidatetime.date(183, 8, 10), 'Test expenses',
                3, 1, '', 2, 30000, None, None, None, None, 0,
                <badidatetime.datetime>, <badidatetime.datetime>),
               [(5, 'national_baháí_fund', 20000),
                (5, 'regional_baháí_council', 10000)])
        """
        def db_to_panel(fn: str, value: str | int, mapping: dict) -> bool:
            return fn == mapping[value]

        trn_map = {None: '', 1: 'contribution', 2: 'distribution',
                   3: 'expense', 4: 'other'}
        ref_map = {None: '', 1: 'ocs', 2: 'check', 3: 'receipt', 4: 'deposit'}
        bnk_map = {None: '', 1: 'deposit', 2: 'withdrawal'}
        coh_map = {None: '', 1: 'replenishment', 2: 'disbursement'}
        inc_map = {None: '', 1: 'local_fund', 2: 'contributed_expense',
                   3: 'other'}
        trans = row[0]
        expenses = row[1]
        data = {'panel': {}, 'transaction': {}, 'reference': {}, 'bank': {},
                'coh': {}, 'income': {}, 'expenses': {}}
        data['panel']['transaction_id'] = trans[0]
        data['panel']['date'] = trans[2]
        data['panel']['memo'] = trans[3]
        data['panel']['total_expenses'] = 0
        data['transaction']['contribution'] = db_to_panel('contribution',
                                                          trans[4], trn_map)
        data['transaction']['distribution'] = db_to_panel('distribution',
                                                          trans[4], trn_map)
        data['transaction']['expense'] = db_to_panel('expense', trans[4],
                                                     trn_map)
        data['transaction']['other'] = db_to_panel('other', trans[4], trn_map)
        data['reference']['ocs'] = db_to_panel('ocs', trans[5], ref_map)
        data['reference']['check'] = db_to_panel('check', trans[5], ref_map)
        data['reference']['receipt'] = db_to_panel('receipt', trans[5],
                                                   ref_map)
        data['reference']['deposit'] = db_to_panel('deposit', trans[5],
                                                   ref_map)
        data['reference']['number'] = trans[6]
        data['bank']['deposit'] = db_to_panel('deposit', trans[7], bnk_map)
        data['bank']['withdrawal'] = db_to_panel('withdrawal', trans[7],
                                                 bnk_map)
        data['bank']['amount'] = trans[8]
        data['coh']['replenishment'] = db_to_panel('replenishment', trans[9],
                                                   coh_map)
        data['coh']['disbursement'] = db_to_panel('disbursement', trans[9],
                                                  coh_map)
        data['coh']['amount'] = trans[10]
        data['income']['local_fund'] = db_to_panel('local_fund', trans[11],
                                                   inc_map)
        data['income']['contributed_expense'] = db_to_panel(
            'contributed_expense', trans[11], inc_map)
        data['income']['other'] = db_to_panel('other', trans[11], inc_map)
        data['income']['amount'] = trans[12]

        for _, fn, amount in expenses:
            data['expenses'][fn] = amount
            data['panel']['total_expenses'] += amount

        return data

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

    def ledger_search_panel(self, panel: wx.Panel) -> list:
        """
        Do the ledger search for the ledger panel.

        :param  wx.Panel panel: The ledger panel.
        :resurns: A list of found records.
        :rtype: list

        .. note::

           1. Incoming data:
              {'panel.transaction_id': '', 'panel.date': '', 'panel.memo': '',
               'transaction.contribution': True,
               'transaction.distribution': False, 'transaction.expense': False,
               'transaction.other': False,
               'reference.ocs': True, 'reference.check': False,
               'reference.receipt': False, 'reference.deposit': False,
               'reference.number': '',
               'bank.deposit': False, 'bank.withdrawal': True,
               'coh.replenishment': False, 'coh.disbursement': False,
               'income.local_fund': False, 'income.contributed_expense': False,
               'income.other': False}

           2. Resulting data (Zero or many rows):
              [((5, 183, badidatetime.date(183, 8, 10), 'Test expenses',
                 3, 1, '', 2, 30000, None, None, None, None, 0,
                 <badidatetime.datetime>, <badidatetime.datetime>),
                [(5, 'national_baháí_fund', 20000),
                 (5, 'regional_baháí_council', 10000)])]
        """
        data = self.collect_panel_values(panel)
        data['panel.purge'] = None  # Temporary
        fy = self.cache.work_on_fiscal_year
        kwargs = {}
        kwargs['trans_id'] = data['panel.transaction_id']
        kwargs['date'] = data['panel.date']
        kwargs['memo'] = data['panel.memo']
        kwargs['purge'] = data['panel.purge']
        # Transaction Type
        co = data['transaction.contribution']
        di = data['transaction.distribution']
        ex = data['transaction.expense']
        ot = data['transaction.other']
        t_type = [idx for idx, value in enumerate((co, di, ex, ot), start=1)
                  if value]
        kwargs['t_type'] = t_type[0] if t_type else 0
        # Entry Reference
        ocs = data['reference.ocs']
        ck = data['reference.check']
        rt = data['reference.receipt']
        dp = data['reference.deposit']
        r_type = [idx for idx, value in enumerate((ocs, ck, rt, dp), start=1)
                  if value]
        kwargs['r_type'] = r_type[0] if r_type else 0
        kwargs['number'] = data['reference.number']
        # Bank
        dpst = data['bank.deposit']
        wthd = data['bank.withdrawal']
        b_type = [idx for idx, value in enumerate((dpst, wthd), start=1)
                  if value]
        kwargs['b_type'] = b_type[0] if b_type else 0
        # CoH
        rpln = data['coh.replenishment']
        dsbu = data['coh.disbursement']
        c_type = [idx for idx, value in enumerate((rpln, dsbu), start=1)
                  if value]
        kwargs['c_type'] = c_type[0] if c_type else 0
        # Income
        lf = data['income.local_fund']
        ce = data['income.contributed_expense']
        othr = data['income.other']  # Sale of an item
        i_type = [idx for idx, value in enumerate((lf, ce, othr), start=1)
                  if value]
        kwargs['i_type'] = i_type[0] if i_type else 0
        rows = []
        valid = any([val for val in kwargs.values() if val])
        lt = LedgerTransaction(self)

        if valid:
            t_rows = self.run_async(lt.select_ledger_transaction(
                fy[1], **kwargs))

            for row in t_rows:
                e_rows = self.run_async(lt.select_expenses(row[0]))  # trans_id
                rows.append((row, e_rows))

        return rows
