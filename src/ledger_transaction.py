# -*- coding: utf-8 -*-
#
# src/ledger_transaction.py
#
__docformat__ = "restructuredtext en"

import sqlite3
import aiosqlite
import badidatetime


class LedgerTransaction:
    """
    Handle all ledger transaction.
    """
    _TRANS_TYPES = ('contribution', 'distribution', 'expense')
    _REF_TYPES = ('ocs',)
    _BANK_TYPES = ('deposit', 'withdrawal')
    _COH_TYPES = ('replenishment', 'disbursement')
    _INCM_TYPES = ('local_fund', 'contributed_expense', 'misc')

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
            self._trans = self._make_types(data['transaction'],
                                           self._TRANS_TYPES)
            self._ref = self._make_types(data['reference'], self._REF_TYPES)
            self._header = data['panel']
            self._bank = self._make_types(data.get('bank'), self._BANK_TYPES)
            self._coh = self._make_types(data.get('coh'), self._COH_TYPES)
            self._income = self._make_types(data.get('income'),
                                            self._INCM_TYPES)
            self._expenses = data.get('expenses')

    def _make_types(self, data: dict, types: tuple) -> dict:
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

    async def select_ledger_transaction(self, year, *,
                                        date: badidatetime.date=None,
                                        trans_num: int=None, ck_num: str=None,
                                        rcpt_num: str=None, memo: str=None
                                        ) -> list:
        """
        Select a row from the vw_ledger_header view.

        :param int year: The fiscal year.
        :param badidatetime.date date: The Badí' date.
        :param int trans_num: The Transaction number.
        :param str ck_num: The check number.
        :param str rcpt_number: The receipt number.
        :param str memo: A partial string in the memo.
        :returns: The row of data.
        :rtype: list
        """
        if date:
            where = "AND ? = date"
            param = date
        elif trans_num:
            where = "AND ? = trans_num"
            param = trans_num
        elif ck_num:
            where = "AND ? = ref_ck_num"
            param = ck_num
        elif rcpt_num:
            where = "AND ? = ref_rcpt_num"
            param = rcpt_num
        elif memo:
            where = "AND memo LIKE '%' || ? || '%'"
            param = memo

        query = (f"SELECT * FROM {self.db._V_LEDGER_HEADER} WHERE "
                 f"fy1_year = ? {where};")
        return await self.db._do_select_query(query, (year, param,))

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
                header_pk, rc = await self._insert_header(con, year, trans_pk,
                                                          ref_pk)
                rowcount += rc

                if self._bank:
                    rowcount += await self._insert_bank(con, header_pk)

                if self._coh:
                    rowcount += await self._insert_coh(con, header_pk)

                if self._income:
                    rowcount += await self._insert_income(con, header_pk)

                if self._expenses:
                    rowcount += await self._insert_expenses(con, header_pk)

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
                 "(t_type, other) VALUES (:itype, :other);")
        cursor = await con.execute(query, self._trans)
        return cursor.lastrowid, cursor.rowcount

    async def _insert_reference(self, con) -> tuple:
        """
        Insert the reference meta-data.

        :param com: The database connection object.
        :returns: The last row pk and the rowcount.
        :rtype: tuple
        """
        query = (f"INSERT INTO {self.db._T_LEDGER_REFERENCE} (ck_num, "
                 "rcpt_num, r_type) VALUES (:check_number, :receipt_number, "
                 ":itype);")
        cursor = await con.execute(query, self._ref)
        return cursor.lastrowid, cursor.rowcount

    async def _insert_header(self, con, year: int, trans_pk: int, ref_pk: int
                             ) -> tuple:
        """
        Insert the ledger header data.

        :param com: The database connection object.
        :param int, year: The fiscal year to insert data for.
        :param int trans_pk: The ledger_transaction pk.
        :param int ref_pk: the ledger_reference pk.
        :returns: The last row pk and the rowcount.
        :rtype: tuple
        """
        now = badidatetime.datetime.now(self.db.utc_tzinfo)
        self._header['ctime'] = self._header['mtime'] = now
        fy = await self.db.select_from_fiscal_year_table(year=year)
        self._header['fy1fk'] = fy[0]
        fy = await self.db.select_from_fiscal_year_table(year=year + 1)
        self._header['fy2fk'] = fy[0]
        query = ("SELECT COALESCE(MAX(trans_num), 0) + 1 "
                 f"FROM {self.db._T_LEDGER_HEADER} WHERE fy1fk = :fy1fk;")
        cursor = await con.execute(query, self._header)
        row = await cursor.fetchone()
        self._header['trans_num'] = row[0]
        self._header['ltfk'] = trans_pk
        self._header['lrfk'] = ref_pk
        query = (f"INSERT INTO {self.db._T_LEDGER_HEADER} (fy1fk, fy2fk, "
                 "ltfk, lrfk, trans_num, date, memo, purged, ctime, mtime) "
                 "VALUES (:fy1fk, :fy2fk, :ltfk, :lrfk, :trans_num, :date, "
                 ":memo, :purged, :ctime, :mtime);")
        cursor = await con.execute(query, self._header)
        return cursor.lastrowid, cursor.rowcount

    async def update_ledger_transaction(self, trans_num: int) -> int:
        """
        Update the ledger_transaction table.

        :param int trans_num: The transaction number of the transaction.
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
                query = ("SELECT pk, ltfk, lrfk "
                         f"FROM {self.db._T_LEDGER_HEADER} "
                         "WHERE trans_num = ?;")
                cursor = await con.execute(query, (trans_num,))
                row = await cursor.fetchone()
                pk, ltfk, lrfk = row

                if self._trans:
                    rowcount += await self._update_transaction(con, ltfk)

                if self._ref:
                    rowcount += await self._update_reference(con, lrfk)

                if self._header:
                    rowcount += await self._update_header(con, pk)

                if self._bank:
                    rowcount += await self._update_bank(con, pk)

                if self._coh:
                    rowcount += await self._update_coh(con, pk)

                if self._income:
                    rowcount += await self._update_income(con, pk)

                if self._expenses:
                    rowcount += await self._update_expenses(con, pk)

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
        self._trans['pk'] = ltfk
        query = (f"UPDATE {self.db._T_LEDGER_TRANSACTION} "
                 "SET t_type = :itype, other = :other WHERE pk = :pk;")
        cursor = await con.execute(query, self._trans)
        return cursor.rowcount

    async def _update_reference(self, con, ltfk: int) -> int:
        """
        Update the reference meta-data.

        :param com: The database connection object.
        :param int ltfk: The ledger_header foreigh key.
        :returns: The last row pk and the rowcount.
        :rtype: tuple
        """
        self._ref['pk'] = ltfk
        query = (f"UPDATE {self.db._T_LEDGER_REFERENCE} "
                 "SET ck_num = :check_number, rcpt_num = :receipt_number, "
                 "r_type = :itype WHERE pk = :pk;")
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
        return 0

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
        query = (f"INSERT INTO {self.db._T_LEDGER_BANK} (lhfk, t_type, "
                 "amount, balance) VALUES (:lhfk, :itype, :amount, :balance);")
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
        return 0

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
        query = (f"INSERT INTO {self.db._T_LEDGER_COH} (lhfk, t_type, amount, "
                 "balance) VALUES (:lhfk, :itype, :amount, :balance);")
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
        return 0

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
        query = (f"INSERT INTO {self.db._T_LEDGER_INCOME} (lhfk, t_type, "
                 "amount, balance) VALUES (:lhfk, :itype, :amount, :balance);")
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
        return 0

    async def select_expenses(self, pk: int) -> list:
        """
        Select the expense records based on the header pk.

        :param int pk: The ledger_header pk.
        :returns: A row of data relating to the ledger_header table.
        """
        query = f"SELECT * FROM {self.db._V_LEDGER_EXPENSE} WHERE lhfk = ?;"
        return await self.db._do_select_query(query, (pk,))

    async def _insert_expenses(self, con, header_pk: int) -> int:
        """
        Insert one or more ledger_expense records.

        :param com: The database connection object.
        :param int header_pk: The ledger_header pk.
        :returns: The rowcount.
        :rtype: int
        """
        rowcount = 0
        params = {}
        params['lhfk'] = header_pk
        query = (f"INSERT INTO {self.db._T_LEDGER_EXPENSE} (lhfk, ftfk, "
                 "amount) VALUES (:lhfk, :ftfk, :amount);")
        fts = await self.db.select_from_field_type_table(tuple(self._expenses))

        for ft in fts:
            params['ftfk'] = ft[0]
            params['amount'] = self._expenses[ft[1]]
            cursor = await con.execute(query, params)
            rowcount += cursor.rowcount

        return rowcount

    async def _update_expenses(self, con, header_pk: int) -> int:
        """
        Update one or more ledger_expense records.

        :param com: The database connection object.
        :param int header_pk: The ledger_header pk.
        :returns: The rowcount.
        :rtype: int
        """
        return 0
