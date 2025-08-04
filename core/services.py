import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import random
import string
import asyncio
from .database import get_db_connection, setup_database_tables
from utils import helpers as help

async def setup_database():
    await setup_database_tables()

def generate_pass_suffix():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))

# --- All functions are now async ---
async def register_hostel(hostel_name, admin_user_id, admin_password):
    hostel_id = help.generate_unique_hostel_id(hostel_name)
    hashed_password = help.hash_password(admin_password)
    async with get_db_connection() as conn:
        try:
            await conn.batch([
                libsql_client.Statement('INSERT INTO hostels (hostel_id, hostel_name) VALUES (?, ?)', [hostel_id.upper(), hostel_name]),
                libsql_client.Statement('INSERT INTO users (hostel_id, user_id, password_hash, role, added_by) VALUES (?, ?, ?, ?, ?)', [hostel_id.upper(), admin_user_id.upper(), hashed_password, 'admin', 'SYSTEM'])
            ])
            return hostel_id
        except Exception:
            return None

async def add_user(hostel_id, user_id, password, role, added_by):
    hashed_password = help.hash_password(password)
    async with get_db_connection() as conn:
        try:
            await conn.execute(
                'INSERT INTO users (hostel_id, user_id, password_hash, role, added_by) VALUES (?, ?, ?, ?, ?)',
                [hostel_id.upper(), user_id.upper(), hashed_password, role, added_by]
            )
            return True
        except Exception:
            return False

async def remove_user(hostel_id, user_id_to_remove):
    async with get_db_connection() as conn:
        rs = await conn.execute("SELECT id FROM users WHERE hostel_id = ? AND user_id = ?", [hostel_id.upper(), user_id_to_remove.upper()])
        if rs.rows:
            await conn.execute("DELETE FROM users WHERE id = ?", [rs.rows[0]["id"]])
            return True
        return False

async def change_password(hostel_id, user_id_to_change, new_password):
    new_hashed_password = help.hash_password(new_password)
    async with get_db_connection() as conn:
        rs = await conn.execute("SELECT id FROM users WHERE hostel_id = ? AND user_id = ?", [hostel_id.upper(), user_id_to_change.upper()])
        if rs.rows:
            await conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", [new_hashed_password, rs.rows[0]["id"]])
            return True
        return False

async def check_hostel_id_exists(hostel_id):
    async with get_db_connection() as conn:
        rs = await conn.execute('SELECT 1 FROM hostels WHERE hostel_id = ?', [hostel_id.upper()])
        return len(rs.rows) > 0

async def get_hostel_name(hostel_id):
    async with get_db_connection() as conn:
        rs = await conn.execute('SELECT hostel_name FROM hostels WHERE hostel_id = ?', [hostel_id.upper()])
        return rs.rows[0]["hostel_name"] if rs.rows else "Unknown"

async def get_hostel_summary(hostel_id):
    async with get_db_connection() as conn:
        name_rs = await conn.execute('SELECT hostel_name FROM hostels WHERE hostel_id = ?', [hostel_id.upper()])
        count_rs = await conn.execute("SELECT COUNT(*) as count FROM users WHERE hostel_id = ? AND role = 'student'", [hostel_id.upper()])
        return {"name": name_rs.rows[0]["hostel_name"] if name_rs.rows else "Unknown", "id": hostel_id, "student_count": count_rs.rows[0]["count"]}

async def authenticate_user(hostel_id, user_id, password):
    async with get_db_connection() as conn:
        rs = await conn.execute('SELECT password_hash, role FROM users WHERE hostel_id = ? AND user_id = ?', [hostel_id.upper(), user_id.upper()])
        if rs.rows and help.verify_password(password, rs.rows[0]["password_hash"]):
            return rs.rows[0]["role"]
        return None

# ... (other functions would need similar async conversion)
