#!/usr/bin/env python3
import discord
import os
import asyncio
#import aiomysql
import pymysql.cursors
from six.moves import configparser
import time

# Read config file in
mydir = os.path.dirname(os.path.realpath(__file__))
configReader = configparser.RawConfigParser()
configReader.read(mydir + "/config.txt")

config = {}
for var in ["secret", "channel-na", "channel-eu", "dbuser", "dbhost", "dbpass", "db"]:
  config[var] = configReader.get("YTD",var)

pausetime = 60
seentime = int(time.time())
channelid = {
  'na': config['channel-na'],
  'eu': config['channel-eu']
}
#os.environ['TZ'] = 'UTC'

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as ' + client.user.name + "#" + str(client.user.discriminator))

async def send_new_events():
    global pausetime
    global seentime
    await client.wait_until_ready()
    while not client.is_closed:
#      async with aiomysql.connect(...?) as conn:
        conn = pymysql.connect(host=config['dbhost'], user=config['dbuser'], password=config['dbpass'], db=config['db'], charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor)
        print("Looking...")
        with conn.cursor() as cursor:
#        async with conn.cursor(aiomysql.DictCursor) as cursor:
            sql = 'SELECT * FROM `events` WHERE `endtime` = 0 AND `starttime` > %s'
            print(seentime)
            #await cursor.execute(sql, seentime)
            #result = await cursor.fetchall()
            cursor.execute(sql, (seentime))
            for newevent in cursor:
              print(newevent)
              # Update highest time seen
              if newevent['starttime'] > seentime:
                seentime = newevent['starttime']
              tags = ""
              cursor2 = conn.cursor()

              sql = 'SELECT name,dc,pvp FROM `shards` WHERE `id` = %s'
              #await cursor.execute(sql, newevent['shardid'])
              #result2 = await cursor.fetchone()
              cursor2.execute(sql, newevent['shardid'])
              result2 = cursor2.fetchone()
              shardname = result2['name']
              if result2['dc'] == "eu":
                tags += ":flag_eu:"
              if result2['dc'] == "na":
                tags += ":flag_us:"
              if result2['pvp'] == 1:
                tags += ":crossed_swords:"
              channel = discord.Object(id=channelid[result2['dc']])
              
              sql = 'SELECT name FROM `zones` WHERE `lang` = "en_US" AND `id` = %s'
              #await cursor.execute(sql, newevent['zoneid'])
              #result2 = await cursor.fetchone()
              cursor2.execute(sql, newevent['zoneid'])
              result2 = cursor2.fetchone()
              zonename = result2['name']
              # Starfall zone IDs
              if newevent['zoneid'] in [788055204, 2007770238, 1208799201, 2066418614]:
                tags += ":stars:"

              sql = 'SELECT name FROM `eventnames` WHERE `lang` = "en_US" AND `id` = %s'
              #await cursor.execute(sql, newevent['eventid'])
              #result2 = await cursor.fetchone()
              cursor2.execute(sql, newevent['eventid'])
              result2 = cursor2.fetchone()
              eventname = result2['name']
              # Xarth's Skull
              if newevent['eventid'] in [201, 202]:
                tags += ":european_castle:"

              await client.send_message(channel, '{!s} **{!s}** has started in **{!s}** on **{!s}**.'.format(tags, eventname, zonename, shardname))
        await asyncio.sleep(pausetime) # task runs every pausetime seconds

client.loop.create_task(send_new_events())
client.run(config['secret'])
