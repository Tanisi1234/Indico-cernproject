import sqlite3
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Corrected database path
db_path = r"C:\Users\Tanisi\OneDrive\Desktop\Flask\venv\IndicoNoticePrint-main\events (3).db"

# Function to clean HTML tags from a string
def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text()

# Function to fetch events from Indico API
def fetch_events(category_number, start_date, end_date):
    url = f"https://indico.cern.ch/export/categ/{category_number}.json?from={start_date}&to={end_date}&pretty=yes"
    response = requests.get(url)

    events_data = []

    if response.status_code == 200:
        json_data = response.json()
        for event in json_data.get("results", []):
            title = event.get("title", "N/A")
            start_date = event.get("startDate", "N/A")
            start_time = event.get("timezone", "N/A")
            end_date = event.get("endDate", "N/A")
            event_id = event.get("id", "N/A")
            location = event.get("location", "N/A")
            description = event.get("description", "N/A")
            url = event.get("url", "N/A")

            # Clean HTML tags from description
            clean_description = clean_html(description)

            events_data.append({
                "Title": title,
                "Start Date": start_date,
                "Start Time": start_time,
                "End Date": end_date,
                "Category ID": event_id,
                "Location": location,
                "Description": clean_description,
                "URL": url
            })
    else:
        print(f"Failed to fetch data for category {category_number}, status code: {response.status_code}")

    return events_data

# Function to retrieve conference event details from the database
def get_conference_events(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT title, start_date, end_date, description, url FROM conferences")
    events = [{
        "Title": row[0],
        "Start Date": row[1],
        "End Date": row[2],
        "Description": row[3],
        "URL": row[4],
        "Location": "N/A"  # Default value if the location column is missing
    } for row in cursor.fetchall()]
    conn.close()
    return events

# Function to retrieve seminar event details from the database
def get_seminar_events(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT title, start_date, end_date, description, url FROM seminars")
    events = [{
        "Title": row[0],
        "Start Date": row[1],
        "End Date": row[2],
        "Description": row[3],
        "URL": row[4],
        "Location": "N/A"  # Default value if the location column is missing
    } for row in cursor.fetchall()]
    conn.close()
    return events

@app.route("/", methods=["GET", "POST"])
def index():
    conference_events = get_conference_events(db_path)
    seminar_events = get_seminar_events(db_path)
    return render_template("basic.html", conference_events=conference_events, seminar_events=seminar_events, forPrint=False)

@app.route("/process_form", methods=["POST"])
def process_form():
    # Retrieve form data
    view = request.form['view']
    category_number = request.form['category_number']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    
    # Fetch events data from Indico API
    events_data = fetch_events(category_number, start_date, end_date)
    
    # Render the selected template with the events data
    return render_template(f"{view}", events_data=events_data, forPrint=True)

if __name__ == "__main__":
    app.run(debug=True, port=3000)
