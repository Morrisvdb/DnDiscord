from dotenv import load_dotenv
import os

class Config():
    load_dotenv()
    prefix = "!"
    TOKEN = os.getenv("DISCORD_TOKEN")
    
    db_host = os.getenv("DATABASE_HOST")
    db_name = os.getenv("DATABASE_NAME")
    db_user = os.getenv("DATABASE_USER")
    db_password = os.getenv("DATABASE_PASSWORD")
    
    db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:3306/{db_name}"
