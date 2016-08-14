#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon
import joseerror as je

import time
import pickle
from random import SystemRandom
random = SystemRandom()

import random as normal_random
from itertools import combinations

NORMAL_CP = 50

DEUSESMON_GO_HT = '''Deusesmon GO - The Gueime

Toda mensagem enviada tem 1% de chance de aparecer um Deus, o josé te
enviará uma mention no canal #deusesmongo e você terá 3 comandos para enviar,
com um timeout de 30 segundos entre cada comando(o comando será identificado
somente se for seu e somente no canal, ou seja, mensagens em qualquer outro
canal serão ignoradas)

Os comandos são "capturar", "doce" e "fugir"
`capturar` - utilizará uma Hóstia(PokéBola) para capturar o Deus que está na sua frente
`doce` - utilizará um Doce do seu inventário para aumentar suas chances de capturar o Deus
`fugir` - seu cagão.

Até agora é só isso mesmo, beijos <3
'''

'''
    bad CP => 100
    good CP => 600+
'''

dgo_data = {
    1: ['Deus',     (NORMAL_CP      , 600)],
    2: ['Belzebu',  (NORMAL_CP      , 500)],
    3: ['Zeus',     (NORMAL_CP      , 450)],
    4: ['Thor',     (NORMAL_CP      , 500)],
    5: ['Apolo',    (NORMAL_CP      , 500)],
    6: ['Hélio',    (NORMAL_CP      , 500)],
    7: ['Hércules', (NORMAL_CP      , 500)],
    8: ['Dionísio', (NORMAL_CP - 200, 500)],
    9: ['Hades',    (NORMAL_CP      , 400)],
}

items = {
    0: ("Hóstias",  0.8),  # 80%
    1: ("Poção",    0.1),  # 10%
    2: ("Incenso",  0.01), # 1%
    3: ("Doces",    0.28), # 28%
    4: ("Lure",     0.05), # 5%
}

RARE_PROB = 0.01
RARE_DEUSES = list(range(4))

COMMON_PROB = 0.1
COMMON_DEUSES = list(range(5,9+1))

class Item(object):
    def __init__(self, itemid):
        self.id = itemid
        item = items[itemid]
        self.name = item[0]
        self.prob = item[1]
    def __str__(self):
        return self.name


async def calc_iv(cp, pr):
    # calculate [ATK, DEF, STA]
    comb = [(a, b, c) for a, b, c in combinations(range(15),3) if (a > 4) and (b > 4) and (c > 4)]
    base = cp * (pr * (cp / 3))
    normal_random.seed(base)
    return normal_random.choice(comb)

class Deusmon:
    def __init__(self, did):
        self.id = did
        self.data = dgo_data[did]
        self.name = self.data[0]
        self.combat_power = random.randint(self.data[1][0], self.data[1][1])
        self.candies = 0
        self.base = 0.4
    def __str__(self):
        return '%s CP %d' % (self.name, self.combat_power)
    def calc_catch(self):
        return (self.base - (0.02 * (self.combat_power % 10))) + (0.1 * self.candies)
    async def process_candy(self):
        self.candies += 1
        return self.candies

async def create_deusmon(did):
    d = Deusmon(did)
    d.iv = await calc_iv(d.combat_power, d.calc_catch())
    return d

async def make_encounter():
    did = 0
    p = random.random()
    if p < RARE_PROB:
        did = random.choice(RARE_DEUSES)
    elif p < COMMON_PROB:
        did = random.choice(COMMON_DEUSES)
    else:
        did = random.choice(COMMON_DEUSES)

    d = await create_deusmon(did)
    return d

class JoseGames(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)
        self.db = {}
        self.encounters = {}
        self.load_flag = False
        self.cooldowns = {}

    async def ext_load(self):
        try:
            self.load_flag = True
            self.db = pickle.load(open('ext/d-go.db', 'rb'))
            self.load_flag = False
            return True, ''
        except Exception as e:
            return False, repr(e)

    async def ext_unload(self):
        try:
            self.load_flag = True
            pickle.dump(self.db, open('ext/d-go.db', 'wb'))
            self.load_flag = False
            return True, ''
        except Exception as e:
            return False, repr(e)

    async def c_dgoinit(self, message, args):
        '''`!dgoinit` - inicia uma conta no Deusesmon GO'''
        if message.author.id in self.db:
            await self.say("conta já existe")
            return

        self.db[message.author.id] = {
            'xp': 0,
            'level': 1,
            'inv': [
                [50, Item(0)], # 50 Balls
                [5, Item(1)], # 5 Potions
                [1, Item(2)], # 1 Incense
                [10, Item(3)], # 10 Berry
                [1, Item(4)], # 1 Lure
            ],
            'dinv': [],
        }
        await self.say("conta criada para <@%s>!" % message.author.id)

    async def c_dgosave(self, message, args):
        done = await self.ext_unload()
        if done:
            await self.say("salvo.")
        elif not done[0]:
            await self.say("py_err: %s" % done[1])
        return

    async def c_dgoload(self, message, args):
        done = await self.ext_load()
        if done:
            await self.say("carregado.")
        elif not done[0]:
            await self.say("py_err: %s" % done[1])
        return

    async def c_dgostat(self, message, args):
        '''`!dgostat` - mostra os status do seu personagem'''
        if not message.author.id in self.db:
            await self.say("Conta não existe.")
            return

        player_data = self.db[message.author.id]

        res = ''
        res += '%s\n' % message.author
        res += 'Inventário:\n'
        for el in player_data['inv']:
            res += '\t%d %s\n' % (el[0], str(el[1]))

        res += 'Deuses:\n'
        for deus in sorted(player_data['dinv'], key=lambda x: -x.combat_power):
            res += '\t\t%s IV: %s\n' % (deus, str(deus.iv))

        res = '```%s```' % res
        await self.say(res)

    async def c_dstop(self, message, args):
        '''`!dstop` - te leva a uma DeusStop(cooldown de 5min)'''
        if message.author.id in self.cooldowns:
            # check time
            if time.time() > self.cooldowns[message.author.id]:
                del self.cooldowns[message.author.id]
            else:
                await self.say("Cooldown ainda não terminado(%.2fs)" % (self.cooldowns[message.author.id] - time.time()))
                return

        res = 'Itens ganhos:\n'
        player = self.db[message.author.id]
        for item_id in items:
            item = items[item_id]
            if random.random() < item[1]:
                quantity = random.randint(0,5)
                player['inv'][item_id][0] += quantity
                res += ' * %d %s\n' % (quantity, item[0])

        await self.say("```%s```" % res)

        # faz cooldown
        self.cooldowns[message.author.id] = time.time() + 300

    async def c_dgotrigger(self, message, args):
        await self.make_encounter_front(message)

    async def c_htdgo(self, message, args):
        await self.say(DEUSESMON_GO_HT)

    async def c_dgolure(self, message, args):
        if message.author.id not in self.db:
            await self.say("Conta não existe")
            return

        lures = self.db[message.author.id]['inv'][4]
        if lures[0] < 1:
            await self.say("Nenhuma Lure disponível")
            return

        lures[0] -= 1
        jcommon.DGO_PROB += 0.03 # 3% until reboot
        await self.say("Lure aplicado, probabilidade agora é de %.2f%%" % (jcommon.DGO_PROB * 100))

    async def make_encounter_front(self, message):
        if self.load_flag:
            return

        if message.author.id not in self.db:
            return

        if message.author.id in self.encounters:
            return

        dgo_channel = discord.utils.get(message.server.channels, name='deusesmongo')
        if dgo_channel is None:
            return

        deus = await make_encounter()
        if deus is None:
            return

        self.current = message
        self.current.channel = dgo_channel
        self.encounters[message.author.id] = deus

        encounter_message = ''
        encounter_message += '<@%s>: Deus encontrado!\n' % message.author.id
        encounter_message += '%s' % str(deus)
        await self.say(encounter_message)

        while True:
            player = self.db[message.author.id]
            cmd = await self.client.wait_for_message(timeout=30.0, author=message.author, channel=dgo_channel)
            if cmd is None:
                await self.say("%s: Deus fugiu(timeout)." % message.author)
                del self.encounters[message.author.id]
                break
            elif cmd.content.startswith('capturar'):
                # catch it
                if player['inv'][0][0] < 1:
                    await self.say("%s: Não possui nenhuma Hóstia disponível" % message.author)
                    break

                await self.say("Capturando...")
                player['inv'][0][0] -= 1

                await asyncio.sleep(2)
                gotit = await self.catch(deus)
                if gotit:
                    await self.say("%s: Parabéns, você conseguiu um %s" % (message.author, deus))
                    player['dinv'].append(deus)
                    del self.encounters[message.author.id]
                    break

                await self.say("%s: Não conseguiu" % message.author)
            elif cmd.content.startswith('doce'):
                # send a candy
                if player['inv'][3][0] < 1:
                    await self.say("%s: Não possui nenhum Doce disponível" % message.author)
                    break

                player['inv'][3][0] -= 1
                gotit = await deus.process_candy()
                if gotit:
                    await self.say("%s: Doce dado!" % message.author)
            elif cmd.content.startswith('fugir'):
                del self.encounters[message.author.id]
                await self.say("%s é cagao" % message.author)
                break
            else:
                await self.say("Comando não encontrado('capturar', 'doce' ou 'fugir' são válidos)")

        done = await self.ext_unload()
        if not done[0]:
            await self.say("py_err: %s" % done[1])
        self.current = message # reset channel hacking

    async def catch(self, deus):
        return random.random() < deus.calc_catch()