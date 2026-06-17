# -*- coding: utf-8 -*-
#
# src/prep_and_cache.py
#
__docformat__ = "restructuredtext en"

import random

from string import ascii_lowercase, ascii_uppercase, digits


class Cache:
    """
    Write-through cache, loaded once at startup, persists for the app lifetime.
    Supports write-through DB updates.
    """
    ORG_FIELDS = ['longitude', 'location_city_name', 'latitude',
                  'locality_prefix', 'start_of_fiscal_year', 'locale_name',
                  'treasurer', 'total_membership', 'iana_name']
    ORG_FIELDS.sort()

    def __init__(self, db, *args, **kwargs) -> None:
        """
        Constructor

        :param object db: The database self object.
        """
        super().__init__(*args, **kwargs)
        self.db = db
        self._log = db._log
        self._flush_cache()

    @property
    def has_cache(self):
        return self._store != {}

    def _flush_cache(self) -> None:
        """
        Remove all data from the cache.
        """
        self._store: dict = {}
        self._year = None

    @property
    def key(self) -> str | None:
        return self._store.get('key')

    @key.setter
    def key(self, key: str) -> None:
        self._store['key'] = key

    @property
    def year(self) -> int | None:
        return self._year

    @year.setter
    def year(self, year: int) -> None:
        self._year = year

    async def load(self) -> None:
        """
        Call once at app startup to populate the cache from the DB.

        .. note::

           1. The `field_type` data is stored by the table name only.
           2. The `config_data` is stored by the year and table name.
           3. The `fiscal_year` data is stored by the year and table name.
           4. The `month`  data is stored by the year and table name.
           5. The `monthly`  data is stored by the year and table name.
        """
        # field_type  -- Also sets the year.
        await self._load_field_type()
        # month
        await self._load_month()
        # fiscal_year
        await self._load_fiscal_year()

        if self.year:
            # config_data
            await self._load_config_data()
            # monthly
            await self._load_monthly()
            self._log.info("Loaded cache with DB data, year set to %s.",
                           self.year)

        if self.has_cache:
            # Create a cache ID.
            rand = random.SystemRandom()
            domain = ascii_lowercase + ascii_uppercase + digits
            self.key = ''.join(rand.choice(domain) for i in range(9))

    async def _load_field_type(self) -> None:
        items = await self.db.select_from_field_type_table(None)

        if items:
            self._store[self.db._T_FIELD_TYPE] = items

    async def _load_month(self) -> None:
        items = await self.db.select_from_month_table()

        if items:
            self._store[self.db._T_MONTH] = items

    async def _load_fiscal_year(self) -> None:
        items = await self.db.select_from_fiscal_year_table()

        if isinstance(items, tuple):  # pragma: no cover
            items = [items]

        for fy in sorted(items, key=lambda x: x[1]):
            year = fy[1]

            if fy[4] == 1:  # Is current year
                self.year = year

            self._store[year] = {}
            self._store[year][self.db._T_FISCAL_YEAR] = [fy]

    async def _load_config_data(self) -> None:
        items = await self.db.select_from_config_data_table(
            self.fields, self.year)
        self._store[self.year][self.db._T_DATA] = items

    async def _load_monthly(self) -> None:
        items = await self.db.select_from_monthly_table(self.year)
        self._store[self.year][self.db._T_MONTHLY] = items

    @property
    def has_fields_data(self) -> bool:
        """
        Check that the cache has fields data.

        :returns: True if data has been saved in the cache and False if not
                  saved.
        :rtype: bool
        """
        return len(self._store.get(self.db._T_FIELD_TYPE, {})) > 0

    @property
    def has_organization_cache_data(self) -> bool:
        """
        Check that the cache has Organization data.

        :returns: True if data has been saved in the cache and False if not
                  saved.
        :rtype: bool
        """
        return len(self.get(self.db._T_DATA, r_type='organization')) > 0

    @property
    def has_budget_cache_data(self) -> bool:
        """
        Check that the cache has Budget data.

        :returns: True if data has been saved in the cache and False if not
                  saved.
        :rtype: bool
        """
        return len(self.get(self.db._T_DATA, r_type='budget')) > 0

    @property
    def has_fiscal_cache_data(self) -> bool:
        """
        Check that the cache has fiscal year data.

        :returns: True if data has been saved in the cache and False if not
                  saved.
        :rtype: bool
        """
        return len(self.get(self.db._T_FISCAL_YEAR)) > 0

    @property
    def has_month_cache_data(self) -> bool:
        """
        Check that the cache has month data.

        :returns: True if data has been saved in the cache and False if not
                  saved.
        :rtype: bool
        """
        return len(self.get(self.db._T_MONTH)) > 0

    @property
    def has_monthly_cache_data(self) -> bool:
        """
        Check that the cache has monthly data.

        :returns: True if data has been saved in the cache and False if not
                  saved.
        :rtype: bool
        """
        return len(self.get(self.db._T_MONTHLY)) > 0

    @property
    def fields(self):
        return [itm[1] for itm in self._store.get(self.db._T_FIELD_TYPE, ())]

    @property
    def get_bgt_fields(self):
        fields = self.fields
        bgt_fields = list(set(fields) - set(self.ORG_FIELDS)) if fields else []
        bgt_fields.sort()
        return bgt_fields

    @property
    def available_years(self):
        return [key for key in self._store.keys()
                if key not in (self.db._T_FIELD_TYPE, self.db._T_MONTH, 'key')]

    def get(self, table_name: str, *, year: int=None, r_type: str=None
            ) -> list:
        """
        Get records of the `table_name`. If a `r_type` is provided return
        just that record based on the `table_name` type.

        :param int year: The fiscal year.
        :param str table_name: The DB table to query.
        :param str r_type: This determines a specific record in the entity.
        :returns: Records based on the `table_name`.
        :rtype: list

        .. note::

           1. The `fields` data is accessed by the `fields` key.
           2. There are two types of `config_data` data.
              a. The `organization` data is accessed by the year, table name,
                 and type.
              b. The `budget` data is accessed by the year, table name, and
                 type.
           3. The `fiscal_year` data is accessed by the year and table name.
           4. The `month`  data is accessed by the year and table name.
           5. The `monthly`  data is accessed by the year and table name.
        """
        year = self.year if year is None else year

        match table_name:
            case self.db._T_FIELD_TYPE:
                data = self._store.get(self.db._T_FIELD_TYPE, [])
            case self.db._T_FISCAL_YEAR:
                data = self._store.get(year, {})
                data = data.get(self.db._T_FISCAL_YEAR, []) if data else []
            case self.db._T_DATA:
                items = self._store.get(year, {}).get(self.db._T_DATA, [])

                match r_type:
                    case 'organization':
                        fields = self.ORG_FIELDS
                    case 'budget':
                        fields = self.get_bgt_fields
                    case None:
                        # This will return all config_data for the given year.
                        fields = self.fields
                    case _:
                        assert r_type in ('organization', 'budget', None), (
                            f"Invalid `r_type`, found '{r_type}'.")

                data = [item for item in items if item[1] in fields]
            case self.db._T_MONTH:
                data = self._store.get(self.db._T_MONTH, [])
            case self.db._T_MONTHLY:
                data = self._store.get(year, {}).get(self.db._T_MONTHLY, [])

        self._log.info("Retrived '%s' data.", table_name)
        return data

    async def insert(self, table_name: str, record: dict) -> int:
        """
        Insert a new record into the DB and add it to the cache. All records
        are in a dict even if there is only one item thus keeping a uniform
        interface.

        :param str table_name: The DB table to query to insert into.
        :param dict data: The data to insert.
        :returns: The insertion rowcount.
        :rtype: int
        """
        data = record.get('data', [])

        match table_name:
            case self.db._T_FIELD_TYPE:
                # Name, now, now
                rowcount = await self.db.insert_into_field_type_table(data)
                await self._load_field_type()
            case self.db._T_MONTH:
                rowcount = await self.db.insert_into_month_table(data)
                await self._load_month()
            case self.db._T_FISCAL_YEAR:
                rowcount = await self.db.insert_into_fiscal_year_table(data)
                await self._load_fiscal_year()
            case self.db._T_DATA:
                year = record['year']
                month = record['month']
                rowcount = await self.db.insert_into_config_data_table(
                    year, month, data)
                await self._load_config_data()
            case self.db._T_MONTHLY:
                year = record['year']
                rowcount = await self.db.insert_into_monthly_table(year, data)
                await self._load_monthly()
            case _:
                self._log.error("Invalid table name %s.", table_name)
                rowcount = 0

        #print('POOP2', rowcount, table_name, self._log)
        self._log.info("Inserted %s row(s) into the %s table.",
                       rowcount, table_name)
        return rowcount

    async def update(self, table_name: str, changes: dict) -> int:
        """
        Update a record in the cache and push the change to the DB.

        :param str table_name: The DB table to update.
        :param dict changes: The data to update.
        :returns: The insertion rowcount.
        :rtype: int
        """
        data = changes.get('data')

        # Then persist to DB
        match table_name:
            # case self.db._T_FIELD_TYPE:
            # *** TODO *** What if a field name is spelled wrong and
            # needs to be fixed? How will that affect the whole system.
            case self.db._T_FISCAL_YEAR:
                rowcount = await self.db.update_fiscal_year_table(data)
                await self._load_fiscal_year()
            case self.db._T_DATA:
                rowcount = await self.db.update_config_data_table(data)
                await self._load_config_data()
            case self.db._T_MONTHLY:
                year = changes.get('year')
                rowcount = await self.db.update_monthly_table(year, data)
                await self._load_monthly()
            case _:
                self._log.error("Invalid table name %s.", table_name)
                rowcount = 0

        self._log.info("Updated data in the %s table.", table_name)
        return rowcount
