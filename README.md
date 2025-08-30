**Hostel Meal Manager**
Problem Statement
Hostel Meal Manager is a data-driven solution for hostels to efficiently manage meal planning, reduce food waste, and streamline communication between students and administration.

Features
This application provides a seamless experience for both students and administrators with role-based access and functionalities:

For Students:
Secure Login: Students can log in with their unique credentials for their specific hostel.

Meal Selection: Students can opt-in or out of upcoming meals (breakfast, lunch, and dinner) before a daily cut-off time.

Meal Pass Generation: After the cut-off time, the app generates unique meal passes for the selected meals.

Dashboard: A clean and intuitive dashboard to manage meal choices.

For Admins:
Secure Admin Login: Admins have a separate, secure login to manage the hostel's meal system.

Live Meal Counts: Admins can view a live dashboard with the total number of students opting in for each meal for the next day, allowing for better meal planning.

User Management: Admins can add, remove, and manage student and other admin accounts.

Password Management: Admins have the ability to change passwords for users.

Meal Pass Verification: Mess staff can easily verify meal passes by entering a unique code for each meal.

Bill & Expense Management: Admins can track and manage mess-related expenses.

Daily Report Generation: After the daily cut-off, admins can generate a final report with the total meal counts.

Tech Stack
The technologies used in this project were chosen to create a robust, scalable, and easy-to-use application.

Technology	Purpose
Streamlit	The core framework for building the web application. Its simplicity and speed of development make it ideal for data-driven applications and internal tools like this.
libsql-client	The official Python client for Turso DB, a distributed SQLite-compatible database. It provides a simple and efficient way to interact with the database.
Turso DB	A distributed SQLite for production. It's a serverless database that's easy to use and scales with the application.
Pandas	Used for data manipulation and analysis, especially for handling and displaying billing information.
Passlib & Bcrypt	For securely hashing and verifying user passwords.

Export to Sheets
Architectural Decisions
The decision to use Streamlit as the frontend framework was a key architectural choice for this project. Streamlit's primary advantage is its ability to rapidly create data-centric web applications with minimal code. This allowed for a focus on the core business logic—meal management and data analysis—rather than on complex frontend development.

However, this choice comes with a trade-off. Streamlit executes the entire script from top to bottom on every user interaction, which can be inefficient for applications with complex state management. To mitigate this, we've used Streamlit's session state to maintain user login status and other session-specific data.

Another important architectural decision was to use an asynchronous database driver (libsql_client) with a synchronous framework (Streamlit). To handle this, a helper function, run_async, was implemented to safely run asynchronous database operations from the synchronous Streamlit environment. This prevents the "event loop is already running" error common in such scenarios and ensures non-blocking database calls, which is crucial for a responsive user experience.

**Setup & Installation**
To get the Hostel Meal Manager running locally, follow these simple steps:

Clone the repository:
Bash
git clone <your-repository-url>
cd hostel-meal-manager

Create a virtual environment and activate it:
Bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

Install the dependencies:
Bash
pip install -r requirements.txt

Set up your Turso database credentials:
Create a .streamlit/secrets.toml file in the root of your project.
Add your Turso database URL and auth token to this file:
Ini, TOML
TURSO_DATABASE_URL = "your-turso-database-url"
TURSO_AUTH_TOKEN = "your-turso-auth-token"

Run the application:
Bash
streamlit run app.py
The application should now be running and accessible in your web browser.
