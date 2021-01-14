import discord
import csv
import random
from discord.ext import commands
from discord.utils import get as discordget
from datetime import date


def read_data():
    with open("data.txt", "r") as f:
        lines = f.readlines()
        return lines[0].strip(), [int(ID) for ID in lines[1].strip().split(',')]


# Defines Bot, Bot prefix, bot description, and the server
Bot_prefix = '?'
Bot = commands.Bot(command_prefix=Bot_prefix, description='Serving the needs of the guild!',
                   intents=discord.Intents.all())
token, adminIDs = read_data()


async def make_ticket(bot, payload):
    with open('data.txt', 'r') as f:
        lines = f.readlines()
        ticket_num = int(lines[2].strip())

    support_category_names = ["Ideas and Concerns", "Guild Bank Requests", "DKP Questions", "Frost Resistance", "Frost Resistance 2"]
    officer_names = "Galaxy Council"
    unique_role_names = {"Ideas and Concerns": None, "Guild Bank Requests": "Guild Bank", "DKP Questions": None, "Frost Resistance": None, "Frost Resistance 2": None}

    guild = bot.get_guild(payload.guild_id)
    moderator = discordget(guild.roles, name=officer_names)
    support_categories = [discordget(guild.categories, name=support_category_names[n])
                          for n in range(len(support_category_names))]
    support_channel = bot.get_channel(payload.channel_id)
    msg = await support_channel.fetch_message(payload.message_id)

    emojis = [str(reaction.emoji) for reaction in msg.reactions]
    for index, item in enumerate(emojis):
        if item == str(payload.emoji):
            overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False),
                          moderator: discord.PermissionOverwrite(read_messages=True),
                          bot.get_user(payload.user_id): discord.PermissionOverwrite(read_messages=True)}
            if unique_role_names[support_category_names[index]] is not None:
                unique_role = discordget(guild.roles, name=unique_role_names[support_category_names[index]])
                overwrites[unique_role] = discord.PermissionOverwrite(read_messages=True)
            ticket_num += 1
            try:
                ticket_channel = await guild.create_text_channel(f'ticket-#{ticket_num}',
                                                                 category=support_categories[index], overwrites=overwrites)
            except discord.errors.HTTPException:
                ticket_channel = await guild.create_text_channel(f'ticket-#{ticket_num}',
                                                                 category=support_categories[index+1], overwrites=overwrites)
            break

    for react in msg.reactions:
        if str(react.emoji) not in emojis[0:len(support_category_names)] or react.count > 1:
            await react.remove(bot.get_user(payload.user_id))

    with open('data.txt', 'w') as f:
        lines[2] = str(ticket_num)
        f.writelines(lines)

    ticketer = bot.get_user(payload.user_id)
    #pm_message = discord.Embed(description=f"{ticketer.mention} has opened a new ticket! "
    #                                       f"{ticket_channel.mention}", color=discord.Color.blue())
    seed_message = discord.Embed(description=f"Hello {ticketer.mention}, our staff will be with you shortly!",
                                 color=discord.Color.blue())
    #await ticketer.send(embed=pm_message)
    await ticket_channel.send(embed=seed_message)


async def assign_role(bot, payload, action):
    guild = bot.get_guild(payload.guild_id)
    requester = guild.get_member(payload.user_id)
    request_channel = guild.get_channel(payload.channel_id)
    role_assign_msg = await request_channel.fetch_message(payload.message_id)
    removed_intro = role_assign_msg.content.split('React to give yourself a role.\n')[1][1:]
    requested_role = None
    for sub_message in removed_intro.split('\n'):
        temp_message = sub_message.split(' : ')
        if len(temp_message) == 2:
            if ':' in temp_message[0]:
                if int(temp_message[0].split(':')[2].replace('>', '')) == payload.emoji.id:
                    requested_role = discordget(guild.roles, name=temp_message[1].replace('`', ''))
            elif temp_message[0] == str(payload.emoji):
                requested_role = discordget(guild.roles, name=temp_message[1].replace('`', ''))
    if action == 'add' and requested_role not in requester.roles and requested_role is not None:
        await requester.add_roles(requested_role, reason="User requested")
        await requester.send(f"**{guild.name}**: {requested_role.name}: Gave you the role!")
    elif action == 'remove' and requested_role in requester.roles:
        await requester.remove_roles(requested_role, reason="User requested")
        await requester.send(f"**{guild.name}**: {requested_role.name}: Took away the role!")


async def dkptable(bot, message):
    await message.attachments[0].save('new_table.csv')
    team = message.content
    dkp_file = open(f'{team}_dkp.csv', 'w')
    new_table_file = open('new_table.csv', 'r')
    new_dkp_reader = csv.reader(new_table_file, delimiter=',')
    dkp_file.write(f'Current as of,{date.today()}\n')
    dkp_file.writelines([f'{line[0]},{line[2]}\n' for line in new_dkp_reader][1:])
    new_table_file.close()
    dkp_file.close()

    team_channel = discordget(message.guild.text_channels, name=f"{team}-raid-discussion")
    text_table = '**DKP Table** ```'
    dkp_file = open(f'{team}_dkp.csv', 'r')
    for index, line in enumerate(dkp_file.readlines()):
        name, points = line.split(',')
        text_table += f'{name}, {points}'
    text_table += '```'

    pins = await team_channel.pins()
    if pins is not None:
        for pin in pins:
            if 'DKP Table' in pin.content:
                await pin.edit(content=text_table)
                return
    msg = await team_channel.send(content=text_table)
    await msg.pin()


async def votersuppression(bot, payload):
    allowed_role_names = ["Galaxy Council"]
    voting_channel = bot.get_channel(payload.channel_id)
    guild = bot.get_guild(payload.guild_id)
    allowed_roles = [discordget(guild.roles, name=allowed_role_name) for allowed_role_name in allowed_role_names]
    for index, item in enumerate(allowed_role_names):
        if index == 0:
            pm_message = f"Sorry, {voting_channel.mention} is for votes from {item}"
        elif index == len(allowed_role_names)-1:
            pm_message += f", and {item}"
        else:
            pm_message += f", {item}"
    pm_message += ' only.'
    if any(role in allowed_roles for role in payload.member.roles):
        return
    else:
        msg = await voting_channel.fetch_message(payload.message_id)
        for react in msg.reactions:
            if str(react.emoji) == str(payload.emoji):
                await react.remove(bot.get_user(payload.user_id))
        await payload.member.send(content=pm_message)


@Bot.event
async def on_member_join(member):
    contact = member.guild.get_member(adminIDs[0])
    greeting_channel_name = "general"
    welcome_info_page_name = "table-of-contents"
    greeting_channel = discordget(member.guild.text_channels, name=greeting_channel_name)
    welcome_info_page = discordget(member.guild.text_channels, name=welcome_info_page_name)
    intro_message = f"Welcome {member.mention}! Please change your discord name to match your main's name in game. " \
                    f"If you are a guildee, PM {contact.mention} on discord for guild permissions. " \
                    f"Have a look at the {welcome_info_page.mention} for help with navigating the server!"
    await greeting_channel.send(content=intro_message)


@Bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id != Bot.user.id:
        support_channel_name = "support"
        role_assign_channel_name = "role-assignment"
        voting_channel_name = "council-votes"
        if Bot.get_channel(payload.channel_id).name == support_channel_name:
            await make_ticket(Bot, payload)
        elif Bot.get_channel(payload.channel_id).name == role_assign_channel_name:
            await assign_role(Bot, payload, 'add')
        elif Bot.get_channel(payload.channel_id).name == voting_channel_name:
            await votersuppression(Bot, payload)


@Bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id != Bot.user.id:
        role_assign_channel_name = "role-assignment"
        if Bot.get_channel(payload.channel_id).name == role_assign_channel_name:
            await assign_role(Bot, payload, 'remove')


@Bot.event
async def on_message(message):
    if message.author == Bot.user:
        return
    if message.guild:
        dkp_archive_channel_name = "dkp-archive"
        dkp_archive_channel = discordget(message.guild.text_channels, name=dkp_archive_channel_name)
        if message.channel == dkp_archive_channel:
            await dkptable(Bot, message)
        await Bot.process_commands(message)
    else:
        admin_user = Bot.get_user(adminIDs[0])
        msg = f"from {message.author.mention}: {message.content}"
        await admin_user.send(content=msg)


@Bot.command()
async def close(ctx):
    """Closes a ticket and PMs the opener with the reason"""
    officer_names = "Galaxy Council"
    unique_role_names = {"Ideas and Concerns": None, "Guild Bank Requests": "Guild Bank", "DKP Questions": None, "Frost Resistance": None}
    support_category_names = ["Ideas and Concerns", "Guild Bank Requests", "DKP Questions", "Frost Resistance"]
    support_categories = [discordget(ctx.guild.categories, name=support_category_names[n])
                          for n in range(len(support_category_names))]
    ctx_category = discordget(ctx.guild.categories, id=ctx.channel.category_id)
    if ctx_category in support_categories:
        async for message in ctx.channel.history(oldest_first=True):
            embed = message.embeds[0]
            description = embed.description
            ticketer_id = int(description.split('@')[1].split('>')[0])
            break
        moderator = discordget(ctx.guild.roles, name=officer_names)
        unique_role = discordget(ctx.guild.roles, name=unique_role_names[ctx_category.name])
        if moderator in ctx.author.roles or unique_role in ctx.author.roles:
            if ctx.message.content != '?close':
                reason = ctx.message.content[7:]
            else:
                reason = 'No reason given'
            text = f"Ticket: {ctx.channel.name}\n" \
                   f"Closer: {ctx.author.mention}\n" \
                   f"Reason: {reason}"
            ticketer = Bot.get_user(ticketer_id)
            await ticketer.send(embed=discord.Embed(description=text, color=discord.Color.red()))
            await ctx.channel.delete()
        else:
            await ctx.channel.send("Incorrect Permissions.")


@Bot.command()
async def createticketmessage(ctx):
    """Creates the support message on which users react to open tickets"""
    emojis = ['🆘', '🏦', '💰', '❄']
    support_channel_name = "support"
    ticket_message = f"This channel will be for support ticket creation, " \
                     f"react to the bot's message with a {emojis[1]} icon for guild bank requests, " \
                     f"{emojis[0]} to open a ticket with the council to discuss ideas/concerns, " \
                     f"{emojis[2]} for questions regarding DKP, " \
                     f"and {emojis[3]} for a Frost Resistance request.\n\n" \
                     f"When creating a ticket, this opens a temporary channel " \
                     f"for which to submit your ideas/concerns/requests. " \
                     f"Once the need has been fulfilled, the channel will be removed."
    ticket_channel = discordget(ctx.guild.text_channels, name=support_channel_name)
    if ctx.author.id in adminIDs:
        ticket_message = await ticket_channel.send(content=ticket_message)
        for emoji in emojis:
            await ticket_message.add_reaction(emoji)
    await ctx.message.delete()


@Bot.command()
async def roll(ctx, arg=100):
    """Generates a random integer in the interval [1,N] where N (integer) is an optional input, default of 100."""
    await ctx.channel.send(f"{ctx.author.mention} has rolled a {random.randint(1, arg)} (1 - {arg})")
    await ctx.message.delete()


#@Bot.command()
#async def dkp(ctx, arg='your character name'):
#    with open('dkp.csv', 'r') as csvfile:
#        dkp_reader = csv.reader(csvfile, delimiter=',')
#        dkp_dict = {}
#        for line in dkp_reader:
#            if line[0] == 'the date':
#                last_updated_date = line[1]
#            dkp_dict[line[0]] = line[2]
#        if arg in dkp_dict.keys():
#            await ctx.author.send(content=f"As of {last_updated_date}, {arg} has {dkp_dict[arg]} DKP.")
#        elif str(ctx.author) in dkp_dict.keys():
#            await ctx.author.send(content=f"As of {last_updated_date}, {str(ctx.author)} "
#                                          f"has {dkp_dict[str(ctx.author)]} DKP.")
#        else:
#            await ctx.author.send(content=f"Sorry, I couldn't find {arg}.")
#        await ctx.message.delete()


Bot.run(token)
