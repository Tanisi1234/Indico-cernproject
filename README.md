# Indico-cernproject
## Overview
This project is a Flask-based web application designed to interact with the Indico API provided by CERN. The application reads category IDs from an Excel sheet and retrieves upcoming events based on specific criteria: conferences for the next six months and seminars for the next seven days. The event data is then stored in a SQLite database and displayed on a web page using HTML templates.

## Features
Excel Integration: Reads category IDs from an Excel file.
Event Fetching: Uses the Indico API to fetch upcoming conferences and seminars.
Dynamic Date Range: Fetches conferences scheduled within the next six months and seminars occurring within the next seven days.
Database Storage: Stores fetched event data in a SQLite database (events_database.db).
Web Interface: Displays the fetched events on a web page using HTML templates.



## Installation

1. **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/your-repo-name.git
    cd your-repo-name
    ```

2. **Set Up Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows use `venv\Scripts\activate`
    ```

3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4. **Run the Application**
    ```bash
    flask run
    ```
## Configure the Application

Place your Excel file containing the category IDs in the project directory.
Update the configuration in config.py to point to your Excel file and any other necessary settings.

## Usage
1. Fetch and Store Events
```bash
   python upcomingevents.py
```
This script reads category IDs from the Excel file, fetches the event data from the Indico API, and stores it in the SQLite database (events_database.db).
    
2. Run the Flask Application
   ```bash
    flask run
    ```

3. Access the Web Interface
Open your web browser and navigate to http://127.0.0.1:5000/.
The home page will display the upcoming events based on the fetched data.

## Indico API Integration
The application fetches event data from the Indico API using the following endpoint format:

```bash
base_url = f"https://indico.cern.ch/export/categ/{category_number}.json?from={start_date}&to={end_date}&pretty=yes"
 ```
Category Number: Retrieved from the Excel file.
Start Date: Current date.
End Date: Conferences: Current date + 6 months.
          Seminars: Current date + 7 days.

          
## Example Workflow
1. Read Category IDs from Excel:
The application reads category IDs from an Excel sheet named categories.xlsx located in the project directory.

2. Fetch Event Data:
The upcomingevents.py script constructs the API URL for each category ID, fetches the event data, and stores it in the SQLite database.

3.Display Events:
The Flask application reads the stored events from the database and displays them on the web page using the basic.html template.


![image](https://github.com/Tanisi1234/Indico-cernproject/assets/129652819/b762608e-a2fc-4881-b47a-e8f33f5c3e71)


printing each event:
![image](https://github.com/Tanisi1234/Indico-cernproject/assets/129652819/6dda38e4-8cda-47cb-835e-7619bfaf358e)
![image](https://github.com/Tanisi1234/Indico-cernproject/assets/129652819/1cf2ff29-68d4-4e21-955c-13121b12c0ff)



