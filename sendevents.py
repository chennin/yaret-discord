#!/usr/bin/env python3
import discord
import os
import asyncio
#import aiomysql
import pymysql.cursors
from six.moves import configparser
import time
import logging
from discord.ext import tasks, commands

logging.basicConfig(level=logging.INFO)

# Read config file in
mydir = os.path.dirname(os.path.realpath(__file__))
configReader = configparser.RawConfigParser()
configReader.read(mydir + "/config.txt")

config = {}
for var in ["secret", "channel-na", "channel-eu", "channel-prime", "dbuser", "dbhost", "dbpass", "db"]:
  config[var] = configReader.get("YTD",var)

pausetime = 31
seentime = int(time.time())
channelid = {
  'na': config['channel-na'],
  'eu': config['channel-eu'],
  'prime': config['channel-prime']
}
#os.environ['TZ'] = 'UTC'

client = discord.Client()
#client = commands.Bot("!")

@client.event
async def on_ready():
    print('Logged in as ' + client.user.name + "#" + str(client.user.discriminator))
    await client.change_presence(activity=discord.Game(name='RIFT'))

@tasks.loop(seconds=pausetime)
async def send_new_events():
    global pausetime
    global seentime
    await client.wait_until_ready()
    if not client.is_closed():
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
              dischans = []
              for cid in channelid[result2['dc']].split(","):
                if not cid.isnumeric():
                  continue
                dischans.append(client.get_channel( int(cid) ))
              if not dischans:
                continue
              shardname = result2['name']
#              if result2['dc'] == "eu":
#                tags += ":flag_eu:"
#              if result2['dc'] == "na":
#                tags += ":flag_us:"
              if result2['pvp'] == 1:
                tags += ":crossed_swords:"
              
              sql = 'SELECT name FROM `zones` WHERE `lang` = "en_US" AND `id` = %s'
              #await cursor.execute(sql, newevent['zoneid'])
              #result2 = await cursor.fetchone()
              cursor2.execute(sql, newevent['zoneid'])
              result2 = cursor2.fetchone()
              zonename = result2['name']
              # Starfall zone IDs
              if newevent['zoneid'] in [788055204, 2007770238, 1208799201, 2066418614, 511816852]:
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
              elif newevent['eventid'] in list(range(206,212)):
                tags += ":mountain_snow:"
              # Hellbugs
              elif newevent['eventid'] in [157,159]:
                tags += ":bug:"
              # Unstables. Not 152!
              elif newevent['eventid'] in list(range(130,152)) + [153] + list(range(187,193)):
                tags += ":white_circle:"

              for channel in dischans:
                await channel.send('{!s} **{!s}** has started in **{!s}** on **{!s}**.'.format(tags, eventname, zonename, shardname))
        conn.close()
#        await asyncio.sleep(pausetime) # task runs every pausetime seconds

#send_new_events.before_loop(client.wait_until_ready())
send_new_events.start()
client.run(config['secret'])

##client.loop.create_task(send_new_events())
#run = True
#while run == True:
##  loop = asyncio.get_event_loop()
#  try:
##    loop.run_until_complete(client.start(config['secret']))
#    send_new_events.start()
#    client.run(config['secret'])
##    client.start(config['secret'])
#  except discord.LoginFailure:
#    print("Failed to log in")
#  except discord.GatewayNotFound:
#    print("Websocket gateway not found, is Discord down?")
#  except KeyboardInterrupt:
#    print("Logging out")
##    loop.run_until_complete(client.logout())
#    client.logout()
#    run = False
#  except (discord.Forbidden, discord.NotFound) as e:
#    print("Error {0}: {1}".format(e.reponse, e.message))
#    pass
#  except discord.HTTPException as e:
#    print("HTTP Error {0}: {1}".format(e.response.status, e.text))
#    client.close()
#    sleep(60)
#  except discord.ConnectionClosed as e:
#    print("Connection Error {0}: {1}".format(str(e.code), e.reason))
#    client.close()
#    sleep(60)
##  finally:
##    loop.close()
