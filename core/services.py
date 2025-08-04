import pandas as pd
from datetime import datetime, timedelta
import random
import string
from .database import get_db_connection
from utils import helpers as help
from libsql_client import Statement

async def setup_database():
    from .database import setup_database_tables
    await setup_database_tables()

def generate_pass_suffix():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))

# --- All functions that touch the DB are now async ---
async def register_hostel(hostel_name, admin_user_id, admin_password):
    hostel_id = help.generate_unique_hostel_id(hostel_name)
    hashed_password = help.hash_password(admin_password)
    async with get_db_connection() as conn:
        try:
            await conn.batch([
                Statement('INSERT INTO hostels (hostel_id, hostel_name) VALUES (?, ?)', [hostel_id.upper(), hostel_name]),
                Statement('INSERT INTO users (hostel_id, user_id, password_hash, role, added_by) VALUES (?, ?, ?, ?, ?)', [hostel_id.upper(), admin_user_id.upper(), hashed_password, 'admin', 'SYSTEM'])
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

async def submit_meal_response(hostel_id, student_id, breakfast, lunch, dinner):
    next_day = (datetime.now() + timedelta(days=1)).date().isoformat()
    async with get_db_connection() as conn:
        rs = await conn.execute('SELECT id FROM meal_responses WHERE hostel_id = ? AND student_id = ? AND response_date = ?', [hostel_id.upper(), student_id.upper(), next_day])
        if rs.rows:
            await conn.execute('UPDATE meal_responses SET breakfast = ?, lunch = ?, dinner = ? WHERE id = ?', [breakfast, lunch, dinner, rs.rows[0]['id']])
        else:
            await conn.execute('INSERT INTO meal_responses (hostel_id, student_id, response_date, breakfast, lunch, dinner) VALUES (?, ?, ?, ?, ?, ?)', [hostel_id.upper(), student_id.upper(), next_day, breakfast, lunch, dinner])

async def get_student_meal_info(hostel_id, student_id):
    next_day = (datetime.now() + timedelta(days=1)).date().isoformat()
    async with get_db_connection() as conn:
        rs = await conn.execute('SELECT breakfast, lunch, dinner, breakfast_pass, lunch_pass, dinner_pass FROM meal_responses WHERE hostel_id = ? AND student_id = ? AND response_date = ?', [hostel_id.upper(), student_id.upper(), next_day])
        return rs.rows[0] if rs.rows else None

async def get_live_meal_counts(hostel_id):
    next_day = (datetime.now() + timedelta(days=1)).date().isoformat()
    async with get_db_connection() as conn:
        rs = await conn.execute('SELECT breakfast, lunch, dinner FROM meal_responses WHERE hostel_id = ? AND response_date = ?', [hostel_id.upper(), next_day])
        df = pd.DataFrame(rs.rows, columns=rs.columns)
        
        total_students_rs = await conn.execute("SELECT COUNT(*) as count FROM users WHERE hostel_id = ? AND role = 'student'", [hostel_id.upper()])
        total_students = total_students_rs.rows[0]['count'] if total_students_rs.rows else 0
        
        responded_count = len(df)
        unresponded_count = total_students - responded_count
        
        return {
            "breakfast": df['breakfast'].sum() + unresponded_count if not df.empty else unresponded_count,
            "lunch": df['lunch'].sum() + unresponded_count if not df.empty else unresponded_count,
            "dinner": df['dinner'].sum() + unresponded_count if not df.empty else unresponded_count,
            "responded": responded_count,
            "total": total_students
        }

async def generate_daily_report_and_passes(hostel_id):
    report_date = (datetime.now() + timedelta(days=1)).date().isoformat()
    async with get_db_connection() as conn:
        summary_rs = await conn.execute('SELECT 1 FROM daily_summary WHERE hostel_id = ? AND report_date = ?', [hostel_id.upper(), report_date])
        if summary_rs.rows:
            return "Report and passes for this date have already been generated."

        responses_rs = await conn.execute('SELECT id, student_id, breakfast, lunch, dinner FROM meal_responses WHERE hostel_id = ? AND response_date = ?', [hostel_id.upper(), report_date])
        
        batch_ops = []
        for res in responses_rs.rows:
            b_pass = f"BRK-{generate_pass_suffix()}" if res['breakfast'] else None
            l_pass = f"LCH-{generate_pass_suffix()}" if res['lunch'] else None
            d_pass = f"DNR-{generate_pass_suffix()}" if res['dinner'] else None
            batch_ops.append(Statement('UPDATE meal_responses SET breakfast_pass = ?, lunch_pass = ?, dinner_pass = ? WHERE id = ?', [b_pass, l_pass, d_pass, res['id']]))
        
        live_counts = await get_live_meal_counts(hostel_id)
        batch_ops.append(Statement('INSERT INTO daily_summary (hostel_id, report_date, total_students, breakfast_opt_in, lunch_opt_in, dinner_opt_in, responded_students) VALUES (?, ?, ?, ?, ?, ?, ?)', [hostel_id.upper(), report_date, live_counts['total'], live_counts['breakfast'], live_counts['lunch'], live_counts['dinner'], live_counts['responded']]))
        
        await conn.batch(batch_ops)
        return f"Successfully generated report and meal passes for {report_date}."

async def verify_meal_pass(hostel_id, meal_type, pass_suffix):
    pass_suffix = pass_suffix.upper()
    full_pass = f"{meal_type.upper()[:3]}-{pass_suffix}"
    pass_column = f"{meal_type.lower()}_pass"
    attended_column = f"{meal_type.lower()}_attended"
    report_date = (datetime.now() + timedelta(days=1)).date().isoformat()
    async with get_db_connection() as conn:
        rs = await conn.execute(f"SELECT id, student_id, {attended_column} FROM meal_responses WHERE hostel_id = ? AND {pass_column} = ? AND response_date = ?", [hostel_id.upper(), full_pass, report_date])
        if not rs.rows:
            return "Invalid Pass Code", None
        if rs.rows[0][attended_column]:
            return f"Pass already used by {rs.rows[0]['student_id']}", None
        await conn.execute(f"UPDATE meal_responses SET {attended_column} = TRUE WHERE id = ?", [rs.rows[0]['id']])
        return f"Pass Verified for {rs.rows[0]['student_id']}", rs.rows[0]['student_id']

async def add_bill(hostel_id, item_name, price):
    async with get_db_connection() as conn:
        await conn.execute("INSERT INTO bills (hostel_id, item_name, price, purchase_date) VALUES (?, ?, ?, ?)",
                           [hostel_id.upper(), item_name, price, datetime.now().date().isoformat()])

async def get_bills(hostel_id):
    async with get_db_connection() as conn:
        rs = await conn.execute("SELECT item_name, price, purchase_date FROM bills WHERE hostel_id = ? ORDER BY purchase_date DESC", [hostel_id.upper()])
        return pd.DataFrame(rs.rows, columns=rs.columns)