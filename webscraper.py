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

# Helper function to convert scores
def parse_score(score):
    return int(score) if score.isdigit() else None

# Set up the database session
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

# Set up the Chrome WebDriver (headless)
options = webdriver.FirefoxOptions()
options.add_argument('--headless')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors=yes')
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--no-sandbox')

# Set up a Webdriver (Selenium converting dynamically generated content into HTML code) for the Match Data
driver = webdriver.Remote(command_executor='http://192.168.178.97:4444/wd/hub',options=options)
driver.get("https://www.oddsportal.com/darts/world/pdc-world-championship/standings/")

# Wait for the page to load
driver.implicitly_wait(50)
# Scroll to the end of the page to make sure all content is loaded
#driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#time.sleep(30)  # Wait for content to load

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

# Loop through all rounds of matches
for round_matches in [r1_matches, r2_matches, r3_matches, final16_matches, quarterfinal_matches, semifinal_matches, final_match]:

    # Define the correct round name
    if round_matches == r1_matches:
        tournament_round = '1/64-finals'
    elif round_matches == r2_matches:
        tournament_round = '1/32-finals'
    elif round_matches == r3_matches:
        tournament_round = '1/16-finals'
    elif round_matches == final16_matches:
        tournament_round = '1/8-finals'
    elif round_matches == quarterfinal_matches:
        tournament_round = 'Quarter-finals'
    elif round_matches == semifinal_matches:
        tournament_round = 'Semi-finals'
    elif round_matches == final_match:
        tournament_round = 'Final'
    else:
        tournament_round = None

    # Iterate through each match for a round
    for match in round_matches:
        # Extract the 'participant home' span using regex for class
        participant_home = match.find('span', class_=re.compile('.*participant home.*'))
        home_name = clean_player_name(participant_home.find('span', class_='name').text.strip())
        home_score = parse_score(participant_home.find('span', class_='score').text.strip())

        # Extract the 'participant away' span using regex for class
        participant_away = match.find('span', class_=re.compile('.*participant away.*'))
        away_name = clean_player_name(participant_away.find('span', class_='name').text.strip())
        away_score = parse_score(participant_away.find('span', class_='score').text.strip())

        # Determine the winner by checking if the 'winner' class is present
        home_winner = 'winner' in participant_home.get('class', [])
        away_winner = 'winner' in participant_away.get('class', [])

        if home_winner:
            winner = home_name
        elif away_winner:
            winner = away_name
        else:
            winner = "Game not finished"

        # If a scraped match has two participants, it is a valid match and should be added to the list
        if home_name and away_name:
            list_of_all_matches.append({'round_name': tournament_round, 'player_1': home_name, 'sets_won_player_1': home_score, 'player_2': away_name, 'sets_won_player_2': away_score, 'winner': winner})

# Close the driver when done
driver.quit()

# Wait for a brief moment to make sure the session is fully closed
time.sleep(2)

# Set up a Webdriver (Selenium converting dynamically generated content into HTML code) for the Match Data
driver = webdriver.Remote(command_executor='http://192.168.178.97:4444/wd/hub',options=options)
driver.get("https://www.oddsportal.com/darts/world/pdc-world-championship/")

# Scroll to the end of the page to make sure all content is loaded
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(30)  # Wait for content to load

# Extract the html content and parse it
html_content = driver.page_source
soup = BeautifulSoup(html_content, 'html.parser')

# Find all matches, which have odds already
matches = soup.find_all('div', class_=re.compile('.*eventRow.*'))
match_dates_divs = soup.find_all('div', class_='text-black-main font-main w-full truncate text-xs font-normal leading-5')
match_dates = []
for match_date in match_dates_divs:
    match_date_text = match_date.text.strip()
    match_dates.append(match_date_text)

# Initialize a variable to track the current match date
match_date_index = 0
current_match_date = match_dates[match_date_index]
# Initialize a list to store match data
odds_data = []
previous_match_time = datetime.strptime('00:00','%H:%M')
# Loop over each match
for match in matches:
    # Get the player names from the <a> tags with 'title' attribute
    players = match.find_all('p', class_='participant-name truncate')
    player_names = [player.text.strip() for player in players]

    # Get the odds values from <p> tags with class containing 'default-odds'
    odds_elements = match.find_all('p', class_=re.compile('.*default-odds.*'))
    odds = [float(odd.get_text(strip=True)) for odd in odds_elements if odd.get_text(strip=True).replace('.', '', 1).isdigit()]
    # Get the Match Time
    time_div = match.find('div', class_='flex w-full')

    if time_div:
        # Inside this div, find the <p> tag containing the time
        time_tag = time_div.find('p')
        if time_tag:
            # Obtain the time
            match_time = datetime.strptime(time_tag.get_text(strip=True),'%H:%M')

    # Switch the match date to the next date if the time of the current match is before the one from the previous match
    if match_time < previous_match_time:
        # Take the next date index
        match_date_index += 1
        # Ensure that the match_date_index doesn't go out of bounds
        if match_date_index <= len(match_dates):
            current_match_date = match_dates[match_date_index]
    
    # Set the current match time to be the previous one
    previous_match_time = match_time
    match_date = datetime.strptime(str(current_match_date), '%d %b %Y')
    
    # Concatenate date and time
    date = datetime.combine(match_date, match_time.time())
    date = date.strftime('%Y-%m-%d %H:%M')

    # Ensure we only have two odds (one for each player)
    if len(odds) == 2:
        odds_data.append({
            'date': date,
            'player1': player_names[0],
            'player2': player_names[1],
            'odds_player1': odds[0],
            'odds_player2': odds[1]
        })
print(odds_data)
# Quit the webscraping
driver.quit()

# Loop through all matches and odds data and combine the lists
for match in list_of_all_matches:
    # Extract player names for the match
    player_1_name = match['player_1']
    player_2_name = match['player_2']

    # Find the corresponding odds for this match
    for odds in odds_data:
        if (odds['player1'] == player_1_name and odds['player2'] == player_2_name) or \
           (odds['player1'] == player_2_name and odds['player2'] == player_1_name):
            # If there's a match, add the odds to the match dictionary
            match['odds_player_1'] = odds['odds_player1']
            match['odds_player_2'] = odds['odds_player2']
            match['match_time'] = odds['date']
            break  # No need to check further odds once a match is found

# Sort the list by match_time (ascending order)
list_of_all_matches.sort(key=lambda x: x["match_time"])

# Update the data into the games table
for game_data in list_of_all_matches:
    round_name, player_1, sets_won_player_1, player_2, sets_won_player_2, winner, odds_player_1, odds_player_2, match_time = game_data
    
    # Check if a game with the same round_name and players already exists, considering interchangeable players
    existing_game = session.query(Game).filter(
        ((Game.round_name == game_data['round_name']) &
         ((Game.player_1 == game_data['player_1']) & (Game.player_2 == game_data['player_2'])) |
         ((Game.player_1 == game_data['player_2']) & (Game.player_2 == game_data['player_1'])))
    ).first()

    if existing_game:
        # If the game exists, update the record
        existing_game.match_time = game_data['match_time']
        existing_game.sets_won_player_1 = game_data['sets_won_player_1']
        existing_game.sets_won_player_2 = game_data['sets_won_player_2']
        existing_game.winner = game_data['winner']
        existing_game.odds_player_1 = game_data['odds_player_1']
        existing_game.odds_player_2 = game_data['odds_player_2']
    else:
        # If the game doesn't exist, create a new game
        new_game = Game(
            round_name=game_data['round_name'],
            match_time=game_data['match_time'],
            player_1=game_data['player_1'],
            player_2=game_data['player_2'],
            sets_won_player_1=game_data['sets_won_player_1'],
            sets_won_player_2=game_data['sets_won_player_2'],
            winner=game_data['winner'],
            odds_player_1 =game_data['odds_player_1'],
            odds_player_2 =game_data['odds_player_2']
        )
        session.add(new_game)

    # Commit the changes after each game (optional, you can commit once after all games)
    session.commit()

