from dotenv import load_dotenv
import os

load_dotenv('.env', override=True)


STAGE = os.getenv('STAGE')