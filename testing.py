import requests
from datetime import datetime, timedelta
import time
from collections import deque
import pandas as pd
from riotwatcher import LolWatcher, ApiError

import boto3
from io import StringIO

# from awsglue.utils import getResolvedOptions
# import sys
# api_key1 = "RGAPI-01ca4b66-6034-4778-830a-0ae07d3e7cc2"
# watcher1 = LolWatcher(api_key1)
# headers1 = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
#     "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
#     "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
#     "Origin": "https://developer.riotgames.com",
#     "X-Riot-Token": api_key1
# }



# def getPlayers(region, tier, queue, division, headers, api_key):
#     url = f'https://{region}.api.riotgames.com/lol/league/v4/entries/{queue}/{tier}/{division}'
#     resp = requests.get(url, headers=headers)
#     data = resp.json()
#     list_of_summoner_id = []

#     for ids in data: 
#         summonerName = ids['summonerName']
#         list_of_summoner_id += [summonerName]
#     return list_of_summoner_id

# def getPuuid(summoner_id, region, watcher):  
#     try: 
#         information = watcher.summoner.by_name(region, summoner_id)
#     except: 
#         return ''
#     puuid = information['puuid']
#     return puuid

# def game_id(match_details): 
#     game_info = {}
#     game_info['matchId'] = match_details['metadata']['matchId']
#     for key in match_details['info'].keys(): 
#         if key == 'participants': 
#             continue
#         game_info[key] = match_details['info'][key]
#     return game_info
# def getRankId():
#     tiers = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
#     divisions = ['IV', 'III', 'II', 'I']

#     ranking = {'rankings': [], 'tier': [], 'division': [], 'rank_id': []}

#     rank_id = 0
#     for tier in tiers:
#         if tier in ['MASTER', 'GRANDMASTER', 'CHALLENGER']:
#             rank = tier
#             ranking['rankings'].append(rank)
#             ranking['rank_id'].append(rank_id)
#             ranking['division'].append('')
#             ranking['tier'].append(tier)
#             rank_id += 1
#         else:
#             for division in divisions:
#                 rank = tier + ' ' + division
#                 ranking['rankings'].append(rank)
#                 ranking['rank_id'].append(rank_id)
#                 ranking['division'].append(division)
#                 ranking['tier'].append(tier)
#                 rank_id += 1
#     return ranking

# def main (): 
#     region = 'na1'
#     tier = "IRON"
#     division = "IV"
#     api_key4 = 'RGAPI-c69ae76c-1ffa-485a-9bad-bc3d0c31356e'
#     watcher4 = LolWatcher(api_key4)
#     headers4 = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
#         "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
#         "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
#         "Origin": "https://developer.riotgames.com",
#         "X-Riot-Token": api_key4
#     }
#     ranks = getRankId()
#     tiers = ranks['tier']
#     divisions = ranks['division']
#     for i in range(len(ranks['rank_id'])): 
#         tier = tiers[i]
#         division = divisions[i]
#         print(tier + ' ' + division)



# if __name__ == '__main__': 
#     main()

