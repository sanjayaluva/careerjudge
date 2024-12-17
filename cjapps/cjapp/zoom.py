import requests
from django.conf import settings

class ZoomClient():
    """Zoom Meeting API Client"""

    def __init__(self):
        self.client_id = settings.ZOOM_CLIENT_ID
        self.account_id = settings.ZOOM_ACCOUNT_ID 
        self.client_secret = settings.ZOOM_CLIENT_SECRET 

        self.auth_token_url = "https://zoom.us/oauth/token"
        self.api_base_url = "https://api.zoom.us/v2"
        
        self.access_token = None

    def get_access_token(self):
        data = {
            "grant_type": "account_credentials",
            "account_id": self.account_id,
            "client_secret": self.client_secret
        }
        response = requests.post(self.auth_token_url, auth=(self.client_id, self.client_secret), data=data)
        
        if response.status_code != 200:
            print("Unable to get access token")
            return False

        response_data = response.json()
        self.access_token = response_data["access_token"]

        # return response_data["access_token"]

    # create the Zoom link function
    def create_meeting(self, topic, duration, start_datetime):
        if self.access_token == None:
            self.get_access_token() 

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "topic": topic,
            "duration": duration,
            'start_time': start_datetime, #f'{start_date}T{start_time}',
            "type": 2
        }

        resp = requests.post(f"{self.api_base_url}/users/me/meetings", headers=headers, json=payload)
        
        if resp.status_code != 201:
            print("Unable to generate meeting link")
            return False
        
        return resp.json()

    def delete_meeting(self, meetingId):
        if self.access_token == None:
            self.get_access_token() 
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        response = requests.delete(f"{self.api_base_url}/meetings/{meetingId}", headers=headers)
        
        if response.status_code != 204:
            print("Unable to delete meeting.")
            return False
    
        return response.json()

