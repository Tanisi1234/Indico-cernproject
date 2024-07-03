import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import sqlite3

# Load the Excel file
file_path = '/content/indico_data1234.xlsx'
df = pd.read_excel(file_path)

# Extract category numbers from the first column
category_numbers = df.iloc[:, 0].tolist()

# Specific category numbers to be treated as seminars
seminar_categories = {71, 2725, 103, 74, 75, 167, 3020, 79, 113, 82, 2401, 6214, 2051, 7868, 112, 111, 5805, 106, 94, 2434, 118, 590, 352, 10101}

# Function to clean HTML tags from a string
def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text()

# Sets to keep track of processed event IDs and processed category numbers
processed_event_ids = set()
processed_category_numbers = set()

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('events.db')
cursor = conn.cursor()

# Create tables for seminars and conferences
cursor.execute('''
    CREATE TABLE IF NOT EXISTS seminars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        meeting_type TEXT,
        start_date TEXT,
        end_date TEXT,
        description TEXT,
        speaker TEXT,
        affiliation TEXT,
        url TEXT,
        UNIQUE(title, start_date, end_date, url)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS conferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        meeting_type TEXT,
        start_date TEXT,
        end_date TEXT,
        description TEXT,
        speaker TEXT,
        affiliation TEXT,
        url TEXT,
        UNIQUE(title, start_date, end_date, url)
    )
''')

# Function to process individual events
def process_event(event, category_number, event_type_filter):
    event_id = event.get("id", "Not Available")
    if event_id in processed_event_ids:
        return

    title = event.get("title", "Not Available")
    start_date_dict = event.get("startDate", {})
    start_date_str = start_date_dict.get("date", "Not Available")
    start_time = start_date_dict.get("time", "Not Available")
    start_tz = start_date_dict.get("tz", "Not Available")
    start_datetime = f"{start_date_str} {start_time} {start_tz}"

    end_date_dict = event.get("endDate", {})
    end_date_str = end_date_dict.get("date", "Not Available")
    end_time = end_date_dict.get("time", "Not Available")
    end_tz = end_date_dict.get("tz", "Not Available")
    end_datetime = f"{end_date_str} {end_time} {end_tz}"

    event_type = event.get("_type", "Not Available")
    description = clean_html(event.get("description", "Not Available"))

    if "chairs" in event:
        speaker_details = [(chair.get("fullName", "Not Available"), chair.get("affiliation", "Not Available")) for chair in event["chairs"]]
    else:
        speaker_details = [("Not Available", "Not Available")]

    if event_type == event_type_filter or (event_type_filter == "Seminar" and category_number in seminar_categories):
        table_name = 'seminars' if event_type_filter == "Seminar" else 'conferences'
        for speaker, affiliation in speaker_details:
            cursor.execute(f'''
                INSERT OR IGNORE INTO {table_name} (title, meeting_type, start_date, end_date, description, speaker, affiliation, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, event_type, start_datetime, end_datetime, description, speaker, affiliation, event.get("url", "Not Available")))

        conn.commit()
        processed_event_ids.add(event_id)

# Function to process events for a given category number
def process_events(category_number, start_date, end_date, event_type_filter):
    if category_number in processed_category_numbers:
        return

    base_url = f"https://indico.cern.ch/export/categ/{category_number}.json?from={start_date}&to={end_date}&pretty=yes"
    response = requests.get(base_url)

    if response.status_code == 200:
        json_data = response.json()

        for event in json_data["results"]:
            process_event(event, category_number, event_type_filter)

            if "show" in event:
                show_url = event["show"]
                fetch_additional_events(show_url, start_date, end_date, event_type_filter)
    else:
        print(f"Failed to retrieve data for category {category_number}, status code: {response.status_code}")

    processed_category_numbers.add(category_number)

# Function to fetch additional events from the "Show" URL
def fetch_additional_events(show_url, start_date, end_date, event_type_filter):
    response = requests.get(show_url)

    if response.status_code == 200:
        json_data = response.json()

        for event in json_data["results"]:
            event_date_str = event.get("startDate", {}).get("date", "")
            if event_date_str:
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
                if start_date <= event_date <= end_date:
                    process_event(event, 0, event_type_filter)
    else:
        print(f"Failed to retrieve additional events from URL, status code: {response.status_code}")

# Calculate today's date and the end dates for seminars (one week from today) and conferences (one month from today)
today = datetime.today()
one_month_later = today + timedelta(days=30)
one_week_later = today + timedelta(days=7)
start_date = today.strftime('%Y-%m-%d')
end_date_seminars = one_week_later.strftime('%Y-%m-%d')
end_date_conferences = one_month_later.strftime('%Y-%m-%d')

# Loop through each day from today to one month later and process conferences
current_date = today
while current_date <= one_month_later:
    for category_number in category_numbers:
        process_events(category_number, current_date.strftime('%Y-%m-%d'), end_date_conferences, "Conference")
    current_date += timedelta(days=1)

# Loop through each day from today to one week later and process seminars
current_date = today
while current_date <= one_week_later:
    for category_number in category_numbers:
        process_events(category_number, current_date.strftime('%Y-%m-%d'), end_date_seminars, "Seminar")
    current_date += timedelta(days=1)

conn.close()
