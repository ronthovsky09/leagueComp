import requests
from datetime import datetime, timedelta
import time
from collections import deque
import pandas as pd
from riotwatcher import LolWatcher, ApiError
# from awsglue.utils import getResolvedOptions
import sys

import time

# import psycopg2
# from sqlalchemy import create_engine

# args = getResolvedOptions(sys.argv, ['API_KEY'])
# api_key = args['API_KEY']

def getPlayers(region, tier, queue, division, headers, api_key):
    url = f'https://{region}.api.riotgames.com/lol/league/v4/entries/{queue}/{tier}/{division}'
    resp = requests.get(url, headers=headers)
    data = resp.json()
    list_of_summoner_id = []

    for ids in data: 
        summonerName = ids['summonerName']
        list_of_summoner_id += [summonerName]
    return list_of_summoner_id

"""This returns a list of PUUID, which requires multiple requests"""
# def getPuuid(list_of_summoner_id, region, watcher): 
#     list_of_puuid = []
#     for name in list_of_summoner_id: 
#         try: 
#             information = watcher.summoner.by_name(region, name)
#         except: 
#             continue
#         puuid = information['puuid']
#         list_of_puuid += [puuid]
#     return list_of_puuid

def getPuuid(summoner_id, region, watcher):  
    try: 
        information = watcher.summoner.by_name(region, summoner_id)
    except: 
        return ''
    puuid = information['puuid']
    return puuid

def getMatches(puuid, region, headers, watcher): 
    # Get the current date and time (now).
    startTime = datetime.now()

    # Subtract 3 days to get the end time.
    fourteen_days_ago = startTime - timedelta(days=14)
    startTime = int(fourteen_days_ago.timestamp())
    
    if region == 'na1':
        # print('Puuid:', puuid)
        # print('API key:', headers['X-Riot-Token'])

        url = 'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{}/ids?startTime={}&queue=420&start=0&count=100&api_key={}'.format(puuid, startTime, headers['X-Riot-Token'])
        success = False
        
        while not success:
            resp = requests.get(url = url, headers = headers)
            if resp.status_code == 429:  # If rate limit is exceeded
                retry_after = int(resp.headers['Retry-After'])  # Extract the value of 'Retry-After' from the headers
                time.sleep(retry_after)  # Sleep for 'Retry-After' seconds
            else:
                success = True

        data = resp.json()
        
        time.sleep(1.2)  # Add delay to respect long-term rate limit
        
    return data

def getMatchInfo(region, game_id, api):
    success = False
    while not success:
        try:
            url = f'https://americas.api.riotgames.com/lol/match/v5/matches/{game_id}?api_key={api}'
            resp = requests.get(url = url)
            match_details = resp.json()
            success = True
        except Exception as e:
            print(f"Error getting match info for game_id {game_id}: {e}")
            time.sleep(5)  # Sleep for 5 seconds before retrying

    time.sleep(1.2)  # Add delay to respect long-term rate limit

    return match_details


# def get_match_info(match, region, api_key, rank, watcher):
    # Initialize with a sample match to get a base set of keys
    match_detail = watcher.match.by_id(region, match)
    key_list = list(match_detail['info']['participants'][0].keys())
    match_info = {}
    for key in key_list:
        match_info[key] = []
    
    # Initialize additional columns
    match_info['gameVersion'] = []
    match_info['timestamp'] = []
    match_info['gameDuration'] = []
    match_info['ranks'] = []

    participants = match_detail['info']['participants']
    for participant in participants:
        # For each participant, if a new key is discovered, initialize it with 'NA's for all previous matches
        for key in participant.keys():
            if key not in match_info:
                match_info[key] = ['NA'] * len(match_info['ranks'])

        # Append game version, timestamp, and game duration
        match_info['gameVersion'].append(match_detail['info']['gameVersion'])
        match_info['timestamp'].append(match_detail['info']['gameEndTimestamp'])
        match_info['gameDuration'].append(match_detail['info']['gameDuration'])

        # Handle challenges dictionary
        challenges = participant.get('challenges', {})
        for key, value in challenges.items():
            if key not in match_info:
                match_info[key] = ['NA'] * len(match_info['ranks'])
            match_info[key].append(value)

        for key in match_info:
            if key in ['gameVersion', 'timestamp', 'gameDuration', 'ranks', 'challenges']:
                continue
            else:
                # Use get method with default value of 'NA'
                match_info[key].append(participant.get(key, 'NA'))

    match_info['ranks'].append(rank)

    return match_info  # Return match info for a single match
def get_match_info(match_details):
    match_df = {}
    my_list = match_details['info']['participants']
    # Handling the main keys
    for item in my_list:
        for key, value in item.items():
            if key == 'challenges' or key == 'perks':
                continue
            if key not in match_df:
                match_df[key] = []  # Initialize as an empty list
            match_df[key].append(value)  # Append value to the list

    # Handling the 'challenges' key
    challenge_keys = set(key for item in my_list if 'challenges' in item for key in item['challenges'])
    for key in challenge_keys:
        if key not in match_df:
            match_df[key] = []  # Initialize as an empty list
        for item in my_list:
            if key not in ['killingSprees', 'turretTakedowns']:
                match_df[key].append(item['challenges'].get(key, 0))  # Append value or 0 to the list if key exists

    match_df['matchId'] = match_details['metadata']['matchId']
    return match_df

def game_id(match_details): 
    game_info = {}
    # game_info['matchId'] = match_details['metadata']['matchId']
    for key in match_details['info'].keys(): 
        if key == 'participants': 
            continue
        game_info[key] = match_details['info'][key]
    return game_info

def crawlExtract(summoner_ids, max_depth, region, tier, division, api_dict, match_limit=1000):
    visited_matches = {}  # To keep track of visited matches, now as dictionary
    player_index = 0  # Start with the first player in summoner_ids

    # Initialize player info dictionary
    player_info = {'player_id': [], 'rank': [], 'division': [], 'tier': []}
    rank = tier + ' ' + division

    all_match_info = []  # Initialize an empty list to store all match info

    match_count = 0  # Track number of matches processed

    while player_index < len(summoner_ids) and match_count < match_limit:
        player_id = summoner_ids[player_index]

        api_key = api_dict['api2']['api']  # Get the API key from the API dictionary
        watcher = api_dict['api2']['watcher']  # Get the watcher from the API dictionary
        headers = api_dict['api2']['headers']  # Get the headers from the API dictionary
        puuid = getPuuid(summoner_id=player_id, region=region, watcher=watcher)

        if puuid == '':
            player_index += 1  # Move to the next summoner ID
            continue

        visited_players = set()  # To keep track of visited players

        # Initialize queue for BFS with the initial player and depth 0
        queue = deque([(player_id, 0)])

        while queue and match_count < match_limit:
            player_id, depth = queue.popleft()  # Dequeue a player from queue

            # If we've reached the max_depth, we stop
            if depth > max_depth:
                break

            # If player hasn't been visited yet
            if player_id not in visited_players:
                visited_players.add(player_id)  # Mark as visited

                matches = getMatches(puuid=puuid, region=region, headers=headers, watcher=watcher)  # Get matches for this player

                for match in matches:
                    if match not in visited_matches:  # If match hasn't been visited yet
                        details = getMatchInfo(region=region, game_id=match, api=api_dict['api3']['api'])
                        game_details = game_id(details)  # Using the game_id function to get detailed information
                        visited_matches[match] = game_details  # Store match details instead of just the ID
                        player_ids = details['metadata']['participants']  # Get players from the match

                        # Enqueue all new players (with incremented depth) to be processed in the next iterations
                        for new_player_id in player_ids:
                            queue.append((new_player_id, depth + 1))
                            player_info['player_id'].append(new_player_id)
                            player_info['rank'].append(rank)
                            player_info['division'].append(division)
                            player_info['tier'].append(tier)

                        # Get match info for current match and store in list
                        match_info = get_match_info(match_details = details)
                        all_match_info.append(match_info)  # Append match info to the list

                        # Increase match count
                        match_count += 1
                    if match_count >= match_limit:
                        break

            # If queue is empty (meaning we've exhausted the network of the current player)
            # and we still haven't reached match_limit
            if not queue and match_count < match_limit:
                break  # Break the inner loop

        player_index += 1  # Move to the next summoner ID

    return player_info, visited_matches, all_match_info  # Return player info, list of unique matches, and all match info


def getRankId():
    tiers = ['IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER']
    divisions = ['IV', 'III', 'II', 'I']

    ranking = {'rankings': [], 'tier': [], 'division': [], 'rank_id': []}

    rank_id = 0
    for tier in tiers:
        if tier in ['MASTER', 'GRANDMASTER', 'CHALLENGER']:
            rank = tier
            ranking['rankings'].append(rank)
            ranking['rank_id'].append(rank_id)
            ranking['division'].append('')
            ranking['tier'].append(tier)
            rank_id += 1
        else:
            for division in divisions:
                rank = tier + ' ' + division
                ranking['rankings'].append(rank)
                ranking['rank_id'].append(rank_id)
                ranking['division'].append(division)
                ranking['tier'].append(tier)
                rank_id += 1
    return ranking


def main():
    max_depth = 10
    region = "na1"
    # matthew01px2017
    api_key1 = "RGAPI-4fb45f07-bcda-41d5-9373-ad3345082e2d"
    watcher1 = LolWatcher(api_key1)
    headers1 = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": api_key1
    }

    # ronthovsky09
    api_key2 = 'RGAPI-643c3b43-98fc-4e43-a8e2-fbdb71d53dbf'
    watcher2 = LolWatcher(api_key2)
    headers2 = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": api_key2
    }
    # ronthovsky08
    api_key3 = 'RGAPI-786711a1-d9ec-4c07-8d54-3df22b5e0250'
    watcher3 = LolWatcher(api_key3)
    headers3 = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": api_key3
    }

    # tungmatt
    api_key4 = 'RGAPI-c69ae76c-1ffa-485a-9bad-bc3d0c31356e'
    watcher4 = LolWatcher(api_key4)
    headers4 = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": api_key4
    }

    api_dict = {
        'api1': {
            'api': api_key1,
            'watcher': watcher1,
            'headers': headers1
        },
        'api2': {
            'api': api_key2,
            'watcher': watcher2,
            'headers': headers2
        },
        'api3': {
            'api': api_key3,
            'watcher': watcher3,
            'headers': headers3
        },
        'api4': {
            'api': api_key4,
            'watcher': watcher4,
            'headers': headers4
        }
    }
    queue = 'RANKED_SOLO_5x5'
    match_limit = 5

    ranks = getRankId()
    # for testing control
    tier_count = 0
    tiers = ranks['tier']
    divisions = ranks['division']
    for i in range(len(ranks['rank_id'])):
        tier = tiers[i]
        division = divisions[i]
        players = getPlayers(region=region, tier=tier, queue=queue, division=division, headers=headers1,
                                api_key=api_key1)
        # print(players)
        player_info, visited_matches, match_info = crawlExtract(summoner_ids = players, max_depth=max_depth,
                                                                region=region, tier=tier, division=division,
                                                                api_dict=api_dict, match_limit=match_limit)
        visited_matches_list = [{'game_id': game_id, **details} for game_id, details in visited_matches.items()]
        visited_matches_df = pd.DataFrame(visited_matches_list)
        player_info = pd.DataFrame(player_info)
        visited_matches = pd.DataFrame(visited_matches)
        match_info = pd.DataFrame(match_info)
        player_info.to_csv('/Users/ronthovsky09/Desktop/riot_api_testing/' + 'player_info_' + tier + division + '.csv',
                            index=False)
        visited_matches_df.to_csv('/Users/ronthovsky09/Desktop/riot_api_testing/' + 'visited_mathces_' + tier + division + '.csv',
                                index=False)
        match_info.to_csv('/Users/ronthovsky09/Desktop/riot_api_testing/' + 'match_info_' + tier + division + '.csv',
                            index=False)
        print(tier, division)
        if tier == "BRONZE" and division == 'I': 
            break


if __name__ == '__main__':
    main()
