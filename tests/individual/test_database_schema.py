#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Test database schema.
#
__docformat__ = "restructuredtext en"

import os
import sys
import datetime as dtime
from zoneinfo import ZoneInfo

import asyncio
import aiosqlite

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

from badidatetime import UTC, datetime


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.append(BASE_DIR)


class DatabaseSchema:
    __YEAR = 'year'
    __MONTH = 'month'
    __FIELD_TYPE = 'field_type'
    __REPORT_TYPE = 'report_type'
    __DATA = 'data'
    __REPORT_PIVOT = 'report_pivot'
    _TABLE_SCHEMA = (
        (__YEAR,
         'pk INTEGER NOT NULL PRIMARY KEY',
         'start_date TEXT UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (__MONTH,
         'pk INTEGER NOT NULL PRIMARY KEY',
         'month TEXT UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (__FIELD_TYPE,
         'pk INTEGER NOT NULL PRIMARY KEY',
         'field TEXT UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (__REPORT_TYPE,
         'pk INTEGER NOT NULL PRIMARY KEY',
         'report TEXT UNIQUE NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL'),
        (__DATA,
         'pk INTEGER NOT NULL PRIMARY KEY',
         'value NOT NULL',
         'c_time TEXT NOT NULL',
         'm_time TEXT NOT NULL',
         'ffk INTEGER NOT NULL',
         'mfk INTEGER NOT NULL'),
        (__REPORT_PIVOT,
         'tpfk INTEGER NOT NULL', 'rfk INTERGER NOT NULL',
         f'FOREIGN KEY (rfk) REFERENCES {__REPORT_TYPE} (pk)'),
         )
    _DB_PATH = '/tmp/test_db.sqlite3'
    _MONTHS = (
        'Bahá', 'Jalál', 'Jamál', "'Aẓamat", 'Núr', 'Raḥmat', 'Kalimát',
        'Kamál', "Asmá'", "'Izzat", 'Mashíyyat', "'Ilm", 'Qudrat', 'Qawl',
        'Masá’il', 'Sharaf', 'Sulṭán', 'Mulk', 'Ayyám-i-Há', "'Alá'"
        )
    _FIELD_TYPES = (
        'administration', 'area_teaching_committee',
        "bahá'í_international_fund", 'cash_in_bank', "continental_bahá'í_fund",
        'education', 'end_of_month_cash_on_hand', 'locale_name',
        'locality_prefix', 'locality_prefix_month', 'monetary_contributions',
        'month', "national_bahá'í_fund", 'ocs_holdings', 'other_funds',
        'other_misc', 'outstanding_bills', 'participation', 'proclamation',
        "regional_bahá'í_center", "regional_bahá'í_fund", 'scolarships',
        "shrine_of_bahá", 'start_of_fiscal_year', 'teaching',
        'total_membership', 'total_membership_beginning_of_year',
        'total_membership_month', 'total_outstanding_bills_previous_year',
        'treasurer', 'treasurer_month'
        )
    _DATA = {'locality_prefix': '0',
             'total_membership': '15',
             'start_of_fiscal_year': '2023-05-01T00:00:00',
             'cash_in_bank': '1000.00',
             'month': 'Bahá',
             'total_membership_month': '16'}

    def __init__(self):
        self._year_data = []  # Updated later
        self.timezone = self.lat = self.lon = ''
        asyncio.run(self.start())

    async def start(self):
        year = 2023
        month = 'Bahá'
        address = 'Fuquay Varina'
        self.timezone, self.lat, self.lon = self._find_timezone(address)
        self._add_sun_set_datetimes(year)

        await self.create_db()
        if not await self._years: await self.add_years()
        if not await self._months: await self.add_months()
        if not await self._field_type: await self.add_field_type()
        if not await self._data: await self.add_data(month, self._DATA)

    async def create_db(self):
        async with aiosqlite.connect(self._DB_PATH) as db:
            for params in self._TABLE_SCHEMA:
                table = params[0]
                fields = ', '.join([field for field in params[1:]])
                query = f"CREATE TABLE IF NOT EXISTS {table}({fields})"
                await db.execute(query)
                await db.commit()

    @property
    async def _years(self):
        query = f"SELECT * FROM {self.__YEAR}"
        values = await self._do_select_query(query)
        return len(values)

    async def add_years(self):
        now = dtime.datetime.now(UTC).isoformat()
        data = [(year, now, now) for year in self._year_data]
        query = (f"INSERT INTO {self.__YEAR} (start_date, c_time, m_time) "
                 "VALUES (?, ?, ?)")
        await self._do_insert_query(query, data)

    @property
    async def _months(self):
        query = f"SELECT * FROM {self.__MONTH}"
        values = await self._do_select_query(query)
        return len(values)

    async def add_months(self):
        now = dtime.datetime.now(UTC).isoformat()
        data = [(month, now, now) for month in self._MONTHS]
        query = (f"INSERT INTO {self.__MONTH} (month, c_time, m_time) "
                 "VALUES (?, ?, ?)")
        await self._do_insert_query(query, data)

    @property
    async def _field_type(self):
        query = f"SELECT * FROM {self.__FIELD_TYPE}"
        values = await self._do_select_query(query)
        return len(values)

    async def add_field_type(self):
        now = dtime.datetime.now(UTC).isoformat()
        data = [(month, now, now) for month in self._FIELD_TYPES]
        query = (f"INSERT INTO {self.__FIELD_TYPE} (field, c_time, m_time) "
                 "VALUES (?, ?, ?)")
        await self._do_insert_query(query, data)

    @property
    async def _data(self):
        query = f"SELECT * FROM {self.__DATA}"
        values = await self._do_select_query(query)
        return len(values)

    async def add_data(self, month: int, data: dict) -> list:
        query = (f"INSERT INTO {self.__DATA} (value, c_time, m_time, ffk, mfk)"
                 " VALUES (?, ?, ?, "
                 f"(SELECT pk FROM {self.__FIELD_TYPE} WHERE field = ?), "
                 f"(SELECT pk FROM {self.__MONTH} WHERE month = ?))")
        now = dtime.datetime.now(UTC).isoformat()
        items = [(value, now, now, field, month)
                 for field, value in data.items()]
        await self._do_insert_query(query, items)

    async def _get_current_year(self, year: int) -> list:
        query = f"SELECT * FROM {self.__YEAR} WHERE start_date LIKE ?"
        return await self._do_select_query(query, params=(f"{year}%",))

    async def _get_current_month(self, month: str) -> list:
        query = f"SELECT * FROM {self.__MONTH} WHERE month = ?"
        return await self._do_select_query(query, params=(month,))

    async def _do_select_query(self, query: str, params: tuple=()) -> list:
        async with aiosqlite.connect(self._DB_PATH) as db:
            async with db.execute(query, params) as cursor:
                values = await cursor.fetchall()

        return values

    async def _do_insert_query(self, query: str, data: list) -> None:
        async with aiosqlite.connect(self._DB_PATH) as db:
            await db.executemany(query, data)
            await db.commit()

    def _find_timezone(self, address):
        geolocator = Nominatim(user_agent='nc-bookkeeper')
        location = geolocator.geocode(address)

        if location:
            raw = location.raw
            lat = float(raw['lat'])
            lon = float(raw['lon'])
            tf = TimezoneFinder()
            iana = tf.timezone_at(lng=lon, lat=lat)

        return iana, lat, lon

    def _local_to_utc_time(self, dt):
        local_tz = ZoneInfo(self.timezone)
        local_dt = dt.replace(tzinfo=local_tz)
        return local_dt.astimezone(UTC)

    def remove_database(self):
        os.remove(self._DB_PATH)


if __name__ == "__main__":
    ds = DatabaseSchema()
    #ds.remove_database()
