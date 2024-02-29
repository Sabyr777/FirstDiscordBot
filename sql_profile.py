import discord
import mysql.connector

class Profile_Database:
    # Database connection parameters
    HOST = 'discord-1.cfmcues88vcl.ap-southeast-2.rds.amazonaws.com'
    USER = 'admin'
    PASSWORD = 'sabyr123'
    DATABASE = 'discord_bot'

    @staticmethod
    def get_connection():
        return mysql.connector.connect(
            host=Profile_Database.HOST,
            user=Profile_Database.USER,
            password=Profile_Database.PASSWORD,
            database=Profile_Database.DATABASE
        )

    @staticmethod
    def get_user_data(user_id):
        conn = Profile_Database.get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM profiles WHERE user_id = %s;"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result


    @staticmethod
    def set_user_data(data):
        conn = Profile_Database.get_connection()
        cursor = conn.cursor()
        query = """INSERT INTO profiles (user_id, name, user_picture, gender, age, about, price, discord_username, wallet) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) 
                   ON DUPLICATE KEY UPDATE 
                   name = VALUES(name), 
                   user_picture = VALUES(user_picture), 
                   gender = VALUES(gender), 
                   age = VALUES(age), 
                   about = VALUES(about), 
                   price = VALUES(price), 
                   discord_username = VALUES(discord_username),
                   wallet = VALUES(wallet);"""
        cursor.execute(query, (
            data.get('user_id'),
            data.get('name'),
            data.get('user_picture'),
            data.get('gender'),
            data.get('age'),
            data.get('about'),
            data.get('price'),
            data.get('discord_username'),
            data.get('wallet')
        ))
        conn.commit()
        cursor.close()
        conn.close()

    @staticmethod
    def get_all_user_ids():
        conn = Profile_Database.get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT user_id FROM profiles;"
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return [row['user_id'] for row in result]

    @staticmethod
    def get_profile_at_index(index):
        user_ids = Profile_Database.get_all_user_ids()
        if user_ids:
            user_id = user_ids[index % len(user_ids)]
            return Profile_Database.get_user_data(user_id)
        return None

    @staticmethod
    def get_next_user_data_excluding_user_id(start_index, exclude_user_id):
        user_ids = Profile_Database.get_all_user_ids()
        if not user_ids:
            return None

        # Adjust the start_index based on the length of the user_ids list
        adjusted_index = start_index % len(user_ids)

        # Try to find the next user profile that does not match the exclude_user_id
        for _ in range(len(user_ids)):  # Ensure we don't loop indefinitely
            potential_user_id = user_ids[adjusted_index]
            if potential_user_id != exclude_user_id:
                return Profile_Database.get_user_data(potential_user_id)
            adjusted_index = (adjusted_index + 1) % len(user_ids)  # Move to the next index, wrap around if necessary

        # If all user_ids are the same as exclude_user_id or no different user found, return None
        return None

    @staticmethod
    def add_wallet(user_id, wallet_value):
        conn = Profile_Database.get_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if the user exists and if so, update or insert the wallet value
        query = """
        INSERT INTO profiles (user_id, wallet) 
        VALUES (%s, %s) 
        ON DUPLICATE KEY UPDATE wallet = VALUES(wallet);
        """

        try:
            cursor.execute(query, (user_id, wallet_value))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    async def check_presence_and_send_invite(interaction: discord.Interaction, user_id: int, guild_id: int):
        target_guild = interaction.client.get_guild(guild_id)
        if not target_guild:
            # Respond or follow-up to interaction based on whether you've already responded
            await interaction.response.send_message("Target guild not found.", ephemeral=True)
            return False

        member = target_guild.get_member(user_id)
        if member:
            return True
        else:
            # The member does not exist in the target guild
            # Respond or follow-up to interaction based on whether you've already responded
            # This assumes you have not responded to the interaction yet
            await interaction.response.defer(ephemeral=True)
            for channel in target_guild.text_channels:
                if channel.permissions_for(target_guild.me).create_instant_invite:
                    invite = await channel.create_invite(reason="Inviting user to join guild")
                    await interaction.followup.send(f"User not found in the target guild. Here is an invite link to join: {invite.url}", ephemeral=True)
                    return False

            await interaction.followup.send("Unable to create an invite link. No suitable channel found.", ephemeral=True)
            return False

    # @staticmethod
    # def set_user_picture(user_id, picture_url):
    #     conn = Profile_Database.get_connection()
    #     cursor = conn.cursor()
    #     query = "UPDATE profiles SET user_picture = %s WHERE user_id = %s;"
    #     cursor.execute(query, (picture_url, user_id))
    #     conn.commit()
    #     cursor.close()
    #     conn.close()



###############################################################################################
    # Temporary in-memory storage for tracking if we're expecting a picture from the user
    expecting_picture_from_users = {}

    @staticmethod
    def is_expecting_picture(user_id):
        # Check if we're expecting a picture from this user
        return Profile_Database.expecting_picture_from_users.get(user_id, False)

    @staticmethod
    def set_user_picture(user_id, picture_url):
        # Update the 'expecting_picture' state
        Profile_Database.expecting_picture_from_users.pop(user_id, None)
        # Update the database with the new picture URL
        conn = Profile_Database.get_connection()
        cursor = conn.cursor()
        print(picture_url)
        query = "UPDATE profiles SET user_picture = %s WHERE user_id = %s;"
        cursor.execute(query, (picture_url, user_id))
        conn.commit()
        cursor.close()
        conn.close()

    # Call this method when you start expecting a picture from a user
    @staticmethod
    def expect_picture_from_user(user_id):
        Profile_Database.expecting_picture_from_users[user_id] = True

    # Call this method to stop expecting a picture from a user
    @staticmethod
    def stop_expecting_picture_from_user(user_id):
        Profile_Database.expecting_picture_from_users.pop(user_id, None)

