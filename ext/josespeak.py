#!/usr/bin/env python3

import discord
import asyncio
import sys
sys.path.append("..")
import josecommon as jcommon
import joseerror as je

import re
import random
import subprocess

def fixCaps(word):
    if word.isupper() and (word != "I" or word != "Eu"):
        word = word.lower()
    elif word [0].isupper():
        word = word.lower().capitalize()
    else:
        word = word.lower()
    return word

def toHashKey(lst):
    return tuple(lst)

def wordlist(filename):
    f = open(filename, 'r')
    wordlist = [fixCaps(w) for w in re.findall(r"[\w']+|[.,!?;]", f.read())]
    f.close()
    return wordlist

class Texter:
    def __init__(self, textpath, markov_length):
        self.tempMapping = {}
        self.mapping = {}
        self.starts = []

        self.build_mapping(wordlist(textpath), markov_length)

    def add_temp_mapping(self, history, word):
        while len(history) > 0:
            first = toHashKey(history)
            if first in self.tempMapping:
                if word in self.tempMapping[first]:
                    self.tempMapping[first][word] += 1.0
                else:
                    self.tempMapping[first][word] = 1.0
            else:
                self.tempMapping[first] = {}
                self.tempMapping[first][word] = 1.0
            history = history[1:]

    def build_mapping(self, wordlist, markovLength):
        self.starts.append(wordlist[0])
        for i in range(1, len(wordlist) - 1):
            if i <= markovLength:
                history = wordlist[: i + 1]
            else:
                history = wordlist[i - markovLength + 1 : i + 1]
            follow = wordlist[i + 1]
            # if the last elt was a period, add the next word to the start list
            if history[-1] == "." and follow not in ".,!?;":
                self.starts.append(follow)
            self.add_temp_mapping(history, follow)

        # Normalize the values in tempMapping, put them into mapping
        for first, followset in self.tempMapping.items():
            total = sum(followset.values())
            # Normalizing here:
            self.mapping[first] = dict([(k, v / total) for k, v in followset.items()])

    def next_word(self, prevList):
        sum = 0.0
        retval = ""
        index = random.random()
        # Shorten prevList until it's in mapping
        while toHashKey(prevList) not in self.mapping:
            prevList.pop(0)

        # Get a random word from the mapping, given prevList
        for k, v in self.mapping[toHashKey(prevList)].items():
            sum += v
            if sum >= index and retval == "":
                retval = k

        return retval

    async def gen_sentence(self, markovLength, word_limit):
        # Start with a random "starting word"
        curr = random.choice(self.starts)
        sent = curr.capitalize()
        prevList = [curr]
        word_count = 0
        # Keep adding words until we hit a period
        while (curr not in "."):
            if word_count > word_limit:
                break
            curr = self.next_word(prevList)
            prevList.append(curr)

            # if the prevList has gotten too long, trim it
            if len(prevList) > markovLength:
                prevList.pop(0)

            if (curr not in ".,!?;"):
                sent += " " # Add spaces between words (but not punctuation)

            sent += curr
            word_count += 1
        return sent

class JoseSpeak(jcommon.Extension):
    def __init__(self, cl):
        jcommon.Extension.__init__(self, cl)
        self.cult_generator = Texter('jose-data.txt', 1)
        self.serverzao_generator = Texter('zelao.txt', 1)

    async def ext_load(self):
        return True, ''

    async def speak(self, texter):
        res = await texter.gen_sentence(1, 100)
        if jcommon.DEMON_MODE:
            res = res[::-1]
        elif jcommon.PARABENS_MODE:
            res = 'Parabéns %s' % res
        await self.say(res)

    async def c_falar(self, message, args):
        """`!falar` - josé fala"""
        await self.speak(self.cult_generator)

    async def c_sfalar(self, message, args):
        """`!sfalar` - falar usando textos do serverzao"""
        await self.speak(self.serverzao_generator)

    async def c_josetxt(self, message, args):
        '''`!josetxt` - Mostra a quantidade de linhas, palavras e bytes no jose-data.txt
        '''
        output = subprocess.Popen(['wc', 'jose-data.txt'], stdout=subprocess.PIPE).communicate()[0]
        await self.say(output)
