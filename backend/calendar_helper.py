from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import timedelta

# 1. Setup access to the robot
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'credentials.json'

# 2. YOUR Calendar ID (Found in your screenshot)
CALENDAR_ID = 'damodardhanush@gmail.com' 

def add_to_google_calendar(task_title, start_time):
    try:
        # Authenticate with the robot's key
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('calendar', 'v3', credentials=creds)

        # Set event to be 1 hour long by default
        end_time = start_time + timedelta(hours=1)

        # Create the event object
        event = {
            'summary': task_title,
            'description': 'Created via Smart Todo App',
            'start': {
                'dateTime': start_time.isoformat(),
            },
            'end': {
                'dateTime': end_time.isoformat(),
            },
        }

        # Send to Google
        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print(f"✅ Successfully added to Google Calendar: {task_title}")
        
    except Exception as e:
        print(f"❌ Failed to add to Calendar: {e}")