import json
from pprint import pprint as pp
from user_config import CONFIG
from wizcal import Wizcal


def main():
	pass

if __name__ == '__main__':
	for location in CONFIG["locations"]:
		wc = Wizcal(city=location[0], country=location[1])
		calendars = wc.get_calendar_data()
		print("%s" % (location.upper()))
		for events in calendars:
			name = events["EVENT_NAME"]
			address = events["ADDRESS1"]
			store = events["STORE_NAME"]
			eventFormat = events["EVENT_FORMAT"]
			email = events["EMAIL_ADDRESS"]
			phone = events["PHONE_NUMBER"]
			web = events["URL"]
			date = events["EVENT_DATE"]
			gMap = events["googleMapUrl"]
			attendees = CONFIG["guest_list"]
			summary = "%s - %s (%s)" % (name, eventFormat, store)
			desc =""" 
			Venue: %s
			Format: %s

			ADD: %s

			P: %s
			E: %s
			W: %s

			gMap: %s""" % (store, eventFormat, address,
				phone, email, web, gMap)

			wc.create_new_event(summary, address, desc, date, attendees)



