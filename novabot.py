import discord
import random
from discord.ext import commands


def read_data():
    with open("data.txt", "r") as f:
        lines = f.readlines()
        return lines[0].strip(), [int(ID) for ID in lines[1].strip().split(',')]


# Defines Bot, Bot prefix, bot description, and the server
bot = commands.Bot(command_prefix='?', description='Serving the needs of the guild!', intents=discord.Intents.all())
token, adminIDs = read_data()


@bot.event
async def on_member_join(member):
    contact = member.guild.get_member(adminIDs[0])
    greeting_channel_name = "general"
    welcome_info_page_name = "table-of-contents"
    for index, item in enumerate(member.guild.text_channels):
        if item.name == welcome_info_page_name:
            welcome_info_page = member.guild.text_channels[index]
        elif item.name == greeting_channel_name:
            greeting_channel = member.guild.text_channels[index]
    intro_message = f"Welcome {member.mention}! Please change your discord name to match your main's name in game. " \
                    f"If you are a guildee, PM your name to {contact.mention} on discord for guild permissions. " \
                    f"Have a look at the {welcome_info_page.mention} for help with navigating the server!"
    print(welcome_info_page)
    await greeting_channel.send(content=intro_message)


@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id != bot.user.id:
        if bot.get_channel(payload.channel_id).name == 'support':
            with open('data.txt', 'r') as f:
                lines = f.readlines()
                ticket_num = int(lines[2].strip())

            guild = bot.get_guild(payload.guild_id)
            for role in guild.roles:
                if role.name == 'Galaxy Council':
                    council = guild.get_role(role.id)
                elif role.name == 'Guild Bank':
                    gbank = guild.get_role(role.id)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                council: discord.PermissionOverwrite(read_messages=True),
                bot.get_user(payload.user_id): discord.PermissionOverwrite(read_messages=True)
            }

            for category in guild.categories:
                if category.name == 'Ideas and Concerns':
                    sos_cat = category
                elif category.name == 'Guild Bank Requests':
                    bank_cat = category
                elif category.name == 'DKP Questions':
                    dkp_cat = category

            support_channel = bot.get_channel(payload.channel_id)
            msg = await support_channel.fetch_message(payload.message_id)

            emojis = [str(reaction.emoji) for reaction in msg.reactions]
            if str(payload.emoji) == emojis[0]:
                ticket_num += 1
                ticket_channel = await guild.create_text_channel(f'ticket-#{ticket_num}', category=sos_cat, overwrites=overwrites)
            elif str(payload.emoji) == emojis[1]:
                ticket_num += 1
                overwrites[gbank] = discord.PermissionOverwrite(read_messages=True)
                ticket_channel = await guild.create_text_channel(f'ticket-#{ticket_num}', category=bank_cat, overwrites=overwrites)
            elif str(payload.emoji) == emojis[2]:
                ticket_num += 1
                ticket_channel = await guild.create_text_channel(f'ticket-#{ticket_num}', category=dkp_cat, overwrites=overwrites)
            for react in msg.reactions:
                if str(react.emoji) not in emojis[0:3] or react.count > 1:
                    await react.remove(bot.get_user(payload.user_id))

            with open('data.txt', 'w') as f:
                lines[2] = str(ticket_num)
                f.writelines(lines)

            ticketer = bot.get_user(payload.user_id)
            pm_message = discord.Embed(description=f"{ticketer.mention} has opened a new ticket! {ticket_channel.mention}", color=discord.Color.blue())
            seed_message = discord.Embed(description=f"Hello {ticketer.mention}, our staff will be with you shortly!", color=discord.Color.blue())
            await ticketer.send(embed=pm_message)
            await ticket_channel.send(embed=seed_message)


@bot.command()
async def close(ctx, arg):
    """Closes a ticket and PMs the opener with the reason"""
    for category in ctx.guild.categories:
        if category.name == 'Ideas and Concerns':
            sos_cat = category
        elif category.name == 'Guild Bank Requests':
            bank_cat = category
        elif category.name == 'DKP Questions':
            dkp_cat = category
    if ctx.channel.category_id in [sos_cat.id, bank_cat.id, dkp_cat.id]:
        async for message in ctx.channel.history(oldest_first=True):
            embed = message.embeds[0]
            description = embed.description
            ticketer_id = int(description.split('@')[1].split('>')[0])
            break
        for role in ctx.guild.roles:
            if role.name == 'Galaxy Council':
                council = ctx.guild.get_role(role.id)
            elif role.name == 'Guild Bank':
                gbank = ctx.guild.get_role(role.id)
        if council in ctx.author.roles or (gbank in ctx.author.roles and ctx.channel.category_id == bank_cat.id):
            if arg is not None:
                reason = arg
            else:
                reason = 'No reason given'
            text = f"Ticket: {ctx.channel.name}\n" \
                   f"Closer: {ctx.author.mention}\n" \
                   f"Reason: {reason}"
            ticketer = bot.get_user(ticketer_id)
            await ticketer.send(embed=discord.Embed(description=text, color=discord.Color.red()))
            await ctx.channel.delete()


@bot.command()
async def createticketmessage(ctx):
    """Creates the support message on which users react to open tickets"""
    emojis = ['🆘', '🏦', '💰']
    support_channel_name = 'support'
    for index, item in enumerate(ctx.guild.text_channels):
        if item.name == support_channel_name:
            ticket_channel = ctx.guild.text_channels[index]
            break
    ticket_message = f"This channel will be for support ticket creation, " \
                     f"react to the bot's message with a {emojis[1]} icon for guild bank requests, " \
                     f"{emojis[0]} to open a ticket with the council to discuss ideas/concerns, and {emojis[2]} for questions regarding DKP.\n\n" \
                     f"When creating a ticket, this opens a temporary channel for which to submit your ideas/concerns/requests.  " \
                     f"Once the need has been fulfilled, the channel will be removed."
    if ctx.author.id in adminIDs:
        ticket_message = await ticket_channel.send(content=ticket_message)
        await ticket_message.add_reaction(emojis[0])
        await ticket_message.add_reaction(emojis[1])
        await ticket_message.add_reaction(emojis[2])
    await ctx.message.delete()


@bot.command()
async def roll(ctx, arg=100):
    """Generates a random integer in the interval [1-N] where N (integer) is an optional input, default of 100."""
    try:
        await ctx.channel.send(f"{ctx.author.mention} has rolled a {random.randint(1, int(arg))} (1 - {arg})")
    except ValueError:
        await ctx.channel.send(f"{ctx.author.mention} has rolled a {random.randint(1, 100)} (1 - 100)")
    except:
        await ctx.channel.send("Sorry, I couldn't understand that, please try again.")
        return
    await ctx.message.delete()


bot.run(token)
