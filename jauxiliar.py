#!/usr/bin/env python3

'''
jauxiliar.py - Auxiliar stuff for Jose modules
'''

import asyncio
import josecommon as jcommon
import jcoin.josecoin as jcoin
import joseerror as je
import json
import aiohttp
import decimal

RICH_TAX = decimal.Decimal(0.1)

class Auxiliar(jcommon.Extension):
    '''
    Auxiliar - auxiliar functions and modules
    All modules that inherit from this class have access to things that wouldn't
    be possible if they were inheriting from jcommon.Extension.

    For example josecoin, josecoin imports from josecommon, but if josecommon
    imported josecoin into its Extension class, it would make a circular import.
    '''
    def __init__(self, client):
        jcommon.Extension.__init__(self, client)
        self.jcommon = jcommon
        self.jcoin = jcoin

    def tbank_fmt(self, cxt):
        return 'tbank#%s' % (cxt.message.server.id)

    def ensure_tbank(self, tbank_id):
        if tbank_id not in self.jcoin.data:
            # type 1 account = taxbank
            self.jcoin.data[tbank_id] = self.jcoin.empty_acc(tbank_id, \
                decimal.Decimal("0"), 1)

    async def jc_control(self, id_user, amnt, ledger_path=None):
        return jcoin.transfer(id_user, jcoin.jose_id, amnt, ledger_path)

    async def jcoin_pricing(self, cxt, amount):
        # taxing
        # ensure taxbank exists
        amount = decimal.Decimal(amount)
        tbank_id = self.tbank_fmt(cxt)
        self.ensure_tbank(tbank_id)

        authorid = cxt.message.author.id
        if authorid not in self.jcoin.data:
            raise je.JoseCoinError("Account doesn't exist")

        # check if account is in top 10 most rich people
        sorted_data = sorted(self.jcoin.data, key=lambda userid: \
            self.jcoin.data[userid]['amount'], reverse=True)

        index = sorted_data.index(authorid)
        if index <= 10:
            amount += (amount * RICH_TAX)

        # make transfer
        res = self.jcoin.transfer(authorid, tbank_id, amount)
        if res[0]:
            return True
        else:
            raise je.JoseCoinError(res[1])

    async def json_load(self, string):
        future_json = self.loop.run_in_executor(None, json.loads, string)

        try:
            res = await future_json
        except Exception as err:
            raise je.JSONError("Error parsing JSON data")

        return res

    async def http_get(self, url, **kwargs):
        timeout = kwargs.get('timeout', 5)

        try:
            response = await asyncio.wait_for(aiohttp.request('GET', url), timeout)
            content = await response.text()
        except Exception as err:
            self.logger.error('http_get', exc_info=True)
            # bump it up through the chain
            raise err

        return content

    async def json_from_url(self, url, **kwargs):
        content = await self.http_get(url, **kwargs)
        data = await self.json_load(content)
        return data

    def server_from_name(self, name):
        return [s for s in self.client.servers if s.name == name]

    def member_from_name(self, name):
        return [m for m in self.client.get_all_members() if m.name == name]
