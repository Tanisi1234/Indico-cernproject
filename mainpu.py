from flask import Flask, render_template
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

app = Flask(__name__)

# Load the Excel file
file_path = 'IndicoNoticePrint-main/indico_data1234.xlsx'
df = pd.read_excel(file_path)

# Extract category numbers from the first column
category_numbers = df.iloc[:, 0].tolist()

# Seminar category numbers
seminar_categories = {71, 2725, 103, 74, 75, 167, 3020, 79, 113, 82, 2401, 6214, 2051, 7868, 112, 111, 5805, 106, 94, 2434, 118, 590, 352, 10101}

# Function to clean HTML tags from a string
def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text()

# Sets to keep track of printed event titles and processed category numbers and URLs
printed_titles = set()
processed_category_numbers = set()
processed_urls = set()

# List to store events before rendering
events = []

# Function to process individual events
def process_event(event, category_number):
    title = event.get("title", "N/A")
    if title in printed_titles:
        return

    # Extract start_date information
    start_date_dict = event.get("startDate", {})
    start_date_str = start_date_dict.get("date", "N/A")
    start_time = start_date_dict.get("time", "N/A")
    start_tz = start_date_dict.get("tz", "N/A")

    # Concatenate start_date, start_time, and start_tz for display
    start_datetime = f"{start_date_str} {start_time} {start_tz}"

    # Extract end_date information
    end_date_dict = event.get("endDate", {})
    end_date_str = end_date_dict.get("date", "N/A")
    end_time = end_date_dict.get("time", "N/A")
    end_tz = end_date_dict.get("tz", "N/A")

    # Concatenate end_date, end_time, and end_tz for display
    end_datetime = f"{end_date_str} {end_time} {end_tz}"

    # Convert dates to datetime objects for comparison
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except ValueError:
        return  # Skip if date format is incorrect

    # Check if the end date is more than 7 days after the start date
    if (end_date - start_date).days > 7:
        return

    event_type = event.get("_type", "N/A")

    # Mark the event as a seminar if it belongs to seminar categories
    if category_number in seminar_categories:
        event_type = "Seminar"

    # Print event details only if the type is "Conference" or "Seminar"
    if event_type in ["Conference", "Seminar"]:
        event_details = {
            "title": title,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "event_type": event_type
        }
        events.append(event_details)

        # Add title to printed set
        printed_titles.add(title)

# Function to process events for a given category number
def process_events(category_number, start_date, end_date):
    if category_number in processed_category_numbers:
        return

    base_url = f"https://indico.cern.ch/export/categ/{category_number}.json?from={start_date}&to={end_date}&pretty=yes"
    response = requests.get(base_url)

    # Check if the request was successful
    if response.status_code == 200:
        try:
            # Parse the JSON data
            json_data = response.json()

            # Iterate through each event in the JSON data
            for event in json_data["results"]:
                process_event(event, category_number)

                # Check for the "Show" URL to look up more events
                if "show" in event:
                    show_url = event["show"]
                    fetch_additional_events(show_url, start_date, end_date, category_number)
        except ValueError as e:
            print(f"Error parsing JSON data: {e}")
    else:
        print(f"Failed to retrieve data for category {category_number}, status code: {response.status_code}")

    # Add category number to processed set
    processed_category_numbers.add(category_number)

# Function to fetch additional events from the "Show" URL
def fetch_additional_events(show_url, start_date, end_date, category_number):
    if show_url in processed_urls:
        return

    response = requests.get(show_url)

    # Check if the request was successful
    if response.status_code == 200:
        try:
            # Parse the JSON data
            json_data = response.json()

            # Iterate through each additional event in the JSON data
            for event in json_data["results"]:
                # Check if the additional event is within the same date range
                event_date_str = event.get("startDate", {}).get("date", "")
                if event_date_str:
                    event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
                    if start_date <= event_date <= end_date:
                        process_event(event, category_number)
        except ValueError as e:
            print(f"Error parsing JSON data: {e}")
    else:
        print(f"Failed to retrieve additional events from URL, status code: {response.status_code}")

    # Add URL to processed set
    processed_urls.add(show_url)

# Calculate today's date and the end date (one week from today)
today = datetime.today()
one_week_later = today + timedelta(days=7)
start_date = today.strftime('%Y-%m-%d')
end_date = one_week_later.strftime('%Y-%m-%d')

# Loop through each day from today to one week later and process events
current_date = today
while current_date <= one_week_later:
    for category_number in category_numbers:
        process_events(category_number, current_date.strftime('%Y-%m-%d'), end_date)
    current_date += timedelta(days=1)

# Render the template with events data
@app.route('/')
def index():
    return render_template('upcoming_events.html', events=events)

if __name__ == '__main__':
    app.run(debug=True, port=300)
