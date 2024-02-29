import discord
from sql_challenge import SQLChallengeDatabase
from discord.ext import commands, tasks
from play_view import PlayView
from profile_view import ProfileView
from sql_profile import Profile_Database
import aiohttp
import asyncio

intents = discord.Intents.default()
# Enable the message content intent
intents.message_content = True
intents.members = True
# Use the updated intents in your bot definition
bot = commands.Bot(command_prefix='!', intents=intents)

##### NEWLY ADDED CODE #####
@bot.event
async def on_message(message):
    # Ignore messages sent by the bot itself or messages without an attachment
    if message.author.bot or not message.attachments:
        return

    # Check if the user just completed their profile setup
    if Profile_Database.is_expecting_picture(message.author.id):
        # Assume the first attachment is the image
        image_url = message.attachments[0].url

        # Update the user's profile with the image URL
        Profile_Database.set_user_picture(message.author.id, image_url)
        # Confirm the update
        await message.channel.send("Profile picture updated successfully.")

##### NEWLY ADDED CODE #####
@bot.tree.command(name="profile", description="Access your profile")
async def profile(interaction: discord.Interaction):
    view = ProfileView()
    await interaction.response.send_message("Welcome onboard! To start being a part of SideQuest Bot, choose 'Setup/Edit Profile.' To check your existing profile, select 'Show Profile.' And don't forget to add your Binance ID/Wallet to be able to receive rewards!", view=view, ephemeral=True)

@bot.tree.command(name="play", description="Choose to play")
async def play(interaction: discord.Interaction):

    view = PlayView(interaction.user.id)
    # Acknowledge the interaction first
    await interaction.response.defer(ephemeral=True)
    # Now we can send the embed with followup.send since we deferred the response
    await interaction.followup.send(embed=view.profile_info, view=view, ephemeral=True)

@tasks.loop(seconds=120)
async def check_payment_and_create_channel():
    challenge_ids = SQLChallengeDatabase.challenge_ids
    async with aiohttp.ClientSession() as session:
        for challenge_id in list(challenge_ids):
            # http://localhost:5000/check_payment_status
            async with session.post(f"https://payout-back-test.aqua-creative.co/payment/status", json={"id": challenge_id}, timeout=30) as response:
                if response.status == 200:
                    status_string = await response.text()
                    # payment failed then do not continue loop
                    # print(f"This is string_link: {status_string}")
                    if status_string == "PAYIN_FAIL":
                        print(status_string)
                        challenge_ids.remove(challenge_id)
                        continue

                    if status_string == "PAYIN_SUCCESS":
                        challenge_ids.remove(challenge_id)
                        challenge = SQLChallengeDatabase.get_challenge(challenge_id)
                        target_guild_id = 1208438041174343690
                        guild = bot.get_guild(target_guild_id)

                        if guild is None:
                            print("Bot is not in the target guild.")
                            continue  # Skip to the next iteration

                        challenger = guild.get_member(int(challenge['user_id1']))
                        challenged = guild.get_member(int(challenge['user_id2']))
                        if not all([challenger, challenged]):
                            print("One or more users could not be found in this guild.")
                            continue

                        overwrites = {
                            guild.default_role: discord.PermissionOverwrite(view_channel=False),
                            challenger: discord.PermissionOverwrite(view_channel=True, connect=True),
                            challenged: discord.PermissionOverwrite(view_channel=True, connect=True)
                        }

                        channel_name = f"fight-{challenge_id[:8]}"
                        voice_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)
                        invite = await voice_channel.create_invite(max_age=86400)

                        try:
                            await challenger.send(f"You've been challenged! Join the fight text channel: {invite.url}")
                            await challenged.send(f"You've been challenged! Join the fight text channel: {invite.url}")
                            print(f"Private arena text channel created: {voice_channel.mention}. Invites sent.")
                        except discord.HTTPException:
                            print("Failed to send invite links to one or more participants.")

                        if SQLChallengeDatabase.update_channel_created(challenge_id):
                            print("Challenge updated successfully.")
                        else:
                            print("Failed to update the challenge.")

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.tree.sync()
    # bot.loop.create_task(check_payment_and_create_channel(bot))
    check_payment_and_create_channel.start()


bot.run('MTIwODQzMzk0MDA1MDg3NDQyOQ.GVSTXI.YEOKyJvOA4Jo_Tq63kARqTU7-pvjsfbNilg_40')
