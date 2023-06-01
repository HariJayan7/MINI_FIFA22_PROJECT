import sqlite3
from random import randint
from flask import session
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


@app.route('/', methods=('GET', 'POST'))
def home_page():
    return render_template('home_page.html')


@app.route('/match_list', methods=('GET', 'POST'))
def match_list():
    conn = get_db_connection()
    match_details = conn.execute('SELECT * FROM Matches').fetchall()
    conn.close()
    return render_template('match_list.html', match_details=match_details)


@app.route('/login_admin', methods=('GET', 'POST'))
def login_admin():
    if request.method == 'POST':
        username = request.form['Username']
        password_entered = request.form['Password']
        conn = get_db_connection()
        passcode = conn.execute(
            'SELECT Password FROM Login_admins WHERE Username=?', (username,)).fetchone()
        conn.close()
        if passcode == None:
            flash('Entered username does not exist for admin!!!')
            return redirect(url_for('login_admin'))

        if passcode[0] == password_entered:
            return redirect(url_for('admin_dashboard', username=username))
        else:
            flash('Wrong Password')
            return redirect(url_for('login_admin'))

    return render_template('login_admin.html')


@app.route('/login_player', methods=('GET', 'POST'))
def login_player():
    if request.method == 'POST':
        username = request.form['Username']
        password_entered = request.form['Password']
        conn = get_db_connection()
        passcode = conn.execute(
            'SELECT Password FROM Login_players WHERE Username=?', (username,)).fetchone()
        conn.close()
        if passcode == None:
            flash('Entered username does not exist for player!!!')
            return redirect(url_for('login_player'))

        if passcode[0] == password_entered:
            return redirect(url_for('player_dashboard', username=username))
        else:
            flash('Wrong Password')
            return redirect(url_for('login_player'))

    return render_template('login_player.html')


@app.route('/<username>/admin_dashboard', methods=('GET', 'POST'))
def admin_dashboard(username):
    if request.method == 'POST':
        if request.form['submit_button'] == 'Start New Game':
            return redirect(url_for('create_game', username=username))
        elif request.form['submit_button'] == 'Add Player':
            return redirect(url_for('add_player', username=username))
        elif request.form['submit_button'] == 'Remove Player':
            return redirect(url_for('remove_player', username=username))
        elif request.form['submit_button'] == 'Edit Match Details':
            pass

        return redirect(url_for('admin_dashboard', username=username))

    conn = get_db_connection()
    admin_details = conn.execute(
        'SELECT * FROM Admins WHERE Admin_id=?', (username,)).fetchone()
    player_details = conn.execute('SELECT * FROM Players').fetchall()
    match_details = conn.execute('SELECT * FROM Matches').fetchall()
    return render_template('admin_dashboard.html', admin_details=admin_details, player_details=player_details, match_details=match_details)


@app.route('/<username>/player_dashboard', methods=('GET', 'POST'))
def player_dashboard(username):
    conn = get_db_connection()
    player_details = conn.execute(
        'SELECT * FROM Players WHERE Player_id=?', (username,)).fetchone()
    match_details = conn.execute('SELECT * FROM Matches WHERE Player1_name=? OR Player2_name=?',
                                 (player_details[1], player_details[1])).fetchall()
    wins, draws, losses = 0, 0, 0
    for row in match_details:
        if row[5] > row[6] and row[1] == player_details[1]:
            wins += 1
        elif row[5] < row[6] and row[2] == player_details[1]:
            wins += 1
        elif row[5] == row[6]:
            draws += 1
        else:
            losses += 1
    return render_template('player_dashboard.html', player_details=player_details, match_details=match_details, wins=wins, draws=draws, losses=losses)


@app.route('/<username>/create_game', methods=('GET', 'POST'))
def create_game(username):
    conn = get_db_connection()
    player_names = conn.execute('SELECT Player_name FROM Players').fetchall()
    player_names = [i[0] for i in player_names]
    teams = conn.execute('SELECT Team_name FROM Teams').fetchall()
    teams = [i[0] for i in teams]
    if request.method == 'POST':
        player1_name = request.form['Player1_name']
        player1_team = request.form['Player1_team']
        player1_score = request.form['Player1_score']

        player2_name = request.form['Player2_name']
        player2_team = request.form['Player2_team']
        player2_score = request.form['Player2_score']

        if player1_name == player2_name:
            flash('Player 1 and Player 2 cannot be the same!!!')
            return redirect(url_for('create_game', username=username))
        conn = get_db_connection()
        conn.execute('INSERT INTO Matches (Player1_name,Player2_name,Player1_team,Player2_team,Player1_score,Player2_score) VALUES (?,?,?,?,?,?)',
                     (player1_name, player2_name, player1_team, player2_team, player1_score, player2_score))
        conn.commit()
        conn.close()
        flash('Match created successfully')
        return redirect(url_for('admin_dashboard', username=username))
    return render_template('create_game.html', username=username, player_names=player_names, teams=teams)


@app.route('/<username>/add_player', methods=('GET', 'POST'))
def add_player(username):
    if request.method == 'POST':
        player_id = request.form['Player_id']
        player_name = request.form['Player_name']
        password = request.form['Password']
        repeat_password = request.form['Repeat_password']

        conn = get_db_connection()
        Player_ids = conn.execute('SELECT Player_id FROM Players').fetchall()
        Player_ids = [i[0] for i in Player_ids]
        conn.close()
        if player_id in Player_ids:
            flash('Player ID already exists!!!')
            return redirect(url_for('add_player', username=username))

        if password != repeat_password:
            flash('Passwords do not match!!!')
            return redirect(url_for('add_player', username=username))

        conn = get_db_connection()
        conn.execute('INSERT INTO Players (Player_id,Player_name) VALUES (?,?)',
                     (player_id, player_name))
        conn.execute('INSERT INTO Login_players (Username,Password) VALUES (?,?)',
                     (player_id, password))
        conn.commit()
        conn.close()
        flash('Player added successfully')
        return redirect(url_for('admin_dashboard', username=username))
    return render_template('add_player.html', username=username)


@app.route('/<username>/remove_player', methods=('GET', 'POST'))
def remove_player(username):
    conn = get_db_connection()
    players = conn.execute('SELECT * FROM Players').fetchall()
    player_ids = conn.execute('SELECT Player_id FROM Players').fetchall()
    player_ids = [i[0] for i in player_ids]
    conn.close()
    if request.method == 'POST':
        player_id = request.form['Player_id']
        if player_id not in player_ids:
            flash('Player ID does not exist!!!')
            return redirect(url_for('remove_player', username=username))

        conn = get_db_connection()
        conn.execute('DELETE FROM Players WHERE Player_id=?', (player_id,))
        conn.execute('DELETE FROM Login_players WHERE Username=?',
                     (player_id,))
        conn.commit()
        conn.close()
        flash('Player removed successfully')
        return redirect(url_for('admin_dashboard', username=username))
    return render_template('remove_player.html', username=username, players=players)


@app.route('/leaderboard', methods=('GET', 'POST'))
def leaderboard():
    conn = get_db_connection()
    player_details = conn.execute('SELECT * FROM Players').fetchall()
    match_details = conn.execute('SELECT * FROM Matches').fetchall()
    conn.close()
    players = {}
    for row in player_details:
        player_id = row[0]
        player_name = row[1]
        players[player_id] = {
            'Player_name': player_name,
            'Total_score': 0,
            'Matches_played': 0,
            'Matches_won': 0,
            'Matches_lost': 0,
            'Matches_drawn': 0,
            'Total_goals_scored': 0,
            'Total_goals_conceded': 0
        }

    for player in player_details:
        wins, draws, losses, scored, conceded = 0, 0, 0, 0, 0
        for row in match_details:
            if row[1] == player[1]:
                scored += row[5]
                conceded += row[6]
            elif row[2] == player[1]:
                scored += row[6]
                conceded += row[5]

            if row[5] > row[6] and row[1] == player[1]:
                wins += 1
            elif row[5] < row[6] and row[2] == player[1]:
                wins += 1
            elif row[5] == row[6] and (row[1] == player[1] or row[2] == player[1]):
                draws += 1
            elif row[5] > row[6] and row[2] == player[1] or row[5] < row[6] and row[1] == player[1]:
                losses += 1
        score = wins*3 + draws
        players[player[0]]['Matches_played'] = wins + draws + losses
        players[player[0]]['Matches_won'] = wins
        players[player[0]]['Matches_lost'] = losses
        players[player[0]]['Matches_drawn'] = draws
        players[player[0]]['Total_goals_scored'] = scored
        players[player[0]]['Total_goals_conceded'] = conceded
        players[player[0]]['Total_score'] = score
    # my_dict = {
    #     'player1': {'score': 10, 'wins': 2, 'losses': 1},
    #     'player2': {'score': 20, 'wins': 3, 'losses': 0},
    #     'player3': {'score': 15, 'wins': 1, 'losses': 2}
    # }

    # Sort the dictionary by the 'score' attribute of the inner dictionaries
    sorted_list = dict(
        sorted(players.items(), key=lambda x: x[1]['Total_score'], reverse=True))
    # print(sorted_list)
    return render_template('leaderboard.html', players=sorted_list)


@app.route('/search', methods=('GET', 'POST'))
def search():
    conn = get_db_connection()
    player_names = conn.execute(
        'SELECT Player_name FROM Players').fetchall()
    player_names = [i[0] for i in player_names]
    conn.close()
    if request.method == 'POST':
        player1_name = request.form['Player1_name']
        player2_name = request.form['Player2_name']
        if player1_name == player2_name:
            flash('Player names cannot be same')
            return redirect(url_for('search'))

        conn = get_db_connection()
        player_names = conn.execute(
            'SELECT Player_name FROM Players').fetchall()
        player_names = [i[0] for i in player_names]
        match_details = conn.execute(
            'SELECT * FROM Matches WHERE Player1_name=? and Player2_name=? or Player1_name=? and Player2_name=?', (player1_name, player2_name, player2_name, player1_name)).fetchall()
        conn.close()
        if len(match_details) == 0:
            flash('No matches found')
            return redirect(url_for('search'))
        return render_template('search.html', player_names=player_names, match_details=match_details)
    return render_template('search.html', player_names=player_names, match_details=[])


if __name__ == "__main__":
    app.run(debug=True, port=5001)
