import discord
from discord.ui import Modal, TextInput
# from request_handler_profile import JSONDatabase
from discord import TextStyle
from sql_profile import Profile_Database

class WalletModal(Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(title="Add Your Wallet", *args, **kwargs)

        self.add_item(TextInput(
            label="Enter your wallet number",
            placeholder="Wallet Number",
            required=True,
            custom_id="wallet_number"
        ))

    async def on_submit(self, interaction: discord.Interaction):
        wallet_number = self.children[0].value
        user_id = interaction.user.id

        # Assuming JSONDatabase.add_wallet() is adjusted to simply update the wallet field
        user_exists = Profile_Database.add_wallet(user_id, wallet_number)

        if user_exists:
            await interaction.response.send_message("Wallet added successfully.", ephemeral=True)
        else:
            await interaction.response.send_message("User not found.", ephemeral=True)


class ProfileModal(Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_item(TextInput(label="What is your name?", placeholder="John Doe", required=True))
        self.add_item(TextInput(label="What is your gender?", placeholder="Male/Female/Other", required=True))
        self.add_item(TextInput(label="What is your age?", placeholder="18", required=True))
        self.add_item(TextInput(label="Tell about yourself", style=TextStyle.long, required=True))
        self.add_item(TextInput(label="Price for an hour of gaming with you", placeholder="Enter the price per hour in USD", required=True))
        # self.add_item(TextInput(label="What is your Binance ID/Wallet number?", placeholder="Enter your Binance ID/Wallet", required=True))

    async def on_submit(self, interaction: discord.Interaction):
            # Extract values from modal
            name = self.children[0].value
            gender = self.children[1].value
            age = self.children[2].value
            about = self.children[3].value
            price = self.children[4].value
            # Validate age and price to ensure they are numeric
            if not age.isdigit():
                await interaction.response.send_message("Please enter a numeric value for age.", ephemeral=True)
                return

            try:
                float_price = float(price)  # This will raise ValueError if price is not a number
            except ValueError:
                await interaction.response.send_message("Please enter a numeric value for price.", ephemeral=True)
                return

            # If validation passes, prepare the user data
            user_data = {
                'name': name,
                'gender': gender,
                'age': int(age),  # Convert age to an integer
                'about': about,
                'price': float_price,  # Use the converted float value for price
                'discord_username': f"{interaction.user.name}#{interaction.user.discriminator}",
                'user_id': interaction.user.id,
                'user_picture': None,
                'wallet': None
            }

            # Set user data in the database
            Profile_Database.set_user_data(user_data)

            Profile_Database.expect_picture_from_user(interaction.user.id)
            print(Profile_Database.expecting_picture_from_users)
            # Send a confirmation message to the user
            await interaction.response.send_message("Profile updated successfully. Please upload a profile picture now.", ephemeral=True)

class ProfileView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Set timeout=None if you don't want the buttons to expire

    @discord.ui.button(label="Setup/Edit Profile", style=discord.ButtonStyle.primary, custom_id="setup_profile")
    async def setup_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Correctly respond to the interaction
        modal = ProfileModal(title="Create Profile")

        if await Profile_Database.check_presence_and_send_invite(interaction=interaction, user_id=interaction.user.id, guild_id=1208438041174343690):
            await interaction.response.send_modal(modal)
            return
        await interaction.response.send_modal("Please join to our discord channel!!!")

    @discord.ui.button(label="Show Profile", style=discord.ButtonStyle.success, custom_id="show_profile")
    async def show_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await Profile_Database.check_presence_and_send_invite(interaction=interaction, user_id=interaction.user.id, guild_id=1208438041174343690):
            # Fetch the user data from the database
            user_data = Profile_Database.get_user_data(interaction.user.id)
            # If profile exists, format and send the user data
            if user_data:
                name = user_data['name']
                user_picture = user_data['user_picture']
                age = user_data['age']
                gender = user_data['gender']
                user_about = user_data['about']
                wallet = user_data['wallet']

                embed = discord.Embed(title=name)
                fields = [
                    ("Gender: ", gender, True),
                    ("Age: ", age, True),
                    ("Wallet ID: ", wallet, True),
                    ("About me: ", user_about, True)
                ]

                for name, value, inline in fields:
                    embed.add_field(name=name, value=value, inline=inline)

                embed.set_image(url=user_picture)
                embed.set_footer(text="Powered by SideQuest")

                # Acknowledge the interaction first
                await interaction.response.defer()
                # Now we can send the embed with followup.send since we deferred the response
                await interaction.followup.send(embed=embed, ephemeral = True)
            else:
                # If the profile does not exist, prompt the user to set up their profile
                await interaction.response.send_message("Please set up your profile.", ephemeral=True)

    @discord.ui.button(label="Add Binance ID/Wallet", style=discord.ButtonStyle.secondary, custom_id="add_wallet")
    async def add_wallet(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await Profile_Database.check_presence_and_send_invite(interaction=interaction, user_id=interaction.user.id, guild_id=1208438041174343690):
            # Show the modal for adding a wallet
            modal = WalletModal()
            await interaction.response.send_modal(modal)
