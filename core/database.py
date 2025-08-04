import sqlite3
from contextlib import contextmanager
from datetime import date, datetime

def adapt_date_iso(val):
    return val.isoformat()

def convert_date_iso(val):
    return datetime.strptime(val.decode('utf-8'), '%Y-%m-%d').date()

sqlite3.register_adapter(date, adapt_date_iso)
sqlite3.register_converter("DATE", convert_date_iso)

DB_FILE = "multi_hostel_meals.db"

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def setup_database_tables():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS hostels (hostel_id TEXT PRIMARY KEY, hostel_name TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        
        # Updated users table with tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hostel_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ("student", "admin")),
                added_by TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hostel_id) REFERENCES hostels (hostel_id),
                UNIQUE (hostel_id, user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meal_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hostel_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                response_date DATE NOT NULL,
                breakfast BOOLEAN NOT NULL,
                lunch BOOLEAN NOT NULL,
                dinner BOOLEAN NOT NULL,
                breakfast_pass TEXT,
                lunch_pass TEXT,
                dinner_pass TEXT,
                breakfast_attended BOOLEAN DEFAULT FALSE,
                lunch_attended BOOLEAN DEFAULT FALSE,
                dinner_attended BOOLEAN DEFAULT FALSE,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hostel_id) REFERENCES hostels (hostel_id)
            )
        ''')

        cursor.execute('CREATE TABLE IF NOT EXISTS daily_summary (id INTEGER PRIMARY KEY AUTOINCREMENT, hostel_id TEXT NOT NULL, report_date DATE NOT NULL, total_students INTEGER, breakfast_opt_in INTEGER, lunch_opt_in INTEGER, dinner_opt_in INTEGER, responded_students INTEGER, FOREIGN KEY (hostel_id) REFERENCES hostels (hostel_id), UNIQUE (hostel_id, report_date))')
        
        cursor.execute('DROP TABLE IF EXISTS billing')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hostel_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                price REAL NOT NULL,
                purchase_date DATE NOT NULL,
                FOREIGN KEY (hostel_id) REFERENCES hostels (hostel_id)
            )
        ''')
        conn.commit()
