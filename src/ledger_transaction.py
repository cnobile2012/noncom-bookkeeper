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
            self._expenses = data.get('expenses')

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

    # def revert_type_index(self, t_type: int, r_type: int) -> tuple:
    #     """
    #     Revert back to the panel view fields and value.

    #     :param int t_type: The transaction type.
    #     :param int r_type: The reference type.
    #     :returns: The field name and value.
    #     :rtype: tuple
    #     """

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
                if column == 'memo':
                    where = f"AND memo LIKE '%' || :{column} || '%' "
                else:
                    where = f"AND {column} = :{column} "
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
                header_pk, rc = await self._insert_header(con, year, trans_pk,
                                                          ref_pk)
                rowcount += rc

                if (self._bank and self._bank['itype'] != 0
                    and self._bank['amount'] is not None):
                    rowcount += await self._insert_bank(con, header_pk)

                if (self._coh and self._coh['itype'] != 0
                    and self._coh['amount'] != 0):
                    rowcount += await self._insert_coh(con, header_pk)

                if (self._income and self._income['itype'] != 0
                    and self._income['amount'] != 0):
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
        query = ("SELECT COALESCE(MAX(trans_id), 0) + 1 "
                 f"FROM {self.db._T_LEDGER_HEADER} WHERE fy1fk = :fy1fk;")
        cursor = await con.execute(query, self._header)
        row = await cursor.fetchone()
        self._header['trans_id'] = row[0]
        self._header['ltfk'] = trans_pk
        self._header['lrfk'] = ref_pk
        query = (f"INSERT INTO {self.db._T_LEDGER_HEADER} (fy1fk, fy2fk, "
                 "ltfk, lrfk, trans_id, date, memo, purge, ctime, mtime) "
                 "VALUES (:fy1fk, :fy2fk, :ltfk, :lrfk, :trans_id, :date, "
                 ":memo, :purge, :ctime, :mtime);")
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

            try:
                await con.execute("BEGIN;")
                rowcount = 0
                query = ("SELECT pk, ltfk, lrfk "
                         f"FROM {self.db._T_LEDGER_HEADER} "
                         "WHERE trans_id = ?;")
                cursor = await con.execute(query, (trans_id,))
                row = await cursor.fetchone()
                pk, ltfk, lrfk = row
                rowcount += await self._update_transaction(con, ltfk)
                rowcount += await self._update_reference(con, lrfk)
                rowcount += await self._update_header(con, pk)

                if (self._bank and self._bank['itype'] != 0
                    and self._bank['amount'] != 0):
                    rowcount += await self._update_bank(con, pk)

                if (self._coh and self._coh['itype'] != 0
                    and self._coh['amount'] != 0):
                    rowcount += await self._update_coh(con, pk)

                if (self._income and self._income['itype'] != 0
                    and self._income['amount'] != 0):
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
        self._header['mtime'] = badidatetime.datetime.now(self.db.utc_tzinfo)
        query = (f"UPDATE {self.db._T_LEDGER_HEADER} SET date = :date, "
                 "memo = :memo, purge = :purge, mtime = :mtime "
                 "WHERE pk = :pk;")
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
        self._bank['lhfk'] = header_pk
        query = (f"UPDATE {self.db._T_LEDGER_BANK} SET b_type = :itype, "
                 "amount = :amount, balance = :balance WHERE lhfk = :lhfk")
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
        query = (f"INSERT INTO {self.db._T_LEDGER_COH} (lhfk, c_type, amount, "
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
        self._coh['lhfk'] = header_pk
        query = (f"UPDATE {self.db._T_LEDGER_COH} SET c_type = :itype, "
                 "amount = :amount, balance = :balance WHERE lhfk = :lhfk")
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
        self._income['lhfk'] = header_pk
        query = (f"UPDATE {self.db._T_LEDGER_INCOME} SET i_type = :itype, "
                 "amount = :amount, balance = :balance WHERE lhfk = :lhfk")
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
        params = [{'lhfk': header_pk, 'ftfk': ft[0],
                   "amount": self._expenses[ft[1]]} for ft in fts]

        if params:
            cursor = await con.executemany(query, params)
            rowcount = cursor.rowcount

        return rowcount

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
