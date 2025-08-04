import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import random
import string
from .database import get_db_connection, setup_database_tables
from utils import helpers as help

def setup_database():
    setup_database_tables()

def generate_pass_suffix():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))

# --- Hostel & User Management ---
def register_hostel(hostel_name, admin_user_id, admin_password):
    hostel_id = help.generate_unique_hostel_id(hostel_name)
    hashed_password = help.hash_password(admin_password)
    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO hostels (hostel_id, hostel_name) VALUES (?, ?)', (hostel_id.upper(), hostel_name))
            cursor.execute('INSERT INTO users (hostel_id, user_id, password_hash, role, added_by) VALUES (?, ?, ?, ?, ?)', (hostel_id.upper(), admin_user_id.upper(), hashed_password, 'admin', 'SYSTEM'))
            conn.commit()
            return hostel_id
        except sqlite3.IntegrityError:
            return None

def add_user(hostel_id, user_id, password, role, added_by):
    hashed_password = help.hash_password(password)
    with get_db_connection() as conn:
        try:
            conn.execute('INSERT INTO users (hostel_id, user_id, password_hash, role, added_by) VALUES (?, ?, ?, ?, ?)', 
                         (hostel_id.upper(), user_id.upper(), hashed_password, role, added_by))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def remove_user(hostel_id, user_id_to_remove):
    """Removes a user from the database."""
    with get_db_connection() as conn:
        user = conn.execute("SELECT id FROM users WHERE hostel_id = ? AND user_id = ?", (hostel_id.upper(), user_id_to_remove.upper())).fetchone()
        if user:
            conn.execute("DELETE FROM users WHERE id = ?", (user['id'],))
            conn.commit()
            return True
        return False

def change_password(hostel_id, user_id_to_change, new_password):
    """Changes the password for a specific user."""
    new_hashed_password = help.hash_password(new_password)
    with get_db_connection() as conn:
        user = conn.execute("SELECT id FROM users WHERE hostel_id = ? AND user_id = ?", (hostel_id.upper(), user_id_to_change.upper())).fetchone()
        if user:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hashed_password, user['id']))
            conn.commit()
            return True
        return False

def process_student_csv(hostel_id, uploaded_file, added_by):
    try:
        df = pd.read_csv(uploaded_file)
        if not {'user_id', 'password'}.issubset(df.columns):
            return 0, "CSV must contain 'user_id' and 'password' columns."
        count = 0
        for _, row in df.iterrows():
            if add_user(hostel_id, str(row['user_id']), str(row['password']), 'student', added_by):
                count += 1
        return count, f"Successfully added {count} new students."
    except Exception as e:
        return 0, f"Error processing CSV file: {e}"

# --- Other service functions (unchanged) ---
def check_hostel_id_exists(hostel_id):
    with get_db_connection() as conn:
        return conn.execute('SELECT 1 FROM hostels WHERE hostel_id = ?', (hostel_id.upper(),)).fetchone() is not None

def get_hostel_name(hostel_id):
    with get_db_connection() as conn:
        name = conn.execute('SELECT hostel_name FROM hostels WHERE hostel_id = ?', (hostel_id.upper(),)).fetchone()
        return name['hostel_name'] if name else "Unknown"

def get_hostel_summary(hostel_id):
    with get_db_connection() as conn:
        name = conn.execute('SELECT hostel_name FROM hostels WHERE hostel_id = ?', (hostel_id.upper(),)).fetchone()
        student_count = conn.execute("SELECT COUNT(*) FROM users WHERE hostel_id = ? AND role = 'student'", (hostel_id.upper(),)).fetchone()[0]
        return {"name": name['hostel_name'] if name else "Unknown", "id": hostel_id, "student_count": student_count}

def authenticate_user(hostel_id, user_id, password):
    with get_db_connection() as conn:
        user = conn.execute('SELECT password_hash, role FROM users WHERE hostel_id = ? AND user_id = ?', (hostel_id.upper(), user_id.upper())).fetchone()
        if user and help.verify_password(password, user['password_hash']):
            return user['role']
        return None

def submit_meal_response(hostel_id, student_id, breakfast, lunch, dinner):
    next_day = (datetime.now() + timedelta(days=1)).date()
    with get_db_connection() as conn:
        existing = conn.execute('SELECT id FROM meal_responses WHERE hostel_id = ? AND student_id = ? AND response_date = ?', (hostel_id.upper(), student_id.upper(), next_day)).fetchone()
        if existing:
            conn.execute('UPDATE meal_responses SET breakfast = ?, lunch = ?, dinner = ? WHERE id = ?', (breakfast, lunch, dinner, existing['id']))
        else:
            conn.execute('INSERT INTO meal_responses (hostel_id, student_id, response_date, breakfast, lunch, dinner) VALUES (?, ?, ?, ?, ?, ?)', (hostel_id.upper(), student_id.upper(), next_day, breakfast, lunch, dinner))
        conn.commit()

def get_student_meal_info(hostel_id, student_id):
    next_day = (datetime.now() + timedelta(days=1)).date()
    with get_db_connection() as conn:
        return conn.execute('SELECT breakfast, lunch, dinner, breakfast_pass, lunch_pass, dinner_pass FROM meal_responses WHERE hostel_id = ? AND student_id = ? AND response_date = ?', (hostel_id.upper(), student_id.upper(), next_day)).fetchone()

def get_live_meal_counts(hostel_id):
    next_day = (datetime.now() + timedelta(days=1)).date()
    with get_db_connection() as conn:
        df = pd.read_sql_query('SELECT breakfast, lunch, dinner FROM meal_responses WHERE hostel_id = ? AND response_date = ?', conn, params=(hostel_id.upper(), next_day))
        total_students = conn.execute("SELECT COUNT(*) FROM users WHERE hostel_id = ? AND role = 'student'", (hostel_id.upper(),)).fetchone()[0]
        responded_count = len(df)
        unresponded_count = total_students - responded_count
        return {"breakfast": df['breakfast'].sum() + unresponded_count, "lunch": df['lunch'].sum() + unresponded_count, "dinner": df['dinner'].sum() + unresponded_count, "responded": responded_count, "total": total_students}

def generate_daily_report_and_passes(hostel_id):
    report_date = (datetime.now() + timedelta(days=1)).date()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if cursor.execute('SELECT 1 FROM daily_summary WHERE hostel_id = ? AND report_date = ?', (hostel_id.upper(), report_date)).fetchone():
            return "Report and passes for this date have already been generated."
        responses = cursor.execute('SELECT id, student_id, breakfast, lunch, dinner FROM meal_responses WHERE hostel_id = ? AND response_date = ?', (hostel_id.upper(), report_date)).fetchall()
        for res in responses:
            b_pass = f"BRK-{generate_pass_suffix()}" if res['breakfast'] else None
            l_pass = f"LCH-{generate_pass_suffix()}" if res['lunch'] else None
            d_pass = f"DNR-{generate_pass_suffix()}" if res['dinner'] else None
            cursor.execute('UPDATE meal_responses SET breakfast_pass = ?, lunch_pass = ?, dinner_pass = ? WHERE id = ?', (b_pass, l_pass, d_pass, res['id']))
        live_counts = get_live_meal_counts(hostel_id)
        cursor.execute('INSERT INTO daily_summary (hostel_id, report_date, total_students, breakfast_opt_in, lunch_opt_in, dinner_opt_in, responded_students) VALUES (?, ?, ?, ?, ?, ?, ?)', (hostel_id.upper(), report_date, live_counts['total'], live_counts['breakfast'], live_counts['lunch'], live_counts['dinner'], live_counts['responded']))
        conn.commit()
        return f"Successfully generated report and meal passes for {report_date}."

def verify_meal_pass(hostel_id, meal_type, pass_suffix):
    pass_suffix = pass_suffix.upper()
    full_pass = f"{meal_type.upper()[:3]}-{pass_suffix}"
    pass_column = f"{meal_type.lower()}_pass"
    attended_column = f"{meal_type.lower()}_attended"
    report_date = (datetime.now() + timedelta(days=1)).date()
    with get_db_connection() as conn:
        student = conn.execute(f"SELECT id, student_id, {attended_column} FROM meal_responses WHERE hostel_id = ? AND {pass_column} = ? AND response_date = ?", (hostel_id.upper(), full_pass, report_date)).fetchone()
        if not student:
            return "Invalid Pass Code", None
        if student[attended_column]:
            return f"Pass already used by {student['student_id']}", None
        conn.execute(f"UPDATE meal_responses SET {attended_column} = TRUE WHERE id = ?", (student['id'],))
        conn.commit()
        return f"Pass Verified for {student['student_id']}", student['student_id']

def add_bill(hostel_id, item_name, price):
    with get_db_connection() as conn:
        conn.execute("INSERT INTO bills (hostel_id, item_name, price, purchase_date) VALUES (?, ?, ?, ?)",
                     (hostel_id.upper(), item_name, price, datetime.now().date()))
        conn.commit()

def get_bills(hostel_id):
    with get_db_connection() as conn:
        return pd.read_sql_query("SELECT item_name, price, purchase_date FROM bills WHERE hostel_id = ? ORDER BY purchase_date DESC",
                                 conn, params=(hostel_id.upper(),))
