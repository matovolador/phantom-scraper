# Scraper

## Installation

This script uses Python3.6.8 64-bit

Since this is a fresh "server" machine, we need to install firefox for selenium to work:

```bash
sudo apt-get install firefox -y
```

Another requirement is the Geckodriver for Selenium.
Download [here](https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz) and unzip it into project root folder.
Command to download and extract on ubuntu:

```bash
wget -c https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz -O - | tar -xz -C ./
```

Module requirements are inside the `requirements.txt` file.
So for installation with pip you would use

```bash
pip install -r requirements.txt
```
The modules include all necesary libraries.

After doing the above, the only thing that is required for this to execute is the `calendar_scraper.py` script, and `instrument_scraper.py` to scrape instruments page.

For automatic scraping, you would need to set up a crontab job like this:

```bash
@hourly /path/to/project/root/run_calendar_scraper.sh
@hourly /path/to/project/root/run_instrument_scraper.sh
```

These use bash scripts to mount the virtualenv and run the python script.

### Regarding the instrument scraper

The instrument scraper script uses a csv file as input called "instruments.csv". This file needs to be placed at project root.
The contents should be in the following format:
```csv
Code,Name
XAU,Gold
```
Where the "Code" must be the name of the instrument for web navigation. Target ulr /CODE  (the script will conver it to upper case automatically). 
"Name" must be the name desired for displaying in the json output (which will also include the Code)
IT IS VERY IMPORTANT THAT THE FIRST LINE OF THE CSV FILE CONTAINS THE HEADER OF THE TABLE SINCE IT WILL BE IGNORED BY THE SCRAPER WHEN READING THE INPUT OF THE FILE.

You can upload the instruments.csv file with the script under `_extra/upload_instrument_input.sh` (linux type systems). The csv file must be placed inside that folder, and the script needs to be executed from that folder also.

If you are using WINDOWS, get [putty](https://putty.org/) and configure the protocol to SCP. Please remember that the location of the remote target must be /var/www/flask_app/flask_app   and the file name must be instruments.csv

## Automation

Both scrapers are set to be executed with `crontab` as follows:
```bash
0 * * * * /var/www/flask_app/flask_app/run_instrument_scraper.sh
30 * * * * /var/www/flask_app/flask_app/run_scraper.sh
```
That means the instrument scraper will execute at 0 minutes on each hour of the day.
And the economic calendar scraper will execute at 30 minutes on each hour of the day.

## Flask app

Flask app is setup to be placed on /var/www/flask_app/flask_app
It will use virtualenv so that needs to be taken into consideration when creating the .wsgi file
Also I've made it to use apache2.

The flask app itself is the `__init__.py` file at the project root.

### Hitting the flask endpoint

Basically there is 1 route to get the files which is domain.com/files/< filename >

In case of the json files there are 2 file names:
    
    data_calendar.json (calendar data, includes last 7 days, today, and next 7 days)
    data_instruments.json (instrument data)

So it would end up being a GET request with this route for example: https://domain.com/files/data_calendar.json

I've set it up so it returns a json message when the file isnt found.

### Errors

Also, in case of calendar scraping errors, they are logged into "errors_calendar.txt" which can also be found like this: domain.com/files/errors.txt
The Instrument Scraper uses another error file called "errors_instruments.txt", found under the same path domain.com/files/errors_instruments.txt
If there are errors in the last execution, you can check it (rapidly) by hitting /health
If the json output contains "errors":1 , it means there was an error, which would be stored in errors.txt. Else, if "errors":0, there were no errors in the scraper execution.

### Cross Origin Requests

The flask app has been set to accept all incoming cross origin requests. If you want to set a particular origin (lock it to the front end domain), you can edit the following:

Remove the line containing (or comment it out):
```python
CORS(app)
```
And replace it with (or uncomment this line):
```python
cors = CORS(app, resources={r"/*": {"origins": "*"}})
```
by changing "origins":"*" for a list of origins. Like:
```python
cors = CORS(app, resources={r"/*": {"origins":["domain-one.com", "domain-extra.org"]})
 ```
Documentation about flask Cors can be found [here](https://pypi.org/project/Flask-Cors/)