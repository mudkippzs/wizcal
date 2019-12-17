# WizKids HeroClix Event Calendar to gCalendar

Please feel free to take and adapt to yoru own needs!

## Prerequisites

Enable the Google Calendar API for your Google Account. This generates a 'credentials.json' file; download it and place it in the folder with 'main.py' & 'wizcal.py'.

Then, use [pip](https://pypi.org/project/pip/) to install the required libraries:

`pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`

For full instructions on these steps:
* Follow Step 1 & Step 2 here: [Google Dev - Python Quickstart](https://developers.google.com/calendar/quickstart/python)

## Once you've completed the Prerequisite steps above

$> pip install -r requirements.txt
$> (vi/subl/emacs) user_config.py
[make appropriate edits & save]
$> python main.py

**Note** You may be asked to authenticate your Google Account the first time you use this. It will state this app isn't verified yet, click to proceed and accep the warning. If you're concerned then feel free to inspect the code and ultimately it's your choice to use it.

When you see the message in the browser:

`The authentication flow has completed. You may close this window.`

You can close the tab and then run the python app again in ther command line:

$> python main.py