# DartsGuesser
A Flask Website to submit guesses and compete with friends for the yearly PDC Darts World Championship

## Features
- Register a user account to start guessing
- Submit guesses for the winner of each match of the PDC World Championship
- Submit guesses for some overall tournament outcomes (winner, player with most 180s, number of 180s, number of 9-darters and player with the highest checkout)
- Create and join groups to compare your guesses to your friends
- Language Translations: The website is available in English, German, Italian, French, Spanish and Dutch

## Framework
The website uses a mySQL database to store user login credentials (passwords and answers to the security question are hashed), game data, guessing data per user and group data. A selenium webscraper automatically updates game data throughout the tournament.

## Setup
The website is available as a docker compose container. To be able to scrape data for the website, an additional container for selenium/standalone-firefox must be installed as well.
