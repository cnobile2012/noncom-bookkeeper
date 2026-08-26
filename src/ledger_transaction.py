# -*- coding: utf-8 -*-
#
# src/ledger_transaction.py
#
__docformat__ = "restructuredtext en"

import json
import sqlite3
import aiosqlite
import badidatetime


class LedgerTransaction:
    """
    Handle all ledger transaction.
    """
    _TRANS_TYPES = ('contribution', 'distribution', 'expense', 'other')
    _REF_TYPES = ('ocs', 'check', 'receipt', 'deposit')
    _BANK_TYPES = ('deposit', 'withdrawal')
    _COH_TYPES = ('replenishment', 'disbursement')
    _INCM_TYPES = ('local_fund', 'contributed_expense', 'other')

    def __init__(self, db, data: dict={}) -> None:
        """
        This constructor splits the data into the dicts needed by each
        insert or update method. It also handles selects on the ledger.

        :param db: The database class object.
        :param dict data: The data to process or an empty object if
                          selecting data.
        """
        self.db = db

        if data:
            self._header = data['panel']
            self._trans = self._make_type_index(data['transaction'],
                                           self._TRANS_TYPES)
            self._ref = self._make_type_index(data['reference'],
                                              self._REF_TYPES)
            self._bank = self._make_type_index(data.get('bank'),
                                               self._BANK_TYPES)
            self._coh = self._make_type_index(data.get('coh'), self._COH_TYPES)
            self._income = self._make_type_index(data.get('income'),
                                            self._INCM_TYPES)
            self._expenses = {
                key: value for key, value in data.get('expenses', {}).items()
                if value not in self.db._EMPTY_FIELDS}
            self._details = self.serialize_data(data)

    def _make_type_index(self, data: dict, types: tuple) -> dict:
        """
        Derive the type for each category that has types.

        :param dict data: The category data.
        :returns: An updated data structure.
        :rtype: dict
        """
        items = {}

        if data:
            idx = 0
            items['itype'] = idx

            for field_name, value in data.items():
                if field_name in types:
                    idx += 1

                    if value:
                        items['itype'] = idx
                else:
                    items[field_name] = value

        return items

    def serialize_data(self, data: dict) -> str:
        """
        Serialize the data for insertion into the history table.

        :param dict data: The data to process or an empty object if
                          selecting data.
        :returns: A JSON object.
        :rtype: str
        """
        to_json = {}

        for cat, cat_values in data.items():
            if isinstance(cat_values, dict):
                tmp = to_json.setdefault(cat, {})

                for key, value in cat_values.items():
                    if isinstance(value, (badidatetime.date,
                                          badidatetime.datetime)):
                        value = value.isoformat()

                    empty = value not in self.db._EMPTY_FIELDS

                    if ((cat == 'expenses' and empty) or cat != 'expenses'):
                        tmp[key] = value

        return json.dumps(to_json)

    def deserialize_data(self, json_str: str) -> dict:
        """
        Deserialize a JSON string to a dict.

        :param str json_str: A sring representing a JSON object.
        :returns: A dictionary from a JSON object.
        :rtype: dict
        """
        tmp_data = json.loads(json_str)
        data = {}

        for cat, cat_values in tmp_data.items():
            if isinstance(cat_values, dict):
                tmp = data.setdefault(cat, {})

                for key, value in cat_values.items():
                    if isinstance(value, str):
                        v_len = len(value)

                        if (v_len >= 10
                            and (value[4], value[7]).count('-') == 2):
                            if (v_len >= 19
                                and (value[13], value[16]).count(':') == 2):
                                value = badidatetime.datetime.fromisoformat(
                                    value)
                            else:
                                value = badidatetime.date.fromisoformat(value)

                    tmp[key] = value

        return data

    async def select_ledger_transaction(self, year, **kwargs) -> list:
        """
        Select a row from the vw_ledger_transaction view.

        :param int year: The fiscal year.
        :param dict kwargs: Keyword arguments of column name and value.
        :returns: The row of data.
        :rtype: list
        """
        def make_where(column, value):
            if value:
                if column in ('memo', 'number'):
                    where = f"AND {column} LIKE '%' || :{column} || '%' "
                else:
                    where = f"AND {column} = :{column} "
            elif value is None and column in ('b_type', 'c_type', 'i_type'):
                match column:
                    case 'b_type':
                        types = "1, 2"
                    case 'c_type':
                        types = "1, 2"
                    case 'i_type':
                        types = "1, 2, 3"

                where = f"AND {column} IN ({types}) "
            else:
                where = ''

            return where

        where = ''

        for column, value in kwargs.items():
            where += make_where(column, value)

        query = (f"SELECT * FROM {self.db._V_LEDGER_TRANSACTION} WHERE "
                 f"fy_year = :year {where.strip()};")
        kwargs['year'] = year
        return await self.db._do_select_query(query, kwargs)

    async def insert_ledger_transaction(self, year: int) -> int:
        """
        Insert into the ledger_transaction table.

        :param int year: The Badi year of the transaction.
        :returns: The rowcount caused by the insert.
        :rtype: int
        """
        async with aiosqlite.connect(
            self.db.user_data_fullpath,
            detect_types=self.db._DETECT_TYPES) as con:
            await con.execute("PRAGMA foreign_keys=ON")

            try:
                await con.execute("BEGIN;")
                rowcount = 0
                trans_pk, rc = await self._insert_transaction(con)
                rowcount += rc
                ref_pk, rc = await self._insert_reference(con)
                rowcount += rc
                fy = await self.db.select_from_fiscal_year_table(year=year)
                fy1fk = fy[0]
                fy = await self.db.select_from_fiscal_year_table(year=year + 1)
                fy2fk = fy[0]
                header_pk, rc = await self._insert_header(
                    con, fy1fk, fy2fk, trans_pk, ref_pk)
                rowcount += rc
                rowcount += await self._insert_ledger_history(
                    con, header_pk, fy1fk)

                if (self._bank and self._bank['itype'] != 0
                    and self._bank['amount'] is not None):
                    rowcount += await self._insert_bank(con, header_pk)
                    rowcount += await self._update_ledger_balances(
                        con, fy1fk, 1)

                if (self._coh and self._coh['itype'] != 0
                    and self._coh['amount'] != 0):
                    rowcount += await self._insert_coh(con, header_pk)
                    rowcount += await self._update_ledger_balances(
                        con, fy1fk, 2)

                if (self._income and self._income['itype'] != 0
                    and self._income['amount'] != 0):
                    rowcount += await self._insert_income(con, header_pk)
                    rowcount += await self._update_ledger_balances(
                        con, fy1fk, 3)

                if self._expenses:
                    rowcount += await self._insert_expenses(con, header_pk)
                    rowcount += await self._update_ledger_balances(
                        con, fy1fk, 4)

                await con.commit()
                return rowcount
            except Exception as e:
                await con.rollback()
                self.db._log.exception("Error during ledger insert.")
                raise

    async def _insert_transaction(self, con) -> tuple:
        """
        Insert the transaction meta-data.

        :param com: The database connection object.
        :returns: The last row pk and the rowcount.
        :rtype: tuple
        """
        query = (f"INSERT INTO {self.db._T_LEDGER_TRANSACTION} "
                 "(t_type) VALUES (:itype);")
        cursor = await con.execute(query, self._trans)
        return cursor.lastrowid, cursor.rowcount

    async def _insert_reference(self, con) -> tuple:
        """
        Insert the reference meta-data.

        :param com: The database connection object.
        :returns: The last row pk and the rowcount.
        :rtype: tuple
        """
        query = (f"INSERT INTO {self.db._T_LEDGER_REFERENCE} (r_type, number) "
                 "VALUES (:itype, :number);")
        cursor = await con.execute(query, self._ref)
        return cursor.lastrowid, cursor.rowcount

    async def _insert_header(self, con, fy1fk: int, fy2fk: int, trans_pk: int,
                             ref_pk: int) -> tuple:
        """
        Insert the ledger header data.

        :param com: The database connection object.
        :param int fy1fk: The fiscal year primary key.
        :param int fy2fk: The fiscal year primary key.
        :param int trans_pk: The ledger_transaction pk.
        :param int ref_pk: the ledger_reference pk.
        :returns: The last row pk and the rowcount.
        :rtype: tuple
        """
        self._header['fy1fk'] = fy1fk
        self._header['fy2fk'] = fy2fk
        self._header['ctime'] = badidatetime.datetime.now(self.db.utc_tzinfo)
        query = ("SELECT COALESCE(MAX(trans_id), 0) + 1 "
                 f"FROM {self.db._T_LEDGER_HEADER} WHERE fy1fk = :fy1fk;")
        cursor = await con.execute(query, self._header)
        row = await cursor.fetchone()
        self._header['trans_id'] = row[0]
        self._header['ltfk'] = trans_pk
        self._header['lrfk'] = ref_pk
        query = (f"INSERT INTO {self.db._T_LEDGER_HEADER} (fy1fk, fy2fk, "
                 "ltfk, lrfk, trans_id, date, memo, purge, ctime) "
                 "VALUES (:fy1fk, :fy2fk, :ltfk, :lrfk, :trans_id, :date, "
                 ":memo, :purge, :ctime);")
        cursor = await con.execute(query, self._header)
        return cursor.lastrowid, cursor.rowcount

    async def update_ledger_transaction(self, trans_id: int) -> int:
        """
        Update the ledger_transaction table.

        :param int trans_id: The transaction number of the transaction.
        :returns: The rowcount caused by the insert.
        :rtype: int
        """
        async with aiosqlite.connect(
            self.db.user_data_fullpath,
            detect_types=self.db._DETECT_TYPES) as con:
            await con.execute("PRAGMA foreign_keys=ON")
            self._header['trans_id'] = trans_id  # This is for the history

            try:
                await con.execute("BEGIN;")
                rowcount = 0
                query = ("SELECT lh.pk, lh.ltfk, lh.lrfk, fy.pk "
                         f"FROM {self.db._T_LEDGER_HEADER} AS lh "
                         f"JOIN {self.db._T_FISCAL_YEAR} AS fy "
                         "ON lh.fy1fk = fy.pk WHERE trans_id = ?;")
                cursor = await con.execute(query, (trans_id,))
                row = await cursor.fetchone()
                pk, ltfk, lrfk, fy1fk = row
                rowcount += await self._update_transaction(con, ltfk)
                rowcount += await self._update_reference(con, lrfk)
                rowcount += await self._update_header(con, pk)
                rowcount += await self._insert_ledger_history(con, pk, fy1fk)

                if (self._bank and self._bank['itype'] != 0
                    and self._bank['amount'] != 0):
                    rowcount += await self._update_bank(con, pk)
                    rowcount += await self._update_ledger_balances(
                        con, fy1fk, 1)

                if (self._coh and self._coh['itype'] != 0
                    and self._coh['amount'] != 0):
                    rowcount += await self._update_coh(con, pk)
                    rowcount += await self._update_ledger_balances(
                        con, fy1fk, 2)

                if (self._income and self._income['itype'] != 0
                    and self._income['amount'] != 0):
                    rowcount += await self._update_income(con, pk)
                    rowcount += await self._update_ledger_balances(
                        con, fy1fk, 3)

                if self._expenses:
                    rowcount += await self._update_expenses(con, pk)
                    rowcount += await self._update_ledger_balances(
                        con, fy1fk, 4)

                await con.commit()
                return rowcount
            except Exception as e:
                await con.rollback()
                self.db._log.exception("Error during ledger update.")
                raise

    async def _update_transaction(self, con, ltfk: int) -> int:
        """
        Update the transaction meta-data.

        :param com: The database connection object.
        :param int ltfk: The ledger_header foreigh key.
        :returns: The last row pk and the rowcount.
        :rtype: tuple
        """
        self._trans['ltfk'] = ltfk
        query = (f"UPDATE {self.db._T_LEDGER_TRANSACTION} "
                 "SET t_type = :itype WHERE pk = :ltfk;")
        cursor = await con.execute(query, self._trans)
        return cursor.rowcount

    async def _update_reference(self, con, lrfk: int) -> int:
        """
        Update the reference meta-data.

        :param com: The database connection object.
        :param int ltfk: The ledger_header foreigh key.
        :returns: The last row pk and the rowcount.
        :rtype: tuple
        """
        self._ref['lrfk'] = lrfk
        query = (f"UPDATE {self.db._T_LEDGER_REFERENCE} "
                 "SET r_type = :itype, number = :number WHERE pk = :lrfk;")
        cursor = await con.execute(query, self._ref)
        return cursor.rowcount

    async def _update_header(self, con, header_pk: int) -> int:
        """
        Update the ledger header data.

        :param com: The database connection object.
        :param int header_pk: The ledger_header pk.
        :returns: The last row pk and the rowcount.
        :rtype: int
        """
        self._header['pk'] = header_pk
        query = (f"UPDATE {self.db._T_LEDGER_HEADER} SET date = :date, "
                 "memo = :memo, purge = :purge WHERE pk = :pk;")
        cursor = await con.execute(query, self._header)
        return cursor.rowcount

    async def select_bank(self, pk: int) -> list:
        """
        Select a ledget_bank record based on the header pk.

        :param int pk: The ledger_header pk.
        :returns: A row of data relating to the ledger_header table.
        """
        query = f"SELECT * FROM {self.db._T_LEDGER_BANK} WHERE lhfk = ?;"
        return await self.db._do_select_query(query, (pk,))

    async def _insert_bank(self, con, header_pk: int) -> int:
        """
        Insert a ledger_bank record.

        :param com: The database connection object.
        :param int header_pk: The ledger_header pk.
        :returns: The rowcount.
        :rtype: int
        """
        self._bank['lhfk'] = header_pk
        query = (f"INSERT INTO {self.db._T_LEDGER_BANK} (lhfk, b_type, "
                 "amount) VALUES (:lhfk, :itype, :amount);")
        cursor = await con.execute(query, self._bank)
        return cursor.rowcount

    async def _update_bank(self, con, header_pk: int) -> int:
        """
        Update a ledger_bank record.

        :param com: The database connection object.
        :param int header_pk: The ledger_header pk.
        :returns: The rowcount.
        :rtype: int
        """
        self._bank['lhfk'] = header_pk
        query = (f"UPDATE {self.db._T_LEDGER_BANK} SET b_type = :itype, "
                 "amount = :amount WHERE lhfk = :lhfk")
        cursor = await con.execute(query, self._bank)
        return cursor.rowcount

    async def select_coh(self, pk: int) -> list:
        """
        Select the ledger_coh record based on the header pk.

        :param int pk: The ledger_header pk.
        :returns: A row of data relating to the ledger_header table.
        """
        query = f"SELECT * FROM {self.db._T_LEDGER_COH} WHERE lhfk = ?;"
        return await self.db._do_select_query(query, (pk,))

    async def _insert_coh(self, con, header_pk: int) -> int:
        """
        Insert a ledger_coh record.

        :param com: The database connection object.
        :param int header_pk: The ledger_header pk.
        :returns: The rowcount.
        :rtype: int
        """
        self._coh['lhfk'] = header_pk
        query = (f"INSERT INTO {self.db._T_LEDGER_COH} (lhfk, c_type, amount) "
                 "VALUES (:lhfk, :itype, :amount);")
        cursor = await con.execute(query, self._coh)
        return cursor.rowcount

    async def _update_coh(self, con, header_pk: int) -> int:
        """
        Update a ledger_coh record.

        :param com: The database connection object.
        :param int header_pk: The ledger_header pk.
        :returns: The rowcount.
        :rtype: int
        """
        self._coh['lhfk'] = header_pk
        query = (f"UPDATE {self.db._T_LEDGER_COH} SET c_type = :itype, "
                 "amount = :amount WHERE lhfk = :lhfk")
        cursor = await con.execute(query, self._coh)
        return cursor.rowcount

    async def select_income(self, pk: int) -> list:
        """
        Select the income record based on the header pk.

        :param int pk: The ledger_header pk.
        :returns: A row of data relating to the ledger_header table.
        """
        query = f"SELECT * FROM {self.db._T_LEDGER_INCOME} WHERE lhfk = ?;"
        return await self.db._do_select_query(query, (pk,))

    async def _insert_income(self, con, header_pk: int) -> int:
        """
        Insert a ledger_income record.

        :param com: The database connection object.
        :param int header_pk: The ledger_header pk.
        :returns: The rowcount.
        :rtype: int
        """
        self._income['lhfk'] = header_pk
        query = (f"INSERT INTO {self.db._T_LEDGER_INCOME} (lhfk, i_type, "
                 "amount) VALUES (:lhfk, :itype, :amount);")
        cursor = await con.execute(query, self._income)
        return cursor.rowcount

    async def _update_income(self, con, header_pk: int) -> int:
        """
        Update a ledger_income record.

        :param com: The database connection object.
        :param int header_pk: The ledger_header pk.
        :returns: The rowcount.
        :rtype: int
        """
        self._income['lhfk'] = header_pk
        query = (f"UPDATE {self.db._T_LEDGER_INCOME} SET i_type = :itype, "
                 "amount = :amount WHERE lhfk = :lhfk")
        cursor = await con.execute(query, self._income)
        return cursor.rowcount

    async def select_expenses(self, trans_id: int) -> list:
        """
        Select the expense records based on the header pk.

        :param int trans_id: The ledger_header transaction ID.
        :returns: A row of data relating to the ledger_header table.
        """
        query = (f"SELECT * FROM {self.db._V_LEDGER_EXPENSE} "
                 "WHERE trans_id = ?;")
        return await self.db._do_select_query(query, (trans_id,))

    async def _insert_expenses(self, con, header_pk: int) -> int:
        """
        Insert one or more ledger_expense records.

        :param com: The database connection object.
        :param int header_pk: The ledger_header pk.
        :returns: The rowcount.
        :rtype: int
        """
        rowcount = 0
        query = (f"INSERT INTO {self.db._T_LEDGER_EXPENSE} (lhfk, ftfk, "
                 "amount) VALUES (:lhfk, :ftfk, :amount);")
        fts = await self.db.select_from_field_type_table(tuple(self._expenses))
        flds = [row[1] for row in fts]
        has_fields = all([False for key in self._expenses if key not in flds])
        params = [{'lhfk': header_pk, 'ftfk': ft[0],
                   'amount': self._expenses[ft[1]]} for ft in fts]

        if not has_fields:
            raise ValueError("Expense fields missing in the "
                             f"'{self.db._T_FIELD_TYPE}' table.")

        if len(params) != len(self._expenses):
            raise ValueError("Invalid number of parameters for the query.")

        cursor = await con.executemany(query, params)
        return cursor.rowcount

    async def _update_expenses(self, con, header_pk: int) -> int:
        """
        Update one or more ledger_expense records.

        :param com: The database connection object.
        :param int header_pk: The ledger_header pk.
        :returns: The rowcount.
        :rtype: int
        """
        query = f"DELETE FROM {self.db._T_LEDGER_EXPENSE} WHERE lhfk = :lhfk;"
        await con.execute(query, {'lhfk': header_pk})
        return await self._insert_expenses(con, header_pk)

    async def select_ledger_history(self, *, history_id: int=None,
                                    trans_id: int=None) -> list:
        """
        Select the ledger_transaction_history by history_id  or trans_id
        or both.

        :param int history_id: The ID for this history transaction.
        :param int trans_id: The ID for the entire transaction.
        :returns The list of histories related to this tansaction ID.
        :rtype: list
        """
        where = ""
        params = ()

        if history_id is not None:
            where += "history_is = ?"
            params += (history_id,)

        if trans_id is not None:
            where += " AND trans_id = ?" if where else "trans_id = ?"
            params += (trans_id,)

        query = f"SELECT * FROM {self.db._V_LEDGER_HISTORY} WHERE {where};"
        return await self.db._do_select_query(query, params)

    async def _insert_ledger_history(self, con, header_pk: int, fy1fk: int
                                     ) -> int:
        """
        Insert into the ledger_transaction_history table.

        :param con: The database connection object.
        :param int header_pk: The ledger_header primary key.
        :param int fy1fk: The fiscal year primary key.
        :returns: The rowcount.
        :rtype: int
        """
        history = {'lhfk': header_pk, 'fy1fk': fy1fk}
        query = ("SELECT COALESCE(MAX(history_id), 0) + 1 "
                 f"FROM {self.db._T_LEDGER_TRANS_HISTORY} "
                 "WHERE fy1fk = :fy1fk;")
        cursor = await con.execute(query, history)
        row = await cursor.fetchone()
        history['history_id'] = row[0]
        history['trans_id'] = self._header['trans_id']
        history['mtime'] = badidatetime.datetime.now(self.db.utc_tzinfo)
        history['details'] = self._details
        query = (f"INSERT INTO {self.db._T_LEDGER_TRANS_HISTORY} ("
                 "lhfk, fy1fk, history_id, trans_id, details, mtime) VALUES ("
                 ":lhfk, :fy1fk, :history_id, :trans_id, :details, :mtime);")
        cursor = await con.execute(query, history)
        return cursor.rowcount

    async def select_transaction_balances(self, year: int, a_type: int=None
                                          ) -> list:
        """
        Select the ledger_balences record.

        :param int year: The fiscal year year.
        :param int a_type: The category where the balance is required.
        :returns The list of balances.
        :rtype: list
        """
        where = ""
        params = {'year': year}

        if a_type:
            where += " AND lb.a_type = :a_type"
            params.update({'a_type': a_type})

        query = ('SELECT fy.year, lb.a_type, lb.balance, lb.mtime '
                 f'FROM {self.db._T_LEDGER_BALANCES} AS lb '
                 f'JOIN {self.db._T_FISCAL_YEAR} AS fy ON fy.pk = lb.fy1fk;')
        return await self.db._do_select_query(query, params)

    async def _update_ledger_balances(self, con, fy1fk: int, a_type: int
                                      ) -> int:
        """
        Insert into the ledger_balances table.
        """
        def add_balance(a_type: int, balance: int) -> int:
            if a_type == 1:
                mul = 1 if self._bank['itype'] == 1 else -1
                balance += self._bank['amount'] * mul
            elif a_type == 2:
                mul = 1 if self._coh['itype'] == 1 else -1
                balance += self._coh['amount']
            elif a_type == 3:
                balance += self._income['amount']
            elif a_type == 4:
                balance += sum([v for v in self._expenses.values()])

            return balance

        params = {'fy1fk': fy1fk, 'a_type': a_type}
        query = (f"SELECT balance FROM {self.db._T_LEDGER_BALANCES} "
                 "WHERE fy1fk = :fy1fk AND a_type = :a_type;")
        row = await self.db._do_select_query(query, params)
        params['mtime'] = badidatetime.datetime.now(self.db.utc_tzinfo)

        if row:
            balance = add_balance(a_type, row[0][0])
            query = (f"UPDATE {self.db._T_LEDGER_BALANCES} "
                     "SET balance = :balance, mtime = :mtime "
                     "WHERE fy1fk = :fy1fk AND a_type = :a_type;")
        else:
            balance = add_balance(a_type, 0)
            query = (f"INSERT INTO {self.db._T_LEDGER_BALANCES} (fy1fk, "
                     "a_type, balance, mtime) "
                     "VALUES (:fy1fk, :a_type, :balance, :mtime);")

        params.update({'balance': balance})
        cursor = await con.execute(query, params)
        return cursor.rowcount
