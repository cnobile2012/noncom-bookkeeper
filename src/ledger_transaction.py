# -*- coding: utf-8 -*-
#
# src/ledger_transaction.py
#
__docformat__ = "restructuredtext en"

import aiosqlite
import badidatetime


class LedgerTransaction:
    """
    Handle all ledger transaction.
    """

    def __init__(self, db, data: dict={}):
        """
        This constructor splits the data into the dicts needed by each
        insert or update method. It also handles selects on the ledger.
        """
        self.db = db

        if data:
            self._trans = data.get(db._T_LEDGER_TRANSACTION)
            self._ref = data.get(db._T_LEDGER_REFERENCE)
            self._header = data.get(db._T_LEDGER_HEADER)
            self._bank = data.get(db._T_LEDGER_BANK)
            self._coh = data.get(db._T_LEDGER_COH)
            self._income = data.get(db._T_LEDGER_INCOME)
            self._expense = data.get(db._T_LEDGER_EXPENSE)

    async def insert_full_ledger_transaction(self, year: int) -> int:
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
            rowcount = 0

            try:
                await con.execute("BEGIN;")
                trans_pk, rc = await self._insert_transaction(con)
                rowcount += rc
                ref_pk, rc = await self._insert_reference(con)
                rowcount += rc
                header_pk, rc = self._insert_header(con, year, trans_pk,
                                                    ref_pk)
                rowcount += rc

                if self._bank:
                    rowcount += await self._insert_bank(con, header_pk)
                elif self._coh:
                    rowcount += await self._insert_coh(con, header_pk)
                elif self._income:
                    rowcount += await self._insert_income(con, header_pk)
                elif self._expense:
                    rowcount += await self._insert_expense(con, header_pk)

                await con.commit()
            except Exception as e:
                await con.rollback()
                self._log.error("Error during ledger insert, %s",
                                e, exc_info=True)

        return rowcount

    async def _insert_transaction(self, con):
        query = (f"INSERT INTO {self.db._T_LEDGER_TRANSACTION} (type, other) "
                 "VALUES (:type, :other);")
        cursor = await con.execute(query, self._trans)
        return cursor.lastrowid, cursor.rowcount

    async def _insert_reference(self, con):
        query = (f"INSERT INTO {self.db._T_LEDGER_REFERENCE} (ck_num, "
                 "rcpt_num, type) VALUES (:ck_num, :rcpt_num, :type);")
        cursor = await con.execute(query, self._ref)
        return cursor.lastrowid, cursor.rowcount

    async def _insert_header(self, con, year: int, trans_pk: int, ref_pk: int):
        now = badidatetime.datetime.now(self.db.utc_tzinfo)
        self._header['ctime'] = self._header['mtime'] = now
        fy = await self.db.select_from_fiscal_year_table(year=year)
        self._header['fy1fk'] = fy[0]
        fy = await self.db.select_from_fiscal_year_table(year=year + 1)
        self._header['fy2fk'] = fy[0]
        query = ("SELECT COALESCE(MAX(trans_no), 0) + 1 "
                 f"FROM {self.db._T_LEDGER_HEADER} WHERE fy1fk = :fy1fk;")
        cursor = await con.execute(query, self._header)
        row = await cursor.fetchone()
        self._header['trans_no'] = row[0]
        self._header['ltfk'] = trans_pk
        self._header['lrfk'] = ref_pk
        query = (f"INSERT INTO {self.db._T_LEDGER_HEADER} (fy1fk, fy2fk, "
                 "ltfk, lrfk, trans_no, date, memo, purged, ctime, mtime) "
                 "VALUES (:fy1fk, :fy2fk, :ltfk, :lrfk, :trans_no, :date, "
                 ":memo, :purged, :ctime, :mtime);")
        cursor = await con.execute(query, self._header)
        return cursor.lastrowid, cursor.rowcount

    async def _insert_bank(self, con, header_pk: int) -> int:
        self._bank['lhfk'] = header_pk
        query = (f"INSERT INTO {self._T_LEDGER_BANK} (lhfk, type, amount, "
                 "balance) VALUES (:lhfk, :bank_type, :amount, :balance);")
        cursor = await con.execute(query, self._header)
        return cursor.rowcount

    async def _insert_coh(self, con, header_pk: int) -> int:
        self._coh['lhfk'] = header_pk
        query = (f"INSERT INTO {self._T_LEDGER_COH} (lhfk, type amount, "
                 "balance) VALUES (:lhfk, :coh_type, :amount, :balance);")
        cursor = await con.execute(query, self._header)
        return cursor.rowcount

    async def _insert_income(self, con, header_pk: int) -> int:
        self._income['lhfk'] = header_pk
        query = (f"INSERT INTO {self._T_LEDGER_INCOME} (lhfk, type amount, "
                 "balance) VALUES (:lhfk, :income_type, :amount, :balance);")
        cursor = await con.execute(query, self._header)
        return cursor.rowcount

    async def _insert_expense(self, con, header_pk: int) -> int:
        rowcount = 0
        params = {}
        params['lhfk'] = header_pk
        query = (f"INSERT INTO {self.db._T_LEDGER_EXPENSE} (lhfk, ftfk, "
                 "amount) VALUES (:lhfk, :ftfk, :amount);")
        fts = self.db.select_from_field_type_table(tuple(self._expense))

        for ft in fts:
            ft_pk = ft[0]
            field = ft[1]
            params['ftfk'] = ft_pk
            params['amount'] = self._expense[field]
            cursor = await con.execute(query, params)
            rowcount += cursor.rowcount

        return rowcount

