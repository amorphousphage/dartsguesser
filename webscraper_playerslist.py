from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from models import Game
from config import Config
import re
import time
from datetime import datetime, timedelta

# Function to clean player names (removing brackets with numbers from the names)
def clean_player_name(name):
    # Use regex to remove text within parentheses (and the parentheses themselves)
    return re.sub(r'\s*\([^)]*\)', '', name).strip()

# Set up the database session
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

# Set up the Firefox WebDriver (headless)
options = webdriver.FirefoxOptions()
options.add_argument('--headless') 

# Set up a Webdriver (Selenium converting dynamically generated content into HTML code) for the Match Data
driver = webdriver.Firefox(options=options)
driver.get("https://www.oddsportal.com/darts/world/pdc-world-championship/standings/")

# Wait for the page to load
driver.implicitly_wait(20)

# Extract the html content and parse it
html_content = driver.page_source
soup = BeautifulSoup(html_content, 'html.parser')

# Define all rounds to be played
rounds = ['1/64-finals','1/32-finals','1/16-finals','1/8-finals','Quarter-finals','Semi-finals','Final']

# Find all matches for the rounds using BeautifulSoup
r1_matches = soup.find_all('div', id=lambda x: x and x.startswith('match-0-'))
r2_matches = soup.find_all('div', id=lambda x: x and x.startswith('match-1-'))
r3_matches = soup.find_all('div', id=lambda x: x and x.startswith('match-2-'))
final16_matches = soup.find_all('div', id=lambda x: x and x.startswith('match-3-'))
quarterfinal_matches = soup.find_all('div', id=lambda x: x and x.startswith('match-4-'))
semifinal_matches = soup.find_all('div', id=lambda x: x and x.startswith('match-5-'))
final_match = soup.find_all('div', id=lambda x: x and x.startswith('match-6-'))

# Define a list to store all match data
list_of_all_matches = []
players = []
# Iterate through each match for a round
for match in r1_matches:
    # Extract the 'participant home' span using regex for class
    participant_home = match.find('span', class_=re.compile('.*participant home.*'))
    if participant_home:
        home_name = clean_player_name(participant_home.find('span', class_='name').text.strip())
        if len(home_name) > 0:
            players.append(home_name)
    # Extract the 'participant away' span using regex for class
    participant_away = match.find('span', class_=re.compile('.*participant away.*'))
    if participant_away:
        away_name = clean_player_name(participant_away.find('span', class_='name').text.strip())
        if len(away_name) > 0:
            players.append(away_name)

print(players)
print(len(players))
# Close the driver when done
driver.quit()

