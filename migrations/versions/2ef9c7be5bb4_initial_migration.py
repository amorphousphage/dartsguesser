"""Initial Migration

Revision ID: 2ef9c7be5bb4
Revises: 
Create Date: 2024-12-02 15:04:44.258978

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2ef9c7be5bb4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('betting_groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('code', sa.String(length=8), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code'),
    sa.UniqueConstraint('name')
    )
    op.create_table('games',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('round_name', sa.String(length=50), nullable=False),
    sa.Column('match_time', sa.String(length=50), nullable=False),
    sa.Column('player_1', sa.String(length=100), nullable=False),
    sa.Column('sets_won_player_1', sa.Integer(), nullable=True),
    sa.Column('player_2', sa.String(length=100), nullable=False),
    sa.Column('sets_won_player_2', sa.Integer(), nullable=True),
    sa.Column('winner', sa.String(length=100), nullable=True),
    sa.Column('odds_player_1', sa.Float(), nullable=True),
    sa.Column('odds_player_2', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('players',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('players', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tournament_guesses_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('guess_type', sa.Enum('winner', 'most_180', 'num_180', 'num_9_darters', 'highest_checkout', name='guess_type_enum'), nullable=False),
    sa.Column('value', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('password', sa.String(length=200), nullable=False),
    sa.Column('security_question', sa.String(length=200), nullable=False),
    sa.Column('security_answer', sa.String(length=200), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('game_guesses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.Integer(), nullable=False),
    sa.Column('predicted_winner', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['game_id'], ['games.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tournament_guesses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('guess_type', sa.Enum('winner', 'most_180', 'num_180', 'num_9_darters', 'highest_checkout', name='guess_type_enum'), nullable=False),
    sa.Column('value', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_betting_groups',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('betting_group_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['betting_group_id'], ['betting_groups.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'betting_group_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_betting_groups')
    op.drop_table('tournament_guesses')
    op.drop_table('game_guesses')
    op.drop_table('users')
    op.drop_table('tournament_guesses_results')
    op.drop_table('players')
    op.drop_table('games')
    op.drop_table('betting_groups')
    # ### end Alembic commands ###