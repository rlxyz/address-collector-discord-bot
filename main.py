import os
import discord
import logging
import pandas as pd
from web3 import Web3
from replit import db

logging.basicConfig(level=logging.INFO)

discord_token = os.environ["DISCORD_TOKEN"]
discord_channel = os.environ["DISCORD_CHANNEL_ID"]

client = discord.Client()
guild = discord.Guild

success_color = 0x0027FF
error_color = 0xFF0000
valid_color = 0x00FF00


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=discord.Game('_scan help'))


@client.event
async def on_message(message):
    author_id = message.author.id

    if str(message.channel.id) != discord_channel:
        return

    if message.author == client.user:
        return

    elif message.content.startswith('!dreamlist'):
        try:
            if len(message.content.split()) > 1:
                address = message.content.split()[1:][0]
                invocation = 1
                if Web3.isAddress(address):
                    db[str(author_id)] = {
                        "address": address,
                        "invocation": invocation
                    }
                    await message.reply(embed=discord.Embed(
                        title="A dreamer has been born ~",
                        description=
                        """<@{username}> you are now added into the dreamlist\n\nDreamlist address: [{address}](https://etherscan.io/address/{address})\n\nAllocation: {invocation}"""
                        .format(username=author_id,
                                address=address,
                                invocation=invocation),
                        color=success_color))
                else:
                    await message.reply(embed=discord.Embed(
                        title="Opps, You're not a dreamer ~",
                        description=
                        """Invalid ETH address supplied. Try again.""",
                        color=error_color))
        except:
            # do_something
            print('add_rollbar_here')

    elif message.content.startswith('!dreamcheck'):
        try:
            value = db[str(author_id)]
            if value:
                await message.reply(embed=discord.Embed(
                    title="You are a dreamer ~",
                    description=
                    """<@{username}> you are on the dreamlist \n\nDreamlist address: [{address}](https://etherscan.io/address/{address})\n\nAllocation: {invocation}"""
                    .format(username=author_id,
                            address=value["address"],
                            invocation=value["invocation"]),
                    color=valid_color))
            else:
                await message.reply(
                    embed=discord.Embed(title="Opps, You're not a dreamer ~",
                                        description="""Try again.""",
                                        color=error_color))
        except:
            # do_something
            print('add_rollbar_here')

    elif message.content.startswith('!dreamadmin'):
        keys = db.keys()
        for key in keys:
            print(key)

    elif message.content.startswith('!'):
        cmd = message.content.split()[0].replace("!", "")
        if len(message.content.split()) > 1:
            parameters = message.content.split()[1:]

        # Bot Commands

        if cmd == 'save':

            data = pd.DataFrame(columns=['content', 'time', 'author'])

            # Acquiring the channel via the bot command
            if len(message.channel_mentions) > 0:
                channel = message.channel_mentions[0]
            else:
                channel = message.channel

            # Aquiring the number of messages to be scraped via the bot command
            if (len(message.content.split()) > 1
                    and len(message.channel_mentions)
                    == 0) or len(message.content.split()) > 2:
                for parameter in parameters:
                    if parameter == "help":
                        answer = discord.Embed(
                            title="Command Format",
                            description=
                            """`_scan <channel> <number_of_messages>`\n\n`<channel>` : **the channel you wish to scan**\n`<number_of_messages>` : **the number of messages you wish to scan**\n\n*The order of the parameters does not matter.*""",
                            colour=0x1a7794)
                        await message.channel.send(embed=answer)
                        return
                    elif parameter[
                            0] != "<":  # Channels are enveloped by "<>" as strings
                        limit = int(parameter)
            else:
                limit = 100

            answer = discord.Embed(
                title="Creating your Message History Dataframe",
                description=
                "Please Wait. The data will be sent to you privately once it's finished.",
                colour=0x1a7794)

            await message.channel.send(embed=answer)

            def is_command(message):
                if len(msg.content) == 0:
                    return False
                elif msg.content.split()[0] == '_scan':
                    return True
                else:
                    return False

            async for msg in channel.history(
                    limit=limit + 1000
            ):  # The added 1000 is so in case it skips messages for being
                if msg.author != client.user:  # a command or a message it sent, it will still read the
                    if not is_command(
                            msg
                    ):  # the total amount originally specified by the user.
                        data = data.append(
                            {
                                'content': msg.content,
                                'time': msg.created_at,
                                'author': msg.author.name
                            },
                            ignore_index=True)
                    if len(data) == limit:
                        break

            # Turning the pandas dataframe into a .csv file and sending it to the user

            file_location = f"{str(channel.guild.id) + '_' + str(channel.id)}.csv"  # Determining file name and location
            data.to_csv(file_location)  # Saving the file as a .csv via pandas

            answer = discord.Embed(
                title="Here is your .CSV File",
                description=
                f"""It might have taken a while, but here is what you asked for.\n\n`Server` : **{message.guild.name}**\n`Channel` : **{channel.name}**\n`Messages Read` : **{limit}**""",
                colour=0x1a7794)

            await message.author.send(embed=answer)
            await message.author.send(file=discord.File(file_location,
                                                        filename='data.csv')
                                      )  # Sending the file
            os.remove(file_location)  # Deleting the file


client.run(discord_token)
