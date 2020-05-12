from __future__ import unicode_literals

from flask import Flask, render_template, request, session, url_for, redirect
from flask_session import Session
# from flask_assets import Environment, Bundle

from game import Game

# http://clouddatafacts.com/heroku/heroku-flask-redis/flask_redis.html#pre-rerequisites 
# https://hackersandslackers.com/redis-py-python/

app = Flask(__name__, instance_relative_config=False)
app.config.from_object('config.Config')

Session(app)

'''
assets = Environment(app)

js_bundle = Bundle('src/js/main.js',
                   filters='jsmin',
                   output='dist/js/main.min.js')
assets.register('main_js', js_bundle)
js_bundle.build()
'''

action_labels = {
    'start': 'Start',
    'stop': 'Stop',
    'start_new': 'Start'
}


# TODO
# use hashes to record each games "last" things: last card, last team. though session might make more sense
# reorg with application context and all that
# keep track of rounds
# reset score?

@app.route('/', methods = ['POST', 'GET'])
def lobby():  
    return render_template('lobby.html')

@app.route('/create-game/', methods = ['POST', 'GET'])
def create_game():  
    return render_template('create-game.html')

@app.route('/join-game/', methods = ['POST', 'GET'])
def join_game():  
    return render_template('join-game.html')

@app.route('/build_new_game/', methods = ['POST', 'GET'])
def build_new_game(): 
    # reset session vars when beginning a new game
    resetSessionVars()

    gamename = request.form.get('gamename', '')
    cardpack = request.form.get('cardpack', '')

    game = Game(gamename, cardpack)
    game.setVars()

    if cardpack == 'custom':
        return redirect(url_for('add_cards', gamename = gamename))
    else:
        return redirect(url_for('home', gamename = gamename))
        #return "tbd" # user wants to play with default card pack

@app.route('/build_existing_game/', methods = ['POST', 'GET'])
def build_existing_game(): 
    # reset session vars when beginning a new game
    resetSessionVars()

    gamename = request.form.get('gamename', '')
    return redirect(url_for('add_cards', gamename = gamename))

@app.route('/<gamename>/add_one_card/', methods = ['POST', 'GET'])
def add_one_card(gamename):
    game = Game(gamename)
    newcard = request.form.get('newcard', '')
    game.addCard(newcard)
    session['cards_added'].append(newcard)
    return redirect(url_for('add_cards', gamename = gamename))

@app.route('/<gamename>/add-cards/', methods = ['POST', 'GET'])
def add_cards(gamename):  
    game = Game(gamename)
    numcards = game.getNumCards()

    cards_added = session['cards_added'][::-1]

    return render_template('add-cards.html', cards_added = cards_added, numcards = numcards, gamename = gamename)

@app.route('/<gamename>/', methods = ['POST', 'GET'])
def home(gamename, card='', selected_team1 = '', selected_team2 = ''): 
    game = Game(gamename)
    numcards = game.getNumCardsRemaining()
    score = game.getScore()
    team1_score = score['team1_score']
    team2_score = score['team2_score']
    card = session.get('current_card')
    next_action = session.get('next_action', 'start')
    next_action_label = action_labels[next_action]
    team_checked = session.get('team_checked', 'team1')
    
    return render_template('home.html', gamename = gamename, card = card, team1_score = team1_score, team2_score = team2_score, numcards = numcards, team_checked = team_checked, next_action = next_action, next_action_label = next_action_label)

@app.route('/<gamename>/pick_card/', methods = ['POST', 'GET'])
def pick_card(gamename):  

    game = Game(gamename)
    card_success = request.form.get('card_success')

     # not needed

    if card_success == "false":
        game.returnLastCard()
    elif card_success == "true": # need logic here if like, 
        game.addPoint(session['team_checked'])
    
    card = game.pickCard()
    if not card:
        card = "Round is over. Click 'Start' when ready to begin next round."
        session['next_action'] = 'start_new'
    session['current_card'] = card
    return redirect(url_for('home', gamename = gamename))
    #return home(gamename = gamename, card = card, selected_team1 = selected_team1, selected_team2 = selected_team2)

@app.route('/<gamename>/start_round/', methods = ['POST', 'GET'])
def start_round(gamename):  
    game = Game(gamename)
    
    team = request.form.get('team')
    session['team_checked'] = team

    session['next_action'] = 'stop'
    return redirect(url_for('pick_card', gamename = gamename))

@app.route('/<gamename>/stop_round/', methods = ['POST', 'GET'])
def stop_round(gamename):  
    game = Game(gamename)
    game.returnLastCard()
    session['current_card'] = ''
    session['next_action'] = 'start'
    return redirect(url_for('home', gamename = gamename))

@app.route('/<gamename>/start_new_round/', methods = ['POST', 'GET'])
def start_new_round(gamename):  
    game = Game(gamename)
    game.reset()
    team = request.form.get('team')
    session['team_checked'] = team
    session['next_action'] = 'stop'
    return redirect(url_for('pick_card', gamename = gamename))

# TODO test this
@app.errorhandler(404)
def not_found():
    """Page not found."""
    return make_response(render_template("404.html"), 404)

def resetSessionVars():
    session['cards_added'] = []
    session['current_card'] = ''
    session['next_action'] = 'start'
    session['team_checked'] = 'team1'
    return

if __name__ == '__main__':
    app.run(debug=True)