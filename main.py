import os
import discord
import logging
import pandas as pd
from web3 import Web3
from replit import db
import rollbar

logging.basicConfig(level=logging.INFO)

discord_token = os.environ["DISCORD_TOKEN"]
discord_channel = os.environ["DISCORD_CHANNEL_ID"]
discord_config_channel = os.environ["DISCORD_CONFIG_CHANNEL_ID"]
discord_admin = os.environ["DISCORD_ADMIN_LIST"]
rollbar_secret_key = os.environ["ROLLBAR_SECRET_KEY"]
rollbar_environment = os.environ["ROLLBAR_ENVIRONMENT"]
rollbar.init(rollbar_secret_key, rollbar_environment)

client = discord.Client()
guild = discord.Guild

success_color = 0x0027FF
error_color = 0xFF0000
valid_color = 0x00FF00

allowlist_command = "!dreamlist"
allowlist_check_command = "!dreamcheck"
allowlist_admin = "!dreamadmin"

discord_watching_text = "the Dreamers"


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name=discord_watching_text))


@client.event
async def on_message(message):
    author_id = message.author.id

    if message.author == client.user:
        return

    if str(message.channel.id) == discord_channel:
        if message.content.startswith(allowlist_command):
            try:
                if len(message.content.split()) > 1:
                    address = message.content.split()[1:][0]
                    invocation = 1
                    if Web3.isAddress(address):
                        db[str(author_id)] = {
                            "address": Web3.toChecksumAddress(address),
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
                        rollbar.report_message('Invalid Address',
                                               'warning',
                                               extra_data={
                                                   'user': {
                                                       "id": author_id,
                                                       "address": address,
                                                   }
                                               })
                        await message.reply(embed=discord.Embed(
                            title="Opps, You're not a dreamer ~",
                            description=
                            """Invalid address supplied. Try again.""",
                            color=error_color))
                else:
                    rollbar.report_message('Invalid Address',
                                           'warning',
                                           extra_data={
                                               'user': {
                                                   "id": author_id,
                                                   "address": "not supplied",
                                               }
                                           })
                    await message.reply(embed=discord.Embed(
                        title="Opps, You're not a dreamer ~",
                        description="""Address not supplied. Try again.""",
                        color=error_color))
            except:
                rollbar.report_exc_info()

        if message.content.startswith(allowlist_check_command):
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
            except:
                # do_something
                rollbar.report_exc_info()
                await message.reply(
                    embed=discord.Embed(title="Opps, You're not a dreamer ~",
                                        description="""Try again.""",
                                        color=error_color))

    if str(message.channel.id) == discord_config_channel:
        if message.content.startswith(allowlist_admin):
            try:
                if str(author_id) in discord_admin:
                    data = pd.DataFrame(
                        columns=['author', 'address', 'invocation'])
                    keys = db.keys()
                    for key in keys:
                        data = data.append(
                            {
                                'author': key,
                                'address': db[key]["address"],
                                'invocation': db[key]["invocation"]
                            },
                            ignore_index=True)

                    file_location = f"{str(message.channel.guild.id) + '_' + str(message.channel.id)}.csv"
                    data.to_csv(
                        file_location)  # Saving the file as a .csv via pandas

                    answer = discord.Embed(
                        title="Hi, admin! Here is the allowlist file",
                        description=
                        f"""It might have taken a while, but here is what you asked for.\n\n`Server` : **{message.guild.name}**\n`Channel` : **{message.channel.name}**""",
                        colour=success_color)
                    await message.author.send(embed=answer)
                    await message.author.send(file=discord.File(
                        file_location,
                        filename='data.csv'))  # Sending the file
                    os.remove(file_location)  # Deleting the file
                else:
                    raise ValueError("author ${author_id} not an admin".format(
                        author_id=author_id))
            except:
                rollbar.report_exc_info()


client.run(discord_token)
