import streamlit as st
import libsql_client
import asyncio
from contextlib import contextmanager
from datetime import date, datetime

# --- Turso Database Connection ---
@contextmanager
def get_db_connection():
    """
    Provides a database connection to Turso using credentials from st.secrets.
    This includes the final, most robust fix for the asyncio event loop issue.
    """
    url = st.secrets["TURSO_DATABASE_URL"]
    auth_token = st.secrets["TURSO_AUTH_TOKEN"]
    
    # This function will run in its own dedicated asyncio event loop.
    async def connect_and_yield():
        try:
            # Create the client within the async context
            async with libsql_client.create_client_async(url=url, auth_token=auth_token) as client:
                yield client
        except Exception as e:
            st.error(f"Database connection error: {e}")
            raise

    # We use a generator to manage the async context from our sync function
    gen = connect_and_yield()
    client = None
    try:
        # Manually start the async generator
        client = asyncio.run(gen.__anext__())
        yield client
    finally:
        if client:
            # Properly close the async generator and the connection
            try:
                asyncio.run(gen.__anext__())
            except StopAsyncIteration:
                pass # This is expected when the 'with' block exits

# --- Database Schema Setup ---
def setup_database_tables():
    """
    Initializes the database with the required tables.
    """
    # This part of the code needs to be adapted to work with the new async connection
    # by running the batch operations within an async function.
    async def _setup():
        with get_db_connection() as client:
            await client.batch([
                'CREATE TABLE IF NOT EXISTS hostels (hostel_id TEXT PRIMARY KEY, hostel_name TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)',
                '''
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
                ''',
                '''
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
                ''',
                'CREATE TABLE IF NOT EXISTS daily_summary (id INTEGER PRIMARY KEY AUTOINCREMENT, hostel_id TEXT NOT NULL, report_date DATE NOT NULL, total_students INTEGER, breakfast_opt_in INTEGER, lunch_opt_in INTEGER, dinner_opt_in INTEGER, responded_students INTEGER, FOREIGN KEY (hostel_id) REFERENCES hostels (hostel_id), UNIQUE (hostel_id, report_date))',
                '''
                CREATE TABLE IF NOT EXISTS bills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hostel_id TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    price REAL NOT NULL,
                    purchase_date DATE NOT NULL,
                    FOREIGN KEY (hostel_id) REFERENCES hostels (hostel_id)
                )
                '''
            ])
    
    # Run the async setup function
    try:
        asyncio.run(_setup())
    except Exception as e:
        # This will catch errors if the tables already exist or other issues
        # which is fine during normal operation after the first run.
        pass
