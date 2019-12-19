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
		
		# Construct tthe final POST data and url.
		self.data = parse.urlencode(params).encode()				
		self.url = base_url

		# Auth with Google API.
		self.google_api_auth()

	def google_api_auth(self):
		"""Auth with Google.
		
		Check if there is a local cached auth token in token.pickle.
		If there's no cached token, then generate a new one via 
		webflow authentication.
		Finally dump the token in a pickle and then build the API 
		client with the credentials.
		"""
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
		"""Get the current list of gCal events.
		
		This allows us to check for events already added to the calendar. Can
		be extended to permit updating of changed events.
		TODO - Extend functionality for updating existing events.

		Returns:
			list -- A unique list of the Google Calendar event's Summary.
		"""
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
		"""Compare an event with all Google Calendar events.
		
		Take an event Summary and iterate through all gCalendar events.
		TODO: Probably more efficient to use a set() here.
		
		Arguments:
			summary {string} -- [description]
			events {list} -- List of Google Calendar events.
		
		Returns:
			list -- A list of matching events.
		"""
		lst = []		
		for event in events:
			if event.get('summary'):
				s1 = event['summary']
				if s1 == summary:							
					lst.append(event)
		return lst

	def already_exists(self, new_event):
		"""Check for events that already exist.
		
		Return True or False if an event exists.
		
		Arguments:
			new_event {dict} -- A dict describing a new event.
		
		Returns:
			bool -- If an event exists or not.
		"""
		events = self.get_gcal_date_events(new_event['summary'], self.get_google_calendar_events())
		event_list = [new_event['summary'] for new_event in events]		
		if new_event['summary'] not in event_list:
			return False
		else:
			return True

	def get_calendar_data(self):
		"""Query Wizkids Calendar (base url) with the POST data.
		
		Set the appropriate headers and then create a HTTP request
		to the Wizkids Calendar endpoint.
		
		Returns:
			dict -- Event data for the given query.
		"""
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
		"""Create a new event in Google Calendar.
		
		Takes the given parameters for an event and builds an event dictionary
		to create an event in Google Calendar via the Google API.
		
		Keyword Arguments:
			summary {str} -- Event title/summary. (default: {"HeroClix Event"})
			location {str} -- Event location. (default: {"Somewhere"})
			description {str} -- Longform details of event. (default: {"Get ready to rumble"})
			start_raw {str} -- Start time as a datetime-parsable string. (default: {None})
			attendees {list} -- List of guests to invite. (default: {[{'email':'nobody@gmail.com'}]})
		"""
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
