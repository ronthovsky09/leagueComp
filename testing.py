import requests
from datetime import datetime, timedelta
import time
from collections import deque
import pandas as pd
from riotwatcher import LolWatcher, ApiError
# from awsglue.utils import getResolvedOptions
import sys
api_key1 = "RGAPI-01ca4b66-6034-4778-830a-0ae07d3e7cc2"
watcher1 = LolWatcher(api_key1)
headers1 = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com",
    "X-Riot-Token": api_key1
}



def getPlayers(region, tier, queue, division, headers, api_key):
    url = f'https://{region}.api.riotgames.com/lol/league/v4/entries/{queue}/{tier}/{division}'
    resp = requests.get(url, headers=headers)
    data = resp.json()
    list_of_summoner_id = []

    for ids in data: 
        summonerName = ids['summonerName']
        list_of_summoner_id += [summonerName]
    return list_of_summoner_id

def getPuuid(summoner_id, region, watcher):  
    try: 
        information = watcher.summoner.by_name(region, summoner_id)
    except: 
        return ''
    puuid = information['puuid']
    return puuid


def main (): 
    region = 'na1'
    tier = "IRON"
    division = "IV"
    api_key1 = "RGAPI-01ca4b66-6034-4778-830a-0ae07d3e7cc2"
    watcher1 = LolWatcher(api_key1)
    headers1 = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": api_key1
    }
    players = getPlayers(region = region, tier = tier, queue = 'RANKED_SOLO_5x5', division = division, headers = headers1, api_key = api_key1)
    print(players[:4])
    for player in players[:4]:
        print(getPuuid(summoner_id = player, region = region, watcher = watcher1))

if __name__ == '__main__': 
    main()