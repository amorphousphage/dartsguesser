from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify, g, Response
from flask_migrate import Migrate
from flask_babel import Babel, gettext as _
from config import Config
from models import db, User, BettingGroup, UserBettingGroup, Game, GameGuess, TournamentGuess, TournamentResults, Player  # Import after initializing db
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests
import os

app = Flask(__name__)
app.config['BABEL_DEFAULT_LOCALE'] = 'en'  # Set default locale to English
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'de', 'it', 'fr', 'es', 'nl']
app.secret_key = os.environ.get("SECRET_KEY")
app.config.from_object(Config)
babel = Babel(app)

# Initialize db first
db.init_app(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

#############################
# Language Selection Routes #
#############################

# Define your languages
LANGUAGES = ['en', 'de', 'it', 'fr', 'es', 'nl']  # Add other languages if needed

# Set up the language selector function
def get_locale():
    """Select the locale/language"""
    locale = session.get('lang', 'en')  # Default to English if no language is selected
    return locale

babel.init_app(app, locale_selector=get_locale)

@app.before_request
def before_request():
    """Load the user's selected language"""
    session.modified = True
    # g.lang will hold the user's language preference for later use in templates
    g.lang = session.get('lang', 'en')

@app.route('/set_language', methods=['POST'])
def set_language():
    """Set the user's language based on the selection"""
    lang = request.form.get('language')
    if lang in LANGUAGES:
        session['lang'] = lang  # Save language choice in the session
    return redirect(request.referrer)  # Redirect to the previous page

##############
# Home Route #
##############

@app.route('/')
def home():
    return render_template('home.html')

##############################
# Routes for user management #
##############################

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        security_question = request.form['security_question']
        security_answer = generate_password_hash(request.form['security_answer'])

        # Check if the username already exists in the database
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            # If the username is taken, show an error message
            flash (_('Username is already taken. Please choose a different one.'), 'error')
            return redirect(url_for('register'))

        # If the username is available, create the new user
        new_user = User(username=username, password=password, security_question=security_question, security_answer=security_answer)
        db.session.add(new_user)
        db.session.commit()

        flash (_('Registration successful! Please log in.'))
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash ( _('Login successful!'))
            return redirect(url_for('dashboard'))
        flash (_('Invalid credentials. Please try again.'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user from session
    flash (_('You have been logged out.'))
    return redirect(url_for('home'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        # Look up the user by their username
        user = User.query.filter_by(username=username).first()

        if not username:
            flash (_('Please enter the username and then click the forgot password link.'))
            return render_template('login.html')

        if user:
            # If user exists, display the security question
            return redirect(url_for('reset_password', username=username))
        else:
            # If user is not found, flash a message
            flash (_('Username not found.'), 'error')

    return render_template('forgot_password.html')

@app.route('/reset-password/<username>', methods=['GET', 'POST'])
def reset_password(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        flash (_('Username not found.'), 'error')
        return redirect(url_for('login'))  # Redirect to login page if no user found

    if request.method == 'POST':
        # Get the submitted answer
        submitted_answer = request.form['security_answer']

        # Compare hashed answer
        if check_password_hash(user.security_answer, submitted_answer):
            # If the answer is correct, allow user to update the password
            new_password = request.form['new_password']
            hashed_password = generate_password_hash(new_password)

            # Update the user's password
            user.password = hashed_password
            db.session.commit()  # Commit the changes to the database

            flash (_('Password successfully updated.'), 'success')
            return redirect(url_for('login'))  # Redirect user to the login page after updating password
        else:
            # If the answer is wrong
            flash (_('Incorrect answer to security question.'), 'error')

    return render_template('reset_password.html', user=user)

##########################################
# Route for the dashboard and explanation#
##########################################

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash (_('Please log in to access the dashboard.'))
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    groups = user.betting_groups
    return render_template('dashboard.html', user=user, groups=groups)

@app.route('/how-it-works')
def how_it_works():
    return render_template('how-it-works.html')

#################################
# Routes for a player's guesses #
#################################

@app.route('/my-guesses')
def my_guesses():
    # Logic to display the user's guesses (you can customize this later)
    return render_template('my-guesses.html', translate_match_time=_('Time of the Match: {} (GMT)'), translate_no_guess=_('No guess'), translate_match_in_progress=('(Match not finished yet)'), translate_tournament_winner=_('Tournament Winner (+ 20 Points)'), translate_most_180s_thrown=_('Player with most 180s thrown (+ 10 Points)'), translate_number_180s_thrown=_('Number of 180s thrown total (+ max. 40 Points (-5 Points for every 10 180s off))'), translate_number_of_9_darters=_('Number of 9-darters thrown (+ 20 Points)'), translate_player_highest_checkout=_('Player with the highest checkout (+ 20 Points)'), translate_zero_points=_('(+ 0 points)'), translate_num180_points=_('({} points off from {} (+{} points))'), translate_guess_missed=_('Guess missed'), translate_odds=_('odds'))

##############################
# Routes for handling groups #
##############################

@app.route('/my-groups')
def my_groups():
    # Assuming you have the user's ID in session or you can get the logged-in user object
    user_id = session.get('user_id')  # Or use current_user.id if using Flask-Login

    if user_id is None:
        return redirect(url_for('login'))  # Redirect to login if no user is logged in

    # Retrieve the user object
    user = User.query.get(user_id)

    # Fetch only the betting groups that the user is assigned to
    groups = BettingGroup.query.join(
        UserBettingGroup
    ).filter(
        UserBettingGroup.user_id == user.id
    ).all()

    return render_template('my-groups.html', groups=groups, translate_confirm_leaving_group=_('Are you sure you want to leave this group?'))

@app.route('/create-group', methods=['GET', 'POST'])
def create_group():
    if request.method == 'POST':
        group_name = request.form['group_name']
        group_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))  # Random 8-character group ID

        # Create a new BettingGroup instance
        new_group = BettingGroup(name=group_name, code=group_id)

        # Save the group to the database
        db.session.add(new_group)
        db.session.commit()

        # Automatically add the user who created the group as a member
        user_id = session.get('user_id')  # Retrieve the logged-in user's ID from the session
        if user_id:
            user_group = UserBettingGroup(user_id=user_id, betting_group_id=new_group.id)
            db.session.add(user_group)
            db.session.commit()  # Commit the membership

        # Redirect to the "my_groups" page after saving
        flash (_("Group created successfully!"), "success")
        return redirect(url_for('my_groups'))  # Redirect to a page where users can see their groups

    return render_template('create-group.html')

@app.route('/join-group', methods=['GET', 'POST'])
def join_group():
    if request.method == 'POST':
        group_id = request.form['group_id']  # Get the group ID from the form

        # Find the group by its unique ID (the 8-character code)
        group = BettingGroup.query.filter_by(code=group_id).first()

        if group:  # If group exists, associate user with the group
            user = User.query.filter_by(id=session.get('user_id')).first()  # Assuming you have a way to get the logged-in user
            if user:
                # Assuming you have a relationship set up between user and betting group
                user.betting_groups.append(group)  # Add the group to the user's list of groups

                # Commit the changes to the database
                db.session.commit()

                flash (_('You have successfully joined the group!'), 'success')
                return redirect(url_for('my_groups'))  # Redirect to the "My Groups" page
            else:
                flash (_('Username not found.'), 'danger')
        else:
            flash (_('Group not found. Please check the group ID and try again.'), 'danger')

    return render_template('join-group.html')

@app.route('/leave_group', methods=['POST'])
def leave_group():
    data = request.json
    group_code = data.get('group_code')

    if not group_code:
        return jsonify({'error': 'No group code provided'}), 400

    # Step 1: Get the betting_group_id from the BettingGroup table using the code
    betting_group = BettingGroup.query.filter_by(code=group_code).first()
    if not betting_group:
        return jsonify({'error': 'Group not found'}), 404

    # Step 2: Find and remove the user's association with this betting group
    user_betting_group = UserBettingGroup.query.filter_by(
        user_id=session.get('user_id'),  # Ensure this is the logged-in user
        betting_group_id=betting_group.id
    ).first()

    if not user_betting_group:
        return jsonify({'error': 'You are not a member of this group'}), 404

    # Step 3: Remove the relationship
    db.session.delete(user_betting_group)
    db.session.commit()

    # Step 4: Check if the group is empty after the user left it
    remaining_users = UserBettingGroup.query.filter_by(betting_group_id=betting_group.id).count()

    if remaining_users == 0:
        # Step 5: Remove the group if it's empty
        db.session.delete(betting_group)
        db.session.commit()

    return jsonify({'success': True}), 200

@app.route('/<group_code>')
def group_page(group_code):
    user_id = session.get('user_id')

    # Obtain the group name
    group_name_data = BettingGroup.query.filter_by(code=group_code).first()
    if group_name_data is not None:
        group_name = group_name_data.name

        return render_template('group_page.html', group_code=group_code, group_name=group_name, logged_in_user_id=user_id, translate_match_time=_('Time of the Match: {} (GMT)'), translate_no_guess=_('No guess'), translate_match_in_progress=('(Match not finished yet)'), translate_category_title=_('Category'), translate_guess_title=_('Guess'), translate_tournament_winner=_('Tournament Winner (+ 20 Points)'), translate_most_180s_thrown=_('Player with most 180s thrown (+ 10 Points)'), translate_number_180s_thrown=_('Number of 180s thrown total (+ max. 40 Points (-5 Points for every 10 180s off))'), translate_number_of_9_darters=_('Number of 9-darters thrown (+ 20 Points)'), translate_player_highest_checkout=_('Player with the highest checkout (+ 20 Points)'), translate_zero_points=_('(+ 0 points)'), translate_num180_points=_('({} points off from {} (+{} points))'), translate_place_title=_('Place'), translate_username_title=_('Username'), translate_points_title=_('Points'), translate_points_180_calc=_('({} points off from {} (+{} points))'), translate_odds=_('odds'))
    else:
        return Response(status=204)

#############################################
# Routes for getting data from the database #
#############################################

@app.route('/get_games', methods=['GET'])
def get_games():
    # Ensure the user is logged in by checking the session    user_id = session.get('user_id')
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401
    round_name = request.args.get('round_name')  # Get the round from the query string

    if round_name:
        # Query games for the selected round
        games = Game.query.filter_by(round_name=round_name).all()
        # Query the guesses for the logged-in user (filter by user_id and game_id)
        game_guesses = GameGuess.query.filter_by(user_id=user_id).filter(GameGuess.game_id.in_([game.id for game in games])).all()

        # Create a dictionary of game guesses with the game_id as key
        game_guesses_dict = {guess.game_id: guess.predicted_winner for guess in game_guesses}

        game_data = []

        # Prepare the games data to send to the frontend
        for game in games:
            game_data.append({
                'game_id': game.id,
                'match_time': game.match_time,
                'player_1': game.player_1,
                'player_2': game.player_2,
                'sets_won_player_1': game.sets_won_player_1,
                'sets_won_player_2': game.sets_won_player_2,
                'winner': game.winner,
                'odds_player_1': game.odds_player_1,
                'odds_player_2': game.odds_player_2,
                'guess': game_guesses_dict.get(game.id, 'No guess')  # Default to 'No guess' if not found
            })

        return jsonify(game_data)

    return jsonify({'error': 'No round selected'}), 400

@app.route('/get_games_for_group', methods=['GET'])
def get_games_for_group():
    # Ensure the user is logged in by checking the session    user_id = session.get('user_id')
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401
    round_name = request.args.get('round_name')  # Get the round from the query string
    group_code = request.args.get('group_code') # Get the group code from the query string

    # Get betting_group_id from group_code
    betting_group = BettingGroup.query.filter_by(code=group_code).first()
    if not betting_group:
        return jsonify({'error': 'Group not found'}), 404
    betting_group_id = betting_group.id

    # Get all user_ids from user_betting_groups table
    user_betting_groups = UserBettingGroup.query.filter_by(betting_group_id=betting_group_id).all()
    if not user_betting_groups:
        return jsonify({'error': 'No users found in this group'}), 404

    user_ids = [ubg.user_id for ubg in user_betting_groups]  # Extract user_ids

    # Get usernames for all users in the betting group
    users = User.query.filter(User.id.in_(user_ids)).all()
    usernames_dict = {user.id: user.username for user in users}

    # Check if a round was specified. Round name "all" is used to obtain all games data for points per group calculation
    if round_name :
        # Query games for the selected round
        if round_name != "all":
            games = Game.query.filter_by(round_name=round_name).all()
        else:
            games = Game.query.all()

        # Query the guesses all users
        game_guesses = GameGuess.query.filter(GameGuess.user_id.in_(user_ids)).filter(GameGuess.game_id.in_([game.id for game in games])).all()

        # Create a dictionary of game guesses with game_id as key
        game_guesses_dict = {}
        for guess in game_guesses:
            if guess.game_id not in game_guesses_dict:
                game_guesses_dict[guess.game_id] = []
            game_guesses_dict[guess.game_id].append({
                'user_id': guess.user_id,
                'predicted_winner': guess.predicted_winner
            })

        game_data = []

        # Prepare the games data to send to the frontend
        for game in games:
            # Get the guesses for the current game
            game_guess = game_guesses_dict.get(game.id, [])

            # Create a list of guesses with user_id and default 'No guess' if no guess exists
            guesses_with_user_name = [
                {
                    'user_id': guess['user_id'],
                    'username': usernames_dict.get(guess['user_id']),
                    'predicted_winner': guess['predicted_winner'] if guess['predicted_winner'] else 'No guess'
                }
                for guess in game_guess
            ]

            # Ensure all users in the group are included in the guesses
            for user_id in user_ids:
                # Check if the user has already submitted a guess for this game
                if not any(guess['username'] == usernames_dict.get(user_id) for guess in guesses_with_user_name):
                    # Add the user with "No guess" if they're missing (have not submitted guesses for the round)
                    guesses_with_user_name.append({
                        'user_id': user_id,
                        'username': usernames_dict.get(user_id),
                        'predicted_winner': 'No guess'
                    })

            # Sort the guesses by username for consistency
            guesses_with_user_name.sort(key=lambda x: x['username'])

            game_data.append({
                'game_id': game.id,
                'match_time': game.match_time,
                'player_1': game.player_1,
                'player_2': game.player_2,
                'sets_won_player_1': game.sets_won_player_1,
                'sets_won_player_2': game.sets_won_player_2,
                'winner': game.winner,
                'odds_player_1': game.odds_player_1,
                'odds_player_2': game.odds_player_2,
                'guesses': guesses_with_user_name  # List of guesses with username and winner guess
            })

        return jsonify(game_data)

    return jsonify({'error': 'No round selected'}), 400

@app.route('/get_players', methods=['GET'])
def get_players():
    # Query all players from the database
    players_list = Player.query.order_by(Player.players.asc()).all()
    # Format the players' names as needed
    formatted_players = [player.players for player in players_list]
    return jsonify(formatted_players)

@app.route('/get_user_tournament_guesses', methods=['GET'])
def get_user_tournament_guesses():
    try:
        user_id = session.get('user_id')  # Get the user ID from session
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        guesses = TournamentGuess.query.filter_by(user_id=user_id).all()

        # Prepare the response in the expected format
        result = [{'guess_type': guess.guess_type, 'value': guess.value} for guess in guesses]
        return jsonify(result)

    except Exception as e:
        print(str(e))
        return jsonify({'error': 'An error occurred'}), 500

@app.route('/get_user_tournament_guesses_for_group', methods=['GET'])
def get_user_tournament_guesses_for_group():

    user_id = session.get('user_id')  # Get the user ID from session
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401

    group_code = request.args.get('group_code') # Get the group code from the query string

    # Get betting_group_id from group_code
    betting_group = BettingGroup.query.filter_by(code=group_code).first()
    if not betting_group:
        return jsonify({'error': 'Group not found'}), 404
    betting_group_id = betting_group.id

    # Get all user_ids from user_betting_groups table
    user_betting_groups = UserBettingGroup.query.filter_by(betting_group_id=betting_group_id).all()
    if not user_betting_groups:
        return jsonify({'error': 'No users found in this group'}), 404

    user_ids = [ubg.user_id for ubg in user_betting_groups]  # Extract user_ids

    # Get usernames for all users in the betting group
    users = User.query.filter(User.id.in_(user_ids)).all()
    usernames_dict = {user.id: user.username for user in users}

    tournament_guesses = TournamentGuess.query.filter(TournamentGuess.user_id.in_(user_ids)).all()

    # Prepare the response in the expected format
    tournament_guesses_list = [{'user_id': guess.user_id, 'username': usernames_dict.get(guess.user_id), 'guess_type': guess.guess_type, 'value': guess.value} for guess in tournament_guesses]

    # Ensure all users in the group are included in the guesses
    for user_id in user_ids:
        for guess_type in ['winner', 'most_180', 'num_180', 'num_9_darters', 'highest_checkout']:
            # Check if the user has already submitted a guess for this game
            if not any(guess['username'] == usernames_dict.get(user_id) and guess['guess_type'] == guess_type for guess in tournament_guesses_list):
                # Add the user with "No guess" if they're missing (have not submitted guesses for the round)
                tournament_guesses_list.append({
                    'user_id': user_id,
                    'username': usernames_dict.get(user_id),
                    'guess_type': guess_type,
                    'value': 'No guess'
                })

    # Sort the guesses by username for consistency
    tournament_guesses_list.sort(key=lambda x: x['username'])
    return jsonify(tournament_guesses_list)

@app.route('/get_tournament_guesses_results', methods=['GET'])
def get_tournament_guesses_results():
    user_id = session.get('user_id')  # Get the user ID from session
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401

        # Fetch all results for tournament guesses
    tournament_results = TournamentResults.query.all()

    # Prepare the response in the expected format
    overall_tournament_results = [{'guess_type': result.guess_type, 'value': result.value} for result in tournament_results]

    return jsonify(overall_tournament_results)

@app.route('/get_all_match_times')
def get_all_match_times():
    # Get all match times from the database in the format dd.mm hh:mm
    match_times = [match_time[0] for match_time in Game.query.with_entities(Game.match_time).all()]

    return jsonify({'match_times': match_times})

@app.route('/get_points', methods=['GET'])
def get_points():
    # Define point values as variables
    POINTS_WINNER = 20
    POINTS_MOST_180 = 10
    POINTS_NUM_180 = 40
    POINTS_NUM_9_DARTERS = 20
    POINTS_HIGHEST_CHECKOUT = 20
    POINTS_DEDUCTION_PER_10_OFF = 5
    #POINTS_GAME = 5

    current_user_id = session.get('user_id')

    # Get the user_id from the query string or default to the logged-in user
    current_user_id = request.args.get('user_id')
    if current_user_id is None:  # No `user_id` provided, fall back to the session's user
        current_user_id = session.get('user_id')
        if not current_user_id:
            return jsonify({'error': 'User not authenticated'}), 401  # No logged-in user


    # Fetch all results for tournament guesses
    tournament_results = TournamentResults.query.all()
    # Fetch user's tournament guesses
    user_guesses = TournamentGuess.query.filter_by(user_id=current_user_id).all()

    # Map user guesses for easy lookup
    user_guesses_dict = {guess.guess_type: guess.value for guess in user_guesses}

    points = 0

    for result in tournament_results:
        if result.value is not None:  # Only calculate if a result is set
            guess_type = result.guess_type
            result_value = result.value
            user_value = user_guesses_dict.get(guess_type)

            # Add to max points if a result exists
            if guess_type == 'winner' and user_value == result_value:
                points += POINTS_WINNER

            elif guess_type == 'most_180' and user_value == result_value:
                points += POINTS_MOST_180

            elif guess_type == 'num_180' and user_value is not None:
                try:
                    user_value = int(user_value)
                    result_value = int(result_value)
                    difference = abs(user_value - result_value)
                    deduction = (difference // 10) * POINTS_DEDUCTION_PER_10_OFF
                    earned_points = max(0, POINTS_NUM_180 - deduction)
                    points += earned_points
                except ValueError:
                    # Handle invalid numeric conversion
                    pass  # No points awarded for invalid guess

            elif guess_type == 'num_9_darters' and user_value == result_value:
                points += POINTS_NUM_9_DARTERS

            elif guess_type == 'highest_checkout' and user_value == result_value:
                points += POINTS_HIGHEST_CHECKOUT

    # Calculate match points as before
    games = Game.query.filter(Game.winner.isnot(None), Game.winner != "Game not finished").all()
    game_ids_and_winners = {}
    for game in games:
        # Determine the winner and the corresponding odds
        if game.winner == game.player_1:
            winning_odds = game.odds_player_1
        elif game.winner == game.player_2:
            winning_odds = game.odds_player_2
        else:
            winning_odds = None  # In case there's some inconsistency, although you filtered for valid winners

        # Add the game id, winner, and odds for the winner
        game_ids_and_winners[game.id] = {
            'winner': game.winner,
            'odds': winning_odds
        }

    # User's guesses for these games
    user_game_guesses = GameGuess.query.filter(
        GameGuess.user_id == current_user_id,
        GameGuess.game_id.in_(game_ids_and_winners.keys())
    ).all()

    # Calculate correct guesses and sum the winning odds for correct predictions
    total_odds = 0

    for guess in user_game_guesses:
        # Check if the predicted winner matches the actual winner
        if game_ids_and_winners.get(guess.game_id)['winner'] == guess.predicted_winner:
            # Add the odds for the correct guess
            total_odds += game_ids_and_winners.get(guess.game_id)['odds']

    # Add match points to totals
    points += total_odds

    return jsonify({
        'points': round(points,3),
        'error': False
    })

@app.route('/get_points_per_group', methods=['GET'])
def get_points_per_group():
    group_code = request.args.get('group_code')
    if not group_code:
        return jsonify({'error': 'Group code is required'}), 400

    # Get betting_group_id from group_code
    betting_group = BettingGroup.query.filter_by(code=group_code).first()
    if not betting_group:
        return jsonify({'error': 'Group not found'}), 404
    betting_group_id = betting_group.id

    # Get all user_ids from user_betting_groups table
    user_betting_groups = UserBettingGroup.query.filter_by(betting_group_id=betting_group_id).all()
    if not user_betting_groups:
        return jsonify({'error': 'No users found in this group'}), 404

    user_ids = [ubg.user_id for ubg in user_betting_groups]  # Extract user_ids

    # Get usernames for all users in the betting group
    users = User.query.filter(User.id.in_(user_ids)).all()
    usernames_dict = {user.id: user.username for user in users}

    # Collect points for each member
    leaderboard = []
    for user in users:

        response = requests.get(f'http://localhost:5000/get_points?user_id={user.id}')
        if response.status_code == 200:
            data = response.json()
            leaderboard.append({'username': user.username, 'points': data['points']})

    # Sort leaderboard by points (descending)
    leaderboard = sorted(leaderboard, key=lambda x: x['points'], reverse=True)

    return jsonify(leaderboard)

##########################################
# Routes for saving data to the database #
##########################################

@app.route('/save_guesses', methods=['POST'])
def save_guesses():
    user_id = session.get('user_id')  # Get the user ID from the session
    game_ids = request.form.getlist('game_ids[]')  # Get the list of game_ids
    guesses = request.form.getlist('guesses[]')  # Get the list of guesses

    # Iterate through the games and their corresponding guesses
    for game_id, guess in zip(game_ids, guesses):
        # Check if the user already has a guess for this game_id
        existing_guess = GameGuess.query.filter_by(user_id=user_id, game_id=game_id).first()

        if existing_guess:
            # Update the existing guess
            existing_guess.predicted_winner = guess
            db.session.commit()
        else:
            # Create a new guess
            new_guess = GameGuess(user_id=user_id, game_id=game_id, predicted_winner=guess)
            db.session.add(new_guess)
            db.session.commit()

    return jsonify({"message": _("Guesses saved successfully!")})

@app.route('/save_tournament_guesses', methods=['POST'])
def save_tournament_guesses():
    try:
        user_id = session.get('user_id')  # Assuming user ID is stored in session
        guesses = request.form.getlist('guesses[]')  # List of guesses
        guess_types = request.form.getlist('guess_types[]')  # List of guess types

        # Loop through the guesses and save or update each guess
        for guess, guess_type in zip(guesses, guess_types):
            # Check if the guess for this user_id and guess_type already exists
            existing_guess = TournamentGuess.query.filter_by(user_id=user_id, guess_type=guess_type).first()

            if existing_guess:
                # If the guess already exists, update it
                existing_guess.value = guess
            else:
                # If the guess does not exist, create a new entry
                tournament_guess = TournamentGuess(
                    user_id=user_id,
                    guess_type=guess_type,
                    value=guess
                )
                db.session.add(tournament_guess)

        db.session.commit()  # Commit the transaction

        return jsonify({"message": _("Overall Tournament Guesses saved successfully!")})

    except Exception as e:
        db.session.rollback()  # Rollback in case of error
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
