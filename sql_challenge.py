import mysql.connector
from uuid import uuid4
from datetime import datetime

class SQLChallengeDatabase:
    challenge_ids = []
    # Database connection parameters
    HOST = 'discord-1.cfmcues88vcl.ap-southeast-2.rds.amazonaws.com'
    USER = 'admin'
    PASSWORD = 'sabyr123'
    DATABASE = 'discord_bot'

    @staticmethod
    def get_connection():
        return mysql.connector.connect(
            host=SQLChallengeDatabase.HOST,
            user=SQLChallengeDatabase.USER,
            password=SQLChallengeDatabase.PASSWORD,
            database=SQLChallengeDatabase.DATABASE
        )

    @staticmethod
    async def create_challenge(user_id1, user_id2, date, price, wallet):
        try:
            # Convert the date from DD-MM-YYYY to YYYY-MM-DD
            date_obj = datetime.strptime(str(date), '%d-%m-%Y')
            formatted_date = date_obj.strftime('%Y-%m-%d')  # Format the date in the correct format for SQL
        except ValueError as e:
            # Log the error and perhaps return or handle it
            print(f"Date format error: {e}")
            return None  # or raise an exception, or handle it as per your application logic

        print(formatted_date)
        challenge_id = str(uuid4())
        conn = SQLChallengeDatabase.get_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO challenges (challenge_id, user_id1, user_id2, date, price, accept, channel_created, wallet) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(query, (challenge_id, user_id1, user_id2, formatted_date, price, 1, 0, wallet))
        conn.commit()
        cursor.close()
        conn.close()
        return challenge_id

    @staticmethod
    def get_challenge(challenge_id):
        conn = SQLChallengeDatabase.get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM challenges WHERE challenge_id = %s;"
        cursor.execute(query, (challenge_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result

    @staticmethod
    def accept_challenge(challenge_id):
        conn = SQLChallengeDatabase.get_connection()
        cursor = conn.cursor()
        query = "UPDATE challenges SET accept = 1 WHERE challenge_id = %s;"
        cursor.execute(query, (challenge_id,))
        affected_rows = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        return affected_rows > 0


    @staticmethod
    def update_channel_created(challenge_id):
        conn = SQLChallengeDatabase.get_connection()
        cursor = conn.cursor()
        query = "UPDATE challenges SET channel_created = 1 WHERE challenge_id = %s;"

        try:
            cursor.execute(query, (challenge_id,))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()



