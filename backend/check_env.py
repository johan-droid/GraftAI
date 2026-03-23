import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
print('DATABASE_URL', os.getenv('DATABASE_URL'))
print('PINECONE_API_KEY', os.getenv('PINECONE_API_KEY'))
print('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY'))
print('REDIS_URL', os.getenv('REDIS_URL'))
