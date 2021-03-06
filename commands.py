import discord
import redis
import numpy as np
from datetime import date
from datetime import datetime
import pytz
import re

def get_today():
	tz_NY = pytz.timezone('America/New_York') 
	datetime_NY = datetime.now(tz_NY)
	today = datetime_NY.strftime("%m/%d/%Y")
	return today

async def bto(message, redis_db):
	full_message = message.content
	full_message_split = full_message.split()

	if len(full_message_split) != 6:
		await message.channel.send('ERROR! Please use format: <:MomentumTrading:777540428010225674> <bto> <ticker> <strike> <expiration> <price>')
	else:
		ticker = full_message_split[2].upper()
		strike = full_message_split[3]
		expiration = full_message_split[4]
		price = full_message_split[5]
		pfp = message.author.avatar_url

		my_embed = discord.Embed(title="BTO", description="Ticker: {0}\nStrike: {1}\nExpiration: {2}\nPrice: {3}".format(ticker, strike, expiration, price), color=0x00ff00)
		my_embed.set_footer(text="Momentum Trading LLC")
		my_embed.set_author(name=message.author.name)
		my_embed.set_thumbnail(url=pfp)

		built_string = '{0}, {1}, {2}, {3}, {4}'.format(ticker, strike, expiration, get_today(), price)
		redis_db.sadd(str(message.author), built_string)

		await message.channel.send(embed=my_embed)
		await message.delete()


async def stc(message, redis_db, bot_test_playground):
	full_message = message.content
	full_message_split = full_message.split()

	if len(full_message_split) != 6:
		await message.channel.send('ERROR! Please use format: <:MomentumTrading:777540428010225674> <stc> <ticker> <strike> <expiration> <price>')
	else:
		ticker = full_message_split[2].upper()
		strike = full_message_split[3]
		expiration = full_message_split[4]
		price = full_message_split[5]
		pfp = message.author.avatar_url

		my_embed = discord.Embed(title="STC", color=0xFF0000)
		my_embed = discord.Embed(title="STC", description="Ticker: {0}\nStrike: {1}\nExpiration: {2}\nPrice: {3}".format(ticker, strike, expiration, price), color=0xFF0000)
		my_embed.set_footer(text="Momentum Trading LLC")
		my_embed.set_author(name=message.author.name)
		my_embed.set_thumbnail(url=pfp)

		built_string = '{0}, {1}, {2}'.format(ticker, strike, expiration)

		if not redis_db.exists(str(message.author)):
			await message.channel.send("You have no open positions right now!")

		my_positions = redis_db.smembers(str(message.author))

		for open_position in my_positions:
			if built_string in open_position:
				redis_db.srem(str(message.author), open_position)
				await message.channel.send(embed=my_embed)

				closed_positions_key = '{0}_closed_positions'.format(str(message.author))
				closed_positions_date_key = '{0}_closed_positions_{1}'.format(str(message.author), get_today())
				closed_positions_value = '{0} --> {1}'.format(open_position, price)

				redis_db.sadd(closed_positions_key, closed_positions_value)
				redis_db.sadd(closed_positions_date_key, closed_positions_value)
				await message.delete()
				return

		await message.channel.send("You do not have an open position matching this stc!")


async def open_positions(message, redis_db):
	if redis_db.exists(str(message.author)):
		my_positions = redis_db.smembers(str(message.author))

		for position in my_positions:
			split_pos = position.split(',')
			ticker = split_pos[0]
			strike = split_pos[1]
			exp = split_pos[2]

			entry = split_pos[4]
			await message.channel.send('Ticker: {0}, Strike: {1}, Exp: {2}, Entry: {3}'.format(ticker, strike, exp, entry))
	else:
		await message.channel.send("You have no open positions right now!")


async def closed_positions(message, redis_db):
	closed_positions_key = '{0}_closed_positions'.format(str(message.author))
	closed_positions = redis_db.smembers(closed_positions_key)

	for position in closed_positions:
		split_pos = position.split(',')
		ticker = split_pos[0]
		strike = split_pos[1]
		exp = split_pos[2]

		entry_exit = split_pos[4]
		entry_exit_split = entry_exit.split('-->')

		entry = entry_exit_split[0]
		exit = entry_exit_split[1]

		percent_gain = int(((float(exit)/float(entry)) * 100) - 100)

		await message.channel.send('Ticker: {0}, Strike: {1}, Exp: {2}, Entry: {3}, Exit: {4}, {5}%'.format(ticker, strike, exp, entry, exit, percent_gain))

async def closed_today(message, redis_db):
	closed_positions_today_key = '{0}_closed_positions_{1}'.format(str(message.author), get_today())
	closed_positions_today = redis_db.smembers(closed_positions_today_key)

	print(closed_positions_today_key)

	for position in closed_positions_today:
		split_pos = position.split(',')
		ticker = split_pos[0]
		strike = split_pos[1]
		exp = split_pos[2]

		entry_exit = split_pos[4]
		entry_exit_split = entry_exit.split('-->')

		entry = entry_exit_split[0]
		exit = entry_exit_split[1]

		percent_gain = int(((float(exit)/float(entry)) * 100) - 100)

		await message.channel.send('Ticker: {0}, Strike: {1}, Exp: {2}, Entry: {3}, Exit: {4}, {5}%'.format(ticker, strike, exp, entry, exit, percent_gain))


async def clear_author(message, redis_db):
	full_message = message.content
	full_message_split = full_message.split()

	author = full_message_split[2]

	redis_db.delete(str(author))
	redis_db.delete('{0}_closed_positions'.format(str(author)))
	redis_db.delete('{0}_closed_positions_{1}'.format(str(message.author), get_today()))

	await message.channel.send('Author cleared')

async def all_closed_today(message, redis_db):
	search_string = '*{0}'.format(get_today())
	print(search_string)
	for key in redis_db.scan_iter(search_string):
		member_name = key.split('_')[0]
		closed_positions = redis_db.smembers(key)
		
		for position in closed_positions:
			split_pos = position.split(',')
			ticker = split_pos[0]
			strike = split_pos[1]
			exp = split_pos[2]

			entry_exit = split_pos[4]
			entry_exit_split = entry_exit.split('-->')

			entry = entry_exit_split[0]
			exit = entry_exit_split[1]

			percent_gain = int(((float(exit)/float(entry)) * 100) - 100)

			await message.channel.send('Member Name: {6}, Ticker: {0}, Strike: {1}, Exp: {2}, Entry: {3}, Exit: {4}, {5}%'.format(ticker, strike, exp, entry, exit, percent_gain, member_name))

async def show_stats(message, redis_db):
	closed_positions_key = '{0}_closed_positions'.format(str(message.author))
	closed_positions = redis_db.smembers(closed_positions_key)

	number_of_trades = len(closed_positions)
	percent_gained_array = []
	trades_won = 0

	print(closed_positions_key)
	print(closed_positions)
	print(number_of_trades)

	if number_of_trades == 0:
		await message.channel.send('You have not taken any trades')
		return

	for position in closed_positions:
		split_pos = position.split(',')

		entry_exit = split_pos[4]
		entry_exit_split = entry_exit.split('-->')

		entry = entry_exit_split[0]
		exit = entry_exit_split[1]

		percent_gain = int(((float(exit)/float(entry)) * 100) - 100)

		if float(exit) > float(entry):
			trades_won += 1

		percent_gained_array.append(percent_gain)

	win_percentage = (float(trades_won) / float(number_of_trades)) * 100 
	win_pct_string = ("%.2f" % win_percentage)
	await message.channel.send('Number of Trades: {0}, Average: {1}%, {2}% Win Rate'.format(number_of_trades, int(np.mean(percent_gained_array)), win_pct_string))

async def show_stats_author(message, redis_db):
	full_message = message.content
	full_message_split = full_message.split()

	author = full_message_split[2]

	closed_positions_key = '{0}_closed_positions'.format(str(author))
	closed_positions = redis_db.smembers(closed_positions_key)

	number_of_trades = len(closed_positions)
	percent_gained_array = []
	trades_won = 0

	print(closed_positions_key)
	print(closed_positions)
	print(number_of_trades)

	if number_of_trades == 0:
		await message.channel.send('You have not taken any trades')
		return

	for position in closed_positions:
		split_pos = position.split(',')

		entry_exit = split_pos[4]
		entry_exit_split = entry_exit.split('-->')

		entry = entry_exit_split[0]
		exit = entry_exit_split[1]

		if float(exit) > float(entry):
			trades_won += 1

		percent_gain = int(((float(exit)/float(entry)) * 100) - 100)

		percent_gained_array.append(percent_gain)

	win_percentage = (float(trades_won) / float(number_of_trades)) * 100 
	win_pct_string = ("%.2f" % win_percentage)
	await message.channel.send('Number of Trades: {0}, Average: {1}%, {2}% Win Rate'.format(number_of_trades, int(np.mean(percent_gained_array)), win_pct_string))
