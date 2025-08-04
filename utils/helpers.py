import random
import string
import base64
from passlib.context import CryptContext
import asyncio

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generate_unique_hostel_id(hostel_name: str) -> str:
    prefix = ''.join(filter(str.isalnum, hostel_name))[:4].upper()
    suffix = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{suffix}"

def df_to_csv_download_link(df, filename="data.csv", link_text="Download CSV"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">{link_text}</a>'

def run_async(coro):
    """
    A helper function to safely run an async function from a sync context,
    avoiding the "event loop is already running" error on Streamlit Cloud.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)