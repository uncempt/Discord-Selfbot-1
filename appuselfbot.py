import collections
import datetime
import math
import subprocess
import asyncio
import random
import glob
import gc
from datetime import timezone
from cogs.utils.allmsgs import *
from discord_webhooks import *
from cogs.utils.checks import *
from discord.ext import commands



config = load_config()

bot_prefix = config['bot_identifier']
if bot_prefix != '':
    bot_prefix += ' '

bot = commands.Bot(command_prefix=config['cmd_prefix'][0], description='''Selfbot by appu1232''', self_bot=True)


# Startup
@bot.event
async def on_ready():
    print('Logged in as')
    try:
        print(bot.user.name)
    except:
        print(bot.user.name.encode("utf-8"))
    print('User id:' + str(bot.user.id))
    print('------')
    bot.uptime = datetime.datetime.now()
    bot.icount = 0
    bot.message_count = 0
    bot.mention_count = 0
    bot.self_log = {}
    bot.all_log = {}
    bot.keyword_log = 0
    bot.refresh_time = time.time()
    bot.gc_time = time.time()
    bot.game = None
    bot.game_interval = None
    bot.avatar = None
    bot.avatar_interval = None
    bot.game_time = time.time()
    bot.avatar_time = time.time()
    bot.subpro = None
    bot.keyword_found = None

    if os.path.isfile('restart.txt'):
        with open('restart.txt', 'r') as re:
            channel = bot.get_channel(re.readline())
            print('Bot has restarted.')
            await bot.send_message(channel, bot_prefix + 'Bot has restarted.')
        os.remove('restart.txt')
    with open('settings/log.json', 'r+') as log:
        loginfo = json.load(log)
        try:
            if 'blacklisted_words' not in loginfo:
                loginfo['blacklisted_words'] = []
            if 'blacklisted_servers' not in loginfo:
                loginfo['blacklisted_servers'] = []
            if 'keyword_logging' not in loginfo:
                loginfo['keyword_logging'] = 'on'
            if 'webhook_url' not in loginfo:
                loginfo['webhook_url'] = ''
            if int(loginfo['log_size']) > 25:
                loginfo['log_size'] = "25"
        except:
            pass
        log.seek(0)
        log.truncate()
        json.dump(loginfo, log, indent=4)
    with open('settings/log.json', 'r') as log:
        bot.log_conf = json.load(log)
    if os.path.isfile('settings/games.json'):
        with open('settings/games.json', 'r') as g:
            games = json.load(g)
        if type(games['games']) is list:
            bot.game = games['games'][0]
            bot.game_interval = games['interval']
        else:
            bot.game = games['games']
    if not os.path.exists('settings/avatars'):
        os.makedirs('settings/avatars')
    if not os.path.isfile('settings/avatars.json'):
        with open('settings/avatars.json', 'w') as avis:
            json.dump({'password': '', 'interval': '0', 'type': 'random'}, avis, indent=4)
    with open('settings/avatars.json', 'r') as g:
        avatars = json.load(g)
    bot.avatar_interval = avatars['interval']
    if os.listdir('settings/avatars') and avatars['interval'] != '0':
        all_avis = os.listdir('settings/avatars')
        all_avis.sort()
        avi = random.choice(all_avis)
        bot.avatar = avi
    if not os.path.isfile('settings/optional_config.json'):
        conf = load_config()
        o_conf = {'google_api_key': conf['google_api_key'], 'custom_search_engine': conf['custom_search_engine'], 'mal_username': conf['mal_username'], 'mal_password': conf['mal_password']}
        with open('settings/optional_config.json', 'w') as oc:
            json.dump(o_conf, oc, indent=4)
    with open('settings/notify.json', 'r') as n:
        notif = json.load(n)
    if notif['type'] == 'dm':
        try:
            bot.subpro = subprocess.Popen(['python3', 'cogs/utils/notify.py'])
        except (SyntaxError, FileNotFoundError):
            bot.subpro = subprocess.Popen(['python', 'cogs/utils/notify.py'])
        except:
            pass


@bot.command(pass_context=True, aliases=['reboot'])
async def restart(ctx):
    """Restarts the bot."""
    def check(msg):
        if msg:
            return msg.content.lower().strip() == 'y' or msg.content.lower().strip() == 'n'
        else:
            return False

    latest = update_bot(True)
    if latest:
        await bot.send_message(ctx.message.channel, bot_prefix + 'There is an update available for the bot. Download and apply the update on restart? (y/n)')
        reply = await bot.wait_for_message(timeout=10, author=ctx.message.author, check=check)
        if not reply or reply.content.lower().strip() == 'n':
            with open('restart.txt', 'w') as re:
                print('Restarting...')
                re.write(str(ctx.message.channel.id))
            await bot.send_message(ctx.message.channel, bot_prefix + 'Restarting...')
        else:
            await bot.send_message(ctx.message.channel, content=None, embed=latest)
            with open('quit.txt', 'w') as q:
                q.write('update')
            print('Downloading update and restarting...')
            await bot.send_message(ctx.message.channel, bot_prefix + 'Downloading update and restarting (check your console to see the progress)...')

    else:
        print('Restarting...')
        with open('restart.txt', 'w') as re:
            re.write(str(ctx.message.channel.id))
        await bot.send_message(ctx.message.channel, bot_prefix + 'Restarting...')

    if bot.subpro:
        bot.subpro.kill()
    os._exit(0)


@bot.command(pass_context=True, aliases=['upgrade'])
async def update(ctx):
    """Update the bot if there is an update available."""
    if ctx.message.content:
        if ctx.message.content[7:].strip() == 'show':
            latest = update_bot(False)
        else:
            latest = update_bot(True)
    else:
        latest = update_bot(True)
    if latest:
        if not ctx.message.content[7:].strip() == 'show':
            if embed_perms(ctx.message):
                await bot.send_message(ctx.message.channel, content=None, embed=latest)
            await bot.send_message(ctx.message.channel, bot_prefix + 'There is an update available. Downloading update and restarting (check your console to see the progress)...')
        else:
            await bot.send_message(ctx.message.channel, content=None, embed=latest)
            return
        with open('quit.txt', 'w') as q:
            q.write('update')
        with open('restart.txt', 'w') as re:
            re.write(str(ctx.message.channel.id))
        if bot.subpro:
            bot.subpro.kill()
        os._exit(0)
    else:
        await bot.send_message(ctx.message.channel, bot_prefix + 'The bot is up to date.')


@bot.command(pass_context=True, aliases=['exit'])
async def quit(ctx):
    """Quits the bot."""
    print('Bot exiting...')
    if bot.subpro:
        bot.subpro.kill()
    with open('quit.txt', 'w') as q:
        q.write('.')
    await bot.send_message(ctx.message.channel, bot_prefix + 'Bot shut down.')
    os._exit(0)


@bot.command(pass_context=True)
async def reload(ctx):
    """Reloads all modules."""
    utils = []
    for i in bot.extensions:
        utils.append(i)
    fail = False
    for i in utils:
        bot.unload_extension(i)
        try:
            bot.load_extension(i)
        except:
            await bot.send_message(ctx.message.channel, bot_prefix + 'Failed to reload extension ``%s``' % i)
            fail = True
    if fail:
        await bot.send_message(ctx.message.channel, bot_prefix + 'Reloaded remaining extensions.')
    else:
        await bot.send_message(ctx.message.channel, bot_prefix + 'Reloaded all extensions.')


# On all messages sent (for quick commands, custom commands, and logging messages)
@bot.event
async def on_message(message):

    await bot.wait_until_ready()
    await bot.wait_until_login()
    if hasattr(bot, 'message_count'):
        bot.message_count += 1

    # If the message was sent by me
    if message.author.id == bot.user.id:
        if message.channel.id not in bot.self_log:
            bot.self_log[message.channel.id] = collections.deque(maxlen=100)
        bot.self_log[message.channel.id].append(message)
        bot.icount += 1
        if message.content.startswith(config['customcmd_prefix'][0]):
            response = custom(message.content.lower().strip())
            if response is None:
                pass
            else:
                if response[0] == 'embed' and embed_perms(message):
                    try:
                        await bot.send_message(message.channel, content=None, embed=discord.Embed(colour=0x27007A).set_image(url=response[1]))
                    except:
                        await bot.send_message(message.channel, response[1])
                else:
                    await bot.send_message(message.channel, response[1])
                await bot.delete_message(message)
        else:
            response = quickcmds(message.content.lower().strip())
            if response:
                await bot.delete_message(message)
                await bot.send_message(message.channel, response)

    notified = message.mentions
    if notified:
        for i in notified:
            if i.id == bot.user.id:
                bot.mention_count += 1

    if not hasattr(bot, 'log_conf'):
        with open('settings/log.json', 'r') as log:
            bot.log_conf = json.load(log)

    # Keyword logging.
    if bot.log_conf['keyword_logging'] == 'on':

        try:
            word_found = False
            if bot.log_conf['allservers'] == 'True' and message.server.id not in bot.log_conf['blacklisted_servers']:
                add_alllog(message.channel.id, message.server.id, message)
                for word in bot.log_conf['keywords']:
                    if word.lower() in message.content.lower() and message.author.id != bot.user.id:
                        word_found = True
                        if message.author.bot:
                            word_found = False
                        for x in bot.log_conf['blacklisted_users']:
                            if message.author.id == x:
                                word_found = False
                                break
                        for x in bot.log_conf['blacklisted_words']:
                            if '[server]' in x:
                                bword, id = x.split('[server]')
                                if bword.strip().lower() in message.content.lower() and message.server.id == id:
                                    word_found = False
                                    break
                            if x.lower() in message.content.lower():
                                word_found = False
                                break
                        break
            else:
                if str(message.server.id) in bot.log_conf['servers']:
                    add_alllog(message.channel.id, message.server.id, message)
                    for word in bot.log_conf['keywords']:
                        if word.lower() in message.content.lower() and message.author.id != bot.user.id:
                            word_found = True
                            if message.author.bot:
                                word_found = False
                            for x in bot.log_conf['blacklisted_users']:
                                if message.author.id == x:
                                    word_found = False
                                    break
                            for x in bot.log_conf['blacklisted_words']:
                                if '[server]' in x:
                                    bword, id = x.split('[server]')
                                    if bword.strip().lower() in message.content.lower() and message.server.id == id:
                                        word_found = False
                                        break
                                if x.lower() in message.content.lower():
                                    word_found = False
                                    break
                            break

            if word_found is True:
                location = bot.log_conf['log_location'].split()
                server = bot.get_server(location[1])
                if message.channel.id != location[0]:
                    msg = message.clean_content.replace('`', '')

                    context = []
                    try:
                        for i in range(0, int(bot.log_conf['context_len'])):
                            context.append(bot.all_log[message.channel.id + ' ' + message.server.id][len(bot.all_log[message.channel.id + ' ' + message.server.id])-i-2])
                        msg = ''
                        for i in range(0, int(bot.log_conf['context_len'])):
                            temp = context[len(context)-i-1][0]
                            if temp.clean_content:
                                msg += 'User: %s | %s\n' % (temp.author.name, temp.timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None).__format__('%x @ %X')) + temp.clean_content.replace('`', '') + '\n\n'
                        msg += 'User: %s | %s\n' % (message.author.name, message.timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None).__format__('%x @ %X')) + message.clean_content.replace('`', '')
                        success = True
                    except:
                        success = False
                        msg = 'User: %s | %s\n' % (message.author.name, message.timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None).__format__('%x @ %X')) + msg

                    part = int(math.ceil(len(msg) / 1950))
                    notify = load_notify_config()
                    if part == 1 and success is True:
                        em = discord.Embed(timestamp=message.timestamp, color=0xbc0b0b, title='%s mentioned: %s' % (message.author.name, word), description='Server: ``%s``\nChannel: ``%s``\n\n**Context:**' % (str(message.server), str(message.channel)))
                        for i in range(0, int(bot.log_conf['context_len'])):
                            temp = context.pop()
                            if temp[0].clean_content:
                                em.add_field(name='%s' % temp[0].author.name, value=temp[0].clean_content, inline=False)
                        em.add_field(name='%s' % message.author.name, value=message.clean_content, inline=False)
                        try:
                            em.set_thumbnail(url=message.author.avatar_url)
                        except:
                            pass
                        if notify['type'] == 'msg':
                            await webhook(em, 'embed')
                        elif notify['type'] == 'ping':
                            await webhook(em, 'embed ping')
                        else:
                            await bot.send_message(server.get_channel(location[0]), embed=em)
                    else:
                        split_list = [msg[i:i + 1950] for i in range(0, len(msg), 1950)]
                        all_words = []
                        split_msg = ''
                        for i, blocks in enumerate(split_list):
                            for b in blocks.split('\n'):
                                split_msg += b + '\n'
                            all_words.append(split_msg)
                            split_msg = ''
                        for b,i in enumerate(all_words):
                            if b == 0:
                                if notify['type'] == 'msg':
                                    await webhook(bot_prefix + 'Keyword ``%s`` mentioned in server: ``%s`` Context: ```Channel: %s\n\n%s```' % (word, str(message.server), str(message.channel), i), 'message')
                                elif notify['type'] == 'ping':
                                    await webhook(bot_prefix + 'Keyword ``%s`` mentioned in server: ``%s`` Context: ```Channel: %s\n\n%s```' % (word, str(message.server), str(message.channel), i), 'message ping')
                                else:
                                    await bot.send_message(server.get_channel(location[0]), bot_prefix + 'Keyword ``%s`` mentioned in server: ``%s`` Context: ```Channel: %s\n\n%s```' % (word, str(message.server), str(message.channel), i))
                            else:
                                if notify['type'] == 'msg':
                                    await webhook('```%s```' % i, 'message')
                                elif notify['type'] == 'ping':
                                    await webhook('```%s```' % i, 'message ping')
                                else:
                                    await bot.send_message(server.get_channel(location[0]), '```%s```' % i)
                    bot.keyword_log += 1

        except:
            pass

    await bot.process_commands(message)

def add_alllog(channel, server, message):
    if not hasattr(bot, 'all_log'):
        bot.all_log = {}
    if channel + ' ' + server in bot.all_log:
        bot.all_log[channel + ' ' + server].append((message, message.clean_content))
    else:
        with open('settings/log.json') as f:
            config = json.load(f)
            bot.all_log[channel + ' ' + server] = collections.deque(maxlen=int(config['log_size']))
            bot.all_log[channel + ' ' + server].append((message, message.clean_content))


def remove_alllog(channel, server):
    del bot.all_log[channel + ' ' + server]


# Webhook for keyword notifications
async def webhook(keyword_content, send_type):
    temp = bot.log_conf['webhook_url'].split('/')
    channel = temp[len(temp) - 2]
    token = temp[len(temp) - 1]
    webhook_class = Webhook(bot)
    request_webhook = webhook_class.request_webhook
    if send_type.startswith('embed'):
        if 'ping' in send_type:
            await request_webhook('/{}/{}'.format(channel, token), embeds=[keyword_content.to_dict()], content=bot.user.mention)
        else:
            await request_webhook('/{}/{}'.format(channel, token), embeds=[keyword_content.to_dict()], content=None)
    else:
        if 'ping' in send_type:
            await request_webhook('/{}/{}'.format(channel, token), content=keyword_content + '\n' + bot.user.mention, embeds=None)
        else:
            await request_webhook('/{}/{}'.format(channel, token), content=keyword_content, embeds=None)

# Set/cycle game
async def game(bot):
    await bot.wait_until_ready()
    current_game = 0
    next_game = 0
    while not bot.is_closed:
        if hasattr(bot, 'game_time') and hasattr(bot, 'game'):
            if bot.game:
                if bot.game_interval:
                    if game_time_check(bot, bot.game_time, bot.game_interval):
                        with open('settings/games.json') as g:
                            games = json.load(g)
                        if games['type'] == 'random':
                            while next_game == current_game:
                                next_game = random.randint(0, len(games['games']) - 1)
                            current_game = next_game
                            bot.game = games['games'][next_game]
                            await bot.change_presence(game=discord.Game(name=games['games'][next_game]))
                        else:
                            if next_game+1 == len(games['games']):
                                next_game = 0
                            else:
                                next_game += 1
                            bot.game = games['games'][next_game]
                            await bot.change_presence(game=discord.Game(name=games['games'][next_game]))


                else:
                    if game_time_check(bot, bot.game_time, 180):
                        with open('settings/games.json') as g:
                            games = json.load(g)

                        bot.game = games['games']
                        await bot.change_presence(game=discord.Game(name=games['games']))

        # Sets status to idle when I go offline (won't trigger while I'm online so this prevents me from appearing online all the time)
        if hasattr(bot, 'refresh_time'):
            if has_passed(bot, bot.refresh_time):
                if bot.game:
                    await bot.change_presence(game=discord.Game(name=bot.game), status='invisible', afk=True)
                else:
                    await bot.change_presence(status='invisible', afk=True)

        if hasattr(bot, 'gc_time'):
            if gc_clear(bot, bot.gc_time):
                gc.collect()

        await asyncio.sleep(5)

# Set/cycle avatar
async def avatar(bot):
    await bot.wait_until_ready()
    current_avatar = 0
    next_avatar = 0
    while not bot.is_closed:
        if hasattr(bot, 'avatar_time') and hasattr(bot, 'avatar'):
            if bot.avatar:
                if bot.avatar_interval:
                    if avatar_time_check(bot, bot.avatar_time, bot.avatar_interval):
                        with open('settings/avatars.json') as g:
                            avi_config = json.load(g)
                        all_avis = glob.glob('settings/avatars/*.jpg')
                        all_avis.extend(glob.glob('settings/avatars/*.jpeg'))
                        all_avis.extend(glob.glob('settings/avatars/*.png'))
                        all_avis = os.listdir('settings/avatars')
                        all_avis.sort()
                        if avi_config['type'] == 'random':
                            while next_avatar == current_avatar:
                                next_avatar = random.randint(0, len(all_avis) - 1)
                            current_avatar = next_avatar
                            bot.avatar = all_avis[next_avatar]
                            with open('settings/avatars/%s' % bot.avatar, 'rb') as fp:
                                await bot.edit_profile(password=avi_config['password'], avatar=fp.read())
                        else:
                            if next_avatar+1 == len(all_avis):
                                next_avatar = 0
                            else:
                                next_avatar += 1
                            bot.avatar = all_avis[next_avatar]
                            with open('settings/avatars/%s' % bot.avatar, 'rb') as fp:
                                await bot.edit_profile(password=avi_config['password'], avatar=fp.read())

        await asyncio.sleep(5)

if __name__ == '__main__':

    for extension in os.listdir("cogs"):
        if extension.endswith('.py'):
            try:
                bot.load_extension("cogs." + extension.rstrip(".py"))
            except Exception as e:
                print('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))

    bot.loop.create_task(game(bot))
    bot.loop.create_task(avatar(bot))
    bot.run(config['token'], bot=False)
