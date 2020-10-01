import discord
from discord.ext import commands


def read_data():
    with open("data.txt", "r") as f:
        lines = f.readlines()
        return lines[0].strip(), int(lines[1].strip())


# Defines Bot, Bot prefix, bot description, and the server
bot = commands.Bot(command_prefix='?', description='Serving the needs of the guild!')
token, adminID, = read_data()


@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id == 703374418407325787:
        with open('data.txt', 'r') as f:
            lines = f.readlines()
            ticket_num = int(lines[2].strip())

        guild = bot.get_guild(640784232276557873)
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
async def close(ctx):
    """Closes a ticket and PMs the opener with the reason"""
    guild = bot.get_guild(640784232276557873)
    for category in guild.categories:
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
        for role in guild.roles:
            if role.name == 'Galaxy Council':
                council = guild.get_role(role.id)
            elif role.name == 'Guild Bank':
                gbank = guild.get_role(role.id)
        if council in ctx.author.roles or (gbank in ctx.author.roles and ctx.channel.category_id == bank_id):
            if ctx.message.content.split('?close')[1]:
                reason = ctx.message.content.split('?close')[1]
            else:
                reason = 'No reason given'
            text = f"Ticket: {ctx.channel.name}\n" \
                   f"Closer: {ctx.author.mention}\n" \
                   f"Reason: {reason}"
            embed = discord.Embed(description=text, color=discord.Color.red())
            ticketer = bot.get_user(ticketer_id)
            await ticketer.send(embed=embed)
            await ctx.channel.delete()


@bot.command()
async def create(ctx):
    """Creates the support message on which users react to open tickets"""
    emojis = ['🆘', '🏦', '💰']
    ticket_channel_id = 703374418407325787
    ticket_channel = bot.get_channel(ticket_channel_id)
    ticket_message = f"This channel will be for support ticket creation, " \
                     f"react to the bot's message with a {emojis[1]} icon for guild bank requests, " \
                     f"{emojis[0]} to open a ticket with the council to discuss ideas/concerns, and {emojis[2]} for questions regarding DKP.\n\n" \
                     f"When creating a ticket, this opens a temporary channel for which to submit your ideas/concerns/requests.  " \
                     f"Once the need has been fulfilled, the channel will be removed."
    if ctx.author.id == adminID:
        ticket_message = await ticket_channel.send(content=ticket_message)
        await ticket_message.add_reaction(emojis[0])
        await ticket_message.add_reaction(emojis[1])
        await ticket_message.add_reaction(emojis[2])


bot.run(token)
