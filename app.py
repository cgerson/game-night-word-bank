from __future__ import unicode_literals

from flask import Flask, Response, render_template, request, session, url_for, redirect
from flask_session import Session
import random
import datetime
from game import Game
#from flask import current_app as app
#from . import app
# from flask_assets import Environment, Bundle

#from . import game

sess = Session()

app = Flask(__name__, instance_relative_config=False)
app.config.from_object('config.Config') 

Session(app)


# http://clouddatafacts.com/heroku/heroku-flask-redis/flask_redis.html#pre-rerequisites 
# https://hackersandslackers.com/redis-py-python/

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
# reset: reset score and card deck
# timer
# if user enters not thru create/join, they should be redirected

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

    session['gamename'] = gamename

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
    session['gamename'] = gamename

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

    # redirect
    if session.get('gamename') != gamename:
        return redirect(url_for('lobby'))

    game = Game(gamename)
    numcardstotal = game.getNumCards()

    cards_added = session['cards_added'][::-1]

    return render_template('add-cards.html', cards_added = cards_added, numcardstotal = numcardstotal, gamename = gamename)

@app.route('/<gamename>/', methods = ['POST', 'GET'])
def home(gamename, card='', selected_team1 = '', selected_team2 = ''): 

    # redirect
    if session.get('gamename') != gamename:
        return redirect(url_for('lobby'))

    game = Game(gamename)
    numcards = game.getNumCardsRemaining()
    numcardstotal = game.getNumCards()
    score = game.getScore()
    current_round = game.getRound()
    team1_score = score['team1_score']
    team2_score = score['team2_score']
    card = session.get('current_card')
    
    next_action = session.get('next_action')

    disabled = "disabled" if next_action == 'start' else ""
    next_action_label = action_labels[next_action]
    
    team_checked = session.get('team_checked', 'team1')
    
    return render_template('home.html', gamename = gamename, card = card, team1_score = team1_score, team2_score = team2_score, numcards = numcards, numcardstotal = numcardstotal, current_round = current_round, team_checked = team_checked, next_action = next_action, next_action_label = next_action_label, disabled = disabled)

@app.route('/<gamename>/pick_card/', methods = ['POST', 'GET'])
def pick_card(gamename, start = False):  

    game = Game(gamename)

    # don't need to check for card success on start / start_round, only after "correct" guesses
    # could create a new route
    # just need to skip to pickcard

    if start == False:
        card_success = request.form.get('card_success')

        if card_success == "false":
            game.returnLastCard()
        elif card_success == "true": # need logic here if like, 
            game.addPoint(session['team_checked'])
    
    card = game.pickCard()
    if card:
        session['next_action'] = 'stop'
    else:
        card = "No cards remaining. Round is over."
        session['next_action'] = 'start'
        game.startRound()
    session['current_card'] = card 

    return redirect(url_for('home', gamename = gamename))
    #return home(gamename = gamename, card = card, selected_team1 = selected_team1, selected_team2 = selected_team2)

@app.route('/<gamename>/start_round/', methods = ['POST', 'GET'])
def start_round(gamename):  
    game = Game(gamename)

    # insert into here logic in case first round
    first_start = game.checkFirstStart()
    if first_start == "true":
        game.startRound()

    team = request.form.get('team')
    session['team_checked'] = team
    session['next_action'] = 'stop'
    session['timestamp_start'] = addSecs(datetime.datetime.now(), 0)
    return redirect(url_for('pick_card', gamename = gamename, start = True))

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
    game.startRound()
    team = request.form.get('team')
    session['team_checked'] = team
    session['next_action'] = 'stop'
    session['timestamp_start'] = addSecs(datetime.datetime.now(), 0)
    return redirect(url_for('pick_card', gamename = gamename, start = True))

@app.route('/<gamename>/hard_reset/', methods = ['POST', 'GET'])
def hard_reset(gamename):  
    game = Game(gamename)
    game.hardReset()
    session['current_card'] = ''
    session['next_action'] = 'start'
    return redirect(url_for('home', gamename = gamename))

@app.errorhandler(404)
def not_found(e):
    """Page not found."""
    return render_template("404.html"), 404

def resetSessionVars():
    session['gamename'] = None # check to redirect users to lobby if needed
    session['cards_added'] = []
    session['current_card'] = ''
    session['next_action'] = 'start'
    session['team_checked'] = 'team1'
    session['timestamp_start'] = addSecs(datetime.datetime.now(), 0)
    session['times_up'] = True
    return

def addSecs(tm, secs):
    fulldate = datetime.datetime(100, 1, 1, tm.hour, tm.minute, tm.second)
    fulldate = fulldate + datetime.timedelta(seconds=secs)
    return fulldate

# TODO test this
@app.route('/time_feed/')
def time_feed():
    now_plus_30sec = addSecs(session['timestamp_start'], 30)
    if (now_plus_30sec - addSecs(datetime.datetime.now(), 0)) > datetime.timedelta(0,0):
        def generate():
            yield str(now_plus_30sec - addSecs(datetime.datetime.now(), 0))
        return Response(generate(), mimetype='text')
    else:
        return "Your turn's up! Press Stop"
        #home(gamename = session['gamename'])
    '''
    def generate():
        if (now_plus_30sec - addSecs(datetime.datetime.now(), 0)) > datetime.timedelta(0,0):
            yield str(now_plus_30sec - addSecs(datetime.datetime.now(), 0))
        else:
            yield "Time's up"
        #.time().strftime("%H:%M:%S")  # return also will work
        # .strftime("%H:%M:%S")
    return Response(generate(), mimetype='text') 

    '''



if __name__ == '__main__':
    app.run(debug=True)