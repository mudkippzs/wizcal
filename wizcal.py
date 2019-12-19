from __future__ import print_function

import json
import datetime
import pickle
import os.path
from geopy.geocoders import Nominatim
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from urllib import request, parse
from pprint import pprint as pp

# Set the scope of access for Google API. If modifying these scopes, delete the file: token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class Wizcal(object):
	"""Wizkids Event Calendar/gCalendar Syncing.
	
	A wrapper for an event calendar on Wizkids.com for Heroclix. Query the
	calendar and parse the results and then sync to a Google Calendar via
	Google API.
	"""
	
	def __init__(self, city="portland", country="United+States", distance=25):
		"""Instantiate a Wizcal object with a given location and max distance from location.
		
		Keyword Arguments:
			city {str} -- Filter by city (default: {"portland"})
			country {str} -- Filter by country (default: {"United+States"})
			distance {number} -- FIlter by distance (default: {25})
		"""
		
		base_url = "https://win.wizkids.com/actions/doSearch.php"
		current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d+%H:%M:%S")
		# Convert the location to a long/lat
		geolocator = Nominatim(user_agent='myapplication')
		location = geolocator.geocode("%s" % (city))
		print(current_timestamp)
		# Build the parameter list
		params = {
			"start":"0",
			"count":"12",
			"cLatitude": location.latitude,
			"cLongitude": location.longitude,
			"dateTime": current_timestamp,
			"storeevent":"1",
			"addressevent":""	,
			"zipevent": city,
			"country": country,
			"miles": distance,
			"gameType":"0",
			"gameUniverse":"0",
			"format":"-1",
			"eventType":"0",
			"program":"0"
		}
		
		self.data = parse.urlencode(params).encode()				
		self.url = base_url

		self.google_api_auth()

	def google_api_auth(self):
		creds = None
		if os.path.exists('token.pickle'):
			with open('token.pickle', 'rb') as token:
				creds = pickle.load(token)
		# If there are no (valid) credentials available, let the user log in.
		if not creds or not creds.valid:
			if creds and creds.expired and creds.refresh_token:
				creds.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file(
					'credentials.json', SCOPES)
				creds = flow.run_local_server(port=0)
			# Save the credentials for the next run
			with open('token.pickle', 'wb') as token:
				pickle.dump(creds, token)

		self.service = build('calendar', 'v3', credentials=creds)

	def get_google_calendar_events(self):
		page_token = None
		now = datetime.datetime.now().isoformat() + 'Z'
		while True:
			events = self.service.events().list(calendarId='primary', timeMin=now,
				maxResults=500, singleEvents=True,
				orderBy='startTime').execute()
			page_token = events.get('nextPageToken')
			if not page_token:
				break
		return events.get('items', [])

	def get_gcal_date_events(self, summary, events):
		lst = []		
		for event in events:
			if event.get('summary'):
				s1 = event['summary']
				if s1 == summary:							
					lst.append(event)
		return lst

	def already_exists(self, new_event):
		events = self.get_gcal_date_events(new_event['summary'], self.get_google_calendar_events())
		event_list = [new_event['summary'] for new_event in events]		
		if new_event['summary'] not in event_list:
			return False
		else:
			return True

	def get_calendar_data(self):
		data = self.data
		headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
		req = request.Request(self.url, data=data)		
		with request.urlopen(req) as resp:
			raw_data = resp.read()	
			encoding = resp.info().get_content_charset('utf8')  # JSON default
			json_resp = json.loads(raw_data.decode(encoding))
			json_cal = json.loads(json_resp["results"])
		return json_cal

	def create_new_event(self, summary="HeroClix Event", location="Somewhere", description="Get ready to rumble",start_raw=None, attendees = [{'email':'nobody@gmail.com'}]):
		
		start_datetime = datetime.datetime.strptime(start_raw, "%Y-%m-%d^%H:%M %p")		
		end = datetime.datetime.strptime(start_raw, "%Y-%m-%d^%H:%M %p") + datetime.timedelta(hours=3)

		event = {
			'summary': summary,
			'location': location,
			'description': description,
			'start': {
				'dateTime': start_datetime.isoformat(), #  format: '2015-05-28T17:00:00-07:00'
				'timeZone': 'America/Los_Angeles', # base on country?
				},
			'end': {
				'dateTime': end.isoformat(), #  format: '2015-05-28T17:00:00-07:00'
				'timeZone': 'America/Los_Angeles', # base on country?
				},
			'recurrence': [],
			'attendees': attendees,
			'reminders': {
				'useDefault': False,
				'overrides': [
					{'method': 'email', 'minutes': 24 * 60},
					{'method': 'popup', 'minutes': 10},
					],
			},
		}

		if not self.already_exists(event):						
			event = self.service.events().insert(calendarId='primary', body=event).execute()
			print('Event created: %s' % (event.get('htmlLink')))			
		else:
			print("Already have '%s' in the calendar" % (summary))
