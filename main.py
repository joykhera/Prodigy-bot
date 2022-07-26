import discord
import os
import datetime
from keep_alive import keep_alive
import copy
from replit import db
import yfinance as yf
import yahoo_fin.stock_info as si
import plotly.graph_objs as go
import time


client = discord.Client()
img_url = 'https://media.discordapp.net/attachments/1000044553086181436/1000237128053178438/IMG_0364.png'
default_embed = discord.Embed(title="Alert:", color=0x00ff00, timestamp=datetime.datetime.utcnow())
default_feilds = [':white_large_square: Ticker', ':blue_square: Entry',':green_square: Take Profit',':red_square: Stop Loss',':speech_balloon: Comments']
default_embed.set_thumbnail(url=img_url)
default_embed.set_footer(text='PRODIGY TRADING TEAM ANALYTICS', icon_url=img_url)
admins = [544931688283766784, 910965903905153087]

def add_channel(db_key, channel):
  if db_key in db.keys():
    channels = db[db_key]
    if channel not in channels: channels.append(channel)
    db[db_key] = channels
  else:
    db[db_key] = [channel]

def remove_channel(db_key, channel):
  if db_key in db.keys():
    channels = db[db_key]
    if channel in channels: channels.remove(channel)
    db[db_key] = channels
  

@client.event
async def on_ready():
  print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
  if message.author == client.user:
    return
    
  if message.content.lower().startswith('$a'):
    if message.channel.id in db['write_channels']:
      embed = copy.deepcopy(default_embed)
      embed.set_author(name=message.author, icon_url=client.user.avatar_url, url='https://discordapp.com/users/' + str(message.author.id))
      messageContent = message.content.split(',')

      if len(messageContent) >= 1: embed.add_field(name=':white_large_square: Ticker', value=messageContent[1].upper(), inline=True)
      if len(messageContent) >= 2: embed.add_field(name=':blue_square: Entry', value=messageContent[2], inline=True)
      if len(messageContent) >= 3: embed.add_field(name=':green_square: Take Profit', value=messageContent[3], inline=True)
      if len(messageContent) >= 4: embed.add_field(name=':red_square: Stop Loss', value=messageContent[4], inline=True)
      
      if message.content.lower().startswith('$ad'):
        ticker = messageContent[1].upper().strip()
        quote_table = si.get_quote_table(ticker)
        stats = si.get_stats(ticker)
        stats.set_index("Attribute", inplace=True)     

        embed.add_field(name=":brown_square: Current Price", value="$" + str(round(quote_table['Quote Price'], 2)), inline=True)
        embed.add_field(name=":purple_square: Volume", value=quote_table['Volume'], inline=True)
        embed.add_field(name=":yellow_square: Float", value=stats.loc['Float 8']["Value"], inline=True)
        embed.add_field(name=":white_square_button: 50 SMA", value=stats.loc['50-Day Moving Average 3']["Value"], inline=True)
        embed.add_field(name=":black_square_button: 200 SMA", value=stats.loc['200-Day Moving Average 3']["Value"], inline=True)
        if len(messageContent) >= 5: embed.add_field(name=':speech_balloon: Comments', value=messageContent[5], inline=True)

        data = yf.download(tickers=ticker, period = '1d', interval = '5m', rounding= True)
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=data.index,open = data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name = 'market data'))
        fig.update_layout(title = ticker + ' share price ' + str(quote_table['Quote Price']), yaxis_title = 'Stock Price (USD)')
        img_name = str(time.time())
        fig.write_image(img_name + ".png")
        embed.set_image(url='attachment://' + img_name + ".png")
        await broadcastWithFile(embed, img_name + ".png")
        os.remove(img_name + ".png")
      else:
        if len(messageContent) >= 5: embed.add_field(name=':speech_balloon: Comments', value=messageContent[5], inline=True)
        await broadcast(embed)
    else:
      await message.channel.send("Channel unauthorized")

  elif message.content.lower().startswith('$c'):
    if message.channel.id in db['write_channels']:
      embed = copy.deepcopy(default_embed)
      embed.set_author(name=message.author, icon_url=client.user.avatar_url, url='https://discordapp.com/users/' + str(message.author.id))
      messageContent = message.content.split(',')
      messageContent.pop(0)
  
      for content in messageContent:
        key = content.split('=')[0]
        value = content.split('=')[1]
  
        for field in default_feilds:
          if key in field: 
            key = field
            break
  
        embed.add_field(name=key, value=value, inline=False)
  
      await broadcast(embed)
    else:
      await message.channel.send("Channel unauthorized")

  elif message.content.lower().startswith('$nr'):
    if message.author.id in admins:
      if ',' in message.content:
        channel_id = message.content.split(',')[1].strip()
        add_channel('read_channels', int(channel_id))
        await message.channel.send(channel_id + " added to alerted channels")
      else:
        add_channel('read_channels', message.channel.id)
        await message.channel.send("This channel added to alerted channels")

  elif message.content.lower().startswith('$rr'):
    if message.author.id in admins:
      if ',' in message.content:
        channel_id = message.content.split(',')[1].strip()
        remove_channel('read_channels', int(channel_id))
        await message.channel.send(channel_id + " removed from alerted channels")
      else:
        remove_channel('read_channels', message.channel.id)
        await message.channel.send("This channel removed from alerted channels")

  elif message.content.lower().startswith('$nw'):
    if message.author.id in admins:
      if ',' in message.content:
        channel_id = message.content.split(',')[1].strip()
        add_channel('write_channels', int(channel_id))
        await message.channel.send(channel_id + " added to alert creating channels")
      else:
        add_channel('write_channels', message.channel.id)
        await message.channel.send("This channel added to alert creating channels")

  elif message.content.lower().startswith('$rw'):
    if message.author.id in admins:
      if ',' in message.content:
        channel_id = message.content.split(',')[1].strip()
        remove_channel('write_channels', int(channel_id))
        await message.channel.send(channel_id + " removed from alert creating channels")
      else:
        remove_channel('write_channels', message.channel.id)
        await message.channel.send("This channel removed from alert creating channels")

async def broadcast(embed):
  for server in client.guilds:
    for channel in server.text_channels:
      if channel.id in db['read_channels']:
        await channel.send(embed=embed)

async def broadcastWithFile(embed, file_path):
  for server in client.guilds:
    for channel in server.text_channels:
      if channel.id in db['read_channels']:
        await channel.send(file=discord.File(file_path), embed=embed)

keep_alive()
client.run(os.environ['TOKEN'])