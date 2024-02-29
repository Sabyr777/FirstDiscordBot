import discord
from sql_challenge import SQLChallengeDatabase  # Adjusted import to use SQLChallengeDatabase
from sql_profile import Profile_Database
from discord.ui import Modal, TextInput, Button, View
from datetime import datetime, date
import aiohttp  # Make sure to import aiohttp
import asyncio

class GameScheduleModal(Modal):
    def __init__(self, user_index, *args, **kwargs):
        super().__init__(title="Schedule Your Game", *args, **kwargs)
        self.user_index = user_index
        self.add_item(TextInput(
            label="Enter the date (e.g., DD-MM-YYYY)",
            placeholder="24-02-2022",
            required=True,
            custom_id="game_date"
        ))
    async def on_submit(self, interaction: discord.Interaction):
        game_date = self.children[0].value

        # Validate date format
        try:
            parsed_game_date = datetime.strptime(game_date, '%d-%m-%Y').date()
        except ValueError:
            await interaction.response.send_message("Please enter the date in the correct format (DD-MM-YYYY).", ephemeral=True)
            return

        # Check if the game date is not in the past
        if parsed_game_date < date.today():
            await interaction.response.send_message("The game date cannot be in the past. Please enter a valid date.", ephemeral=True)
            return

        profile_data = Profile_Database.get_profile_at_index(self.user_index)
        user_id1 = interaction.user.id
        user_id2 = profile_data['user_id']  # Assuming `user_id` is part of the profile data
        price = profile_data['price']
        wallet = profile_data["wallet"]
        challenge_id = await SQLChallengeDatabase.create_challenge(user_id1, user_id2, game_date, price, wallet)
        if profile_data:
            await PlayView.create_channel_new(interaction, challenge_id)
            discord_username = profile_data.get("discord_username", "someone")
            # Ensure only to use interaction.response for the initial response
            # if interaction.response.is_done():
            #     # If a response has been sent, use followup for subsequent messages
            #     await interaction.followup.send(f"You have challenged {discord_username} on {game_date}. Please wait for payment process.", ephemeral=True)
            # else:
            #     # If no response has been sent yet, use response.send_message
            #     await interaction.response.send_message(f"You have challenged {discord_username} on {game_date}. Please wait for payment process.", ephemeral=True)
        else:
            # Handle the case where no profile is found similarly
            if interaction.response.is_done():
                await interaction.followup.send("No profile found to challenge.", ephemeral=True)
            else:
                await interaction.response.send_message("No profile found to challenge.", ephemeral=True)



class PlayView(View):
    def __init__(self, user_id, user_index=0):
        super().__init__(timeout=None)
        self.user_index = user_index
        self.show_user_profile(user_id)

    def show_user_profile(self, user_id):
        profile_data = Profile_Database.get_profile_at_index(self.user_index)
        if profile_data:
            if profile_data["user_id"] != str(user_id):
                username1 = profile_data["name"]
                age1 = profile_data["age"]
                profilepic1 = profile_data["user_picture"]
                description1 = profile_data["about"]
                gender1 = profile_data["gender"]
                price1 = profile_data["price"]
                # wallet_id = profile_data["wallet"]

                embed1 = discord.Embed(title=username1, description=", ".join(""))
                fields = [
                    ("Price:", price1, True),
                    ("Gender:", gender1, True),
                    ("Age:", age1, True),
                    # ("Wallet ID:", wallet_id, False),
                    ("About me:", description1, False)
                ]

                for name, value, inline in fields:
                    embed1.add_field(name=name, value=value, inline=inline)

                embed1.set_image(url=profilepic1)
                embed1.set_footer(text="Powered by SideQuest")

                self.profile_info = embed1
            else:
                self.user_index += 1
                self.show_user_profile(user_id)
        else:
            self.profile_info = "No profiles found or end of profile list reached. Starting over."
            self.user_index = -1  # Reset index for next button press

    @discord.ui.button(label="Play", style=discord.ButtonStyle.success, custom_id="play_user")
    async def play(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await Profile_Database.check_presence_and_send_invite(interaction=interaction, user_id=interaction.user.id, guild_id=1208438041174343690):
            modal = GameScheduleModal(user_index=self.user_index)
            await interaction.response.send_modal(modal)
            return
        await interaction.response.send_modal("Please join to our discord channel!!!")


    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, custom_id="next_user")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.user_index += 1  # Move to the next profile
        self.show_user_profile(interaction.user.id)  # Update the profile info
        # Fix for responding to interaction
        if interaction.response.is_done():
            # If response is already sent, use followup to edit the message
            await interaction.followup.send(embed=self.profile_info, view=self, ephemeral=True)
        else:
            # Properly defer and then edit the original response
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_response(embed=self.profile_info, view=self)

    @staticmethod
    async def create_channel_new(interaction, challenge_id):

        await interaction.response.defer(ephemeral=True)  # Defer to indicate a response will be sent later.

        # Get the challenge details
        challenge = SQLChallengeDatabase.get_challenge(challenge_id)
        challenge_date_str = challenge['date'].isoformat() if isinstance(challenge['date'], datetime) else challenge['date']


        # Define the payment API URL and the payload
        # http://localhost:5000/request_payment
        payment_api_url = "https://payout-back-test.aqua-creative.co/payment/order"
        payload = {
            "id": challenge_id,
            "paymentAmount": str(challenge['price']),
            "walletId": challenge["wallet"],
            "orderDate": challenge_date_str,
        }

        ############# 60 SECONDS WAIT #################
        async with aiohttp.ClientSession() as session:
            try:
                # Set a timeout for the API call
                async with session.post(payment_api_url, json=payload, timeout=60) as response:
                    if response.status == 200:
                        # Assuming the payment system responds with JSON including a status field
                        string_link = await response.text()
                        await interaction.followup.send(f"Please go to the link {string_link}", ephemeral=True)
                        SQLChallengeDatabase.challenge_ids.append(payload["id"])
                        return
                    else:
                        await interaction.followup.send("Failed to verify payment. Challenge creation cancelled.", ephemeral=True)
                        return
            except asyncio.TimeoutError:
                await interaction.followup.send("Payment verification timed out. Challenge creation cancelled.", ephemeral=True)
                return
