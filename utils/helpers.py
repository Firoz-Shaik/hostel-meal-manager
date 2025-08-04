import random
import string
import base64
from passlib.context import CryptContext

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
