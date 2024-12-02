from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Association table for many-to-many relationship between Users and BettingGroups
class UserBettingGroup(db.Model):
    __tablename__ = 'user_betting_groups'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    betting_group_id = db.Column(db.Integer, db.ForeignKey('betting_groups.id'), primary_key=True)

    user = db.relationship('User', backref='user_betting_groups')
    betting_group = db.relationship('BettingGroup', backref='user_betting_groups')

    def __repr__(self):
        return f'<UserBettingGroup User={self.user_id} Group={self.betting_group_id}>'

# User model
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    security_question = db.Column(db.String(200), nullable=False)
    security_answer = db.Column(db.String(200), nullable=False)


    # Many-to-many relationship to BettingGroup through the association table
    betting_groups = db.relationship('BettingGroup', secondary='user_betting_groups', overlaps="betting_group,user_betting_groups,user")

    # Relationship to GameGuess
    game_guesses = db.relationship('GameGuess', back_populates='user')

    # Relationship to TournamentGuess
    tournament_guesses = db.relationship('TournamentGuess', back_populates='user')

    def __repr__(self):
        return f'<User {self.username}>'

# BettingGroup model
class BettingGroup(db.Model):
    __tablename__ = 'betting_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(8), unique=True, nullable=False)

    # Relationship to User through association table
    members = db.relationship('User', secondary='user_betting_groups', overlaps="betting_group,user_betting_groups,user,betting_groups")

    def __repr__(self):
        return f'<BettingGroup {self.name}>'

# Game model
class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    round_name = db.Column(db.String(50), nullable=False)  # Example: "Quarter-finals"
    match_time = db.Column(db.String(50), nullable=False)  # Match date/time
    player_1 = db.Column(db.String(100), nullable=False)  # Name of the first player
    sets_won_player_1 = db.Column(db.Integer, nullable=True)  # Number of sets won by Player 1
    player_2 = db.Column(db.String(100), nullable=False)  # Name of the second player
    sets_won_player_2 = db.Column(db.Integer, nullable=True)  # Number of sets won by Player 2
    winner = db.Column(db.String(100), nullable=True)  # Nullable if the match isn't completed yet
    odds_player_1 = db.Column(db.Float, nullable=True) # Odds for winning of player 1
    odds_player_2 = db.Column(db.Float, nullable=True) # Odds for winning of player 2

    # Relationship to GameGuess
    game_guesses = db.relationship('GameGuess', back_populates='game')

    def __repr__(self):
        return (f'<Game {self.round_name}: {self.player_1} ({self.sets_won_player_1}) vs '
                f'{self.player_2} ({self.sets_won_player_2})>')

# GameGuess model
class GameGuess(db.Model):
    __tablename__ = 'game_guesses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    predicted_winner = db.Column(db.String(100), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='game_guesses')
    game = db.relationship('Game', back_populates='game_guesses')

    def __repr__(self):
        return f'<GameGuess User={self.user_id} Game={self.game_id} Winner={self.predicted_winner}>'

# TournamentGuess model
class TournamentGuess(db.Model):
    __tablename__ = 'tournament_guesses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    guess_type = db.Column(db.Enum('winner', 'most_180', 'num_180', 'num_9_darters', 'highest_checkout', name='guess_type_enum'), nullable=False)
    value = db.Column(db.String(100), nullable=False)

    # Relationship to User
    user = db.relationship('User', back_populates='tournament_guesses')

    def __repr__(self):
        return f'<TournamentGuess User={self.user_id} Type={self.guess_type} Value={self.value}>'

# Results for TournamentGuess model
class TournamentResults(db.Model):
    __tablename__ = 'tournament_guesses_results'

    id = db.Column(db.Integer, primary_key=True)
    guess_type = db.Column(db.Enum('winner', 'most_180', 'num_180', 'num_9_darters', 'highest_checkout', name='guess_type_enum'), nullable=False)
    value = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<TournamentGuessResults Type={self.guess_type} Value={self.value}>'

class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    players = db.Column(db.String(100))
