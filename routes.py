from __future__ import unicode_literals

import os
import random
import redis
from flask import Flask, render_template, request, session, url_for, redirect

from flask_session import Session


# http://clouddatafacts.com/heroku/heroku-flask-redis/flask_redis.html#pre-rerequisites 
# https://hackersandslackers.com/redis-py-python/

app = Flask(__name__)
app.config.from_object('config.Config')
Session(app)

redis_url = os.environ['REDISCLOUD_URL']

placeholder_cards = 'Oprah_Santa Claus_Harry Potter_Beyonce_Lance Armstrong_Steve Jobs_Tom Hanks_Lil Dicky_Moses_Marge Simpson_Captain Kirk_FDR_Gandalf_Netanyahu_Beatrice Potter_Peter Pan'

db=redis.from_url(redis_url)
db.set('default_card_pack', placeholder_cards)

# TODO
# use session to record last card picked?
# use session to record last team picked?
# don't expose pick_card URL, can I route thru pick_card to home, but still send card picked? this might be a good use of sessions

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
    session['cards_added'] = []
    session['current_card'] = ''

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
    session['cards_added'] = []
    session['current_card'] = ''

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
    numcards = game.getNumCards()
    score = game.getScore()
    team1_score = score['team1_score']
    team2_score = score['team2_score']
    card = session.get('current_card', '')
    
    return render_template('home.html', gamename = gamename, card = card, team1_score = team1_score, team2_score = team2_score, numcards = numcards, selected_team1 = selected_team1, selected_team2 = selected_team2)

@app.route('/<gamename>/pick_card/', methods = ['POST', 'GET'])
def pick_card(gamename):  

    game = Game(gamename)
    card_success = request.form.get('card_success')
    team = request.form.get('team')
    selected_team1 = "selected" if team == 'team1' else ''
    selected_team2 = "selected" if team == 'team2' else ''

     # not needed

    if card_success == "false":
        game.returnLastCard()
    elif card_success == "true":
        game.addPoint(team)
    
    card = game.pickCard()
    if not card:
        card = "Round is over. Click 'Start' when ready to begin next round."
    session['current_card'] = card
    return redirect(url_for('home', gamename = gamename))
    #return home(gamename = gamename, card = card, selected_team1 = selected_team1, selected_team2 = selected_team2)

@app.route('/<gamename>/start_round/', methods = ['POST', 'GET'])
def start_round(gamename):  
    game = Game(gamename)
    game.reset()
    return redirect(url_for('pick_card', gamename = gamename))

class Game:
    def __init__(self, gamename, cardpack = "custom"):
        self.gamename = gamename
        self.cardpack = cardpack
        self.team1_score_key = self.sessionize('team1_score',self.gamename)
        self.team2_score_key = self.sessionize('team2_score',self.gamename)
        self.last_card_picked_key = self.sessionize('last_card_picked',self.gamename)
        self.card_pack_key = self.sessionize('card_pack',self.gamename)
        self.cards_remaining_key = self.sessionize('cards_remaining',self.gamename)

    def setVars(self):
        # track two game vars:
        # 1 - full card set, in "card_pack_key"
        # 2 - cards remaining in full card set at any moment in game, in "cards_remaining_key" 
        
        default_cards_value = placeholder_cards if self.cardpack == 'default' else ''
        db.set(self.cards_remaining_key, default_cards_value, 14400)
        db.set(self.card_pack_key, default_cards_value, 14400) # 4 hour ttl
        
        db.set(self.team1_score_key, '0', 14400)
        db.set(self.team2_score_key, '0', 14400)
        db.set(self.last_card_picked_key, '', 14400)
    
    def addCard(self, card):
        cards=db.get(self.card_pack_key).decode('UTF-8')
        cards = cards + "_" + str(card)
        db.set(self.card_pack_key,cards)
        db.set(self.cards_remaining_key,cards)

    def pickCard(self):
        # pull cards from cards remaining
        # listify and select random card
        # rejoin as string and set as cards remaining

        cards_raw = db.get(self.cards_remaining_key).decode('UTF-8').split("_")
        cards = list(filter(lambda x: x, cards_raw))
        if len(cards) > 0:
            card = random.choice(cards)
            db.set(self.last_card_picked_key,card) # set last card picked
            cards.remove(card)
            cards_remaining = "_".join(cards)
            db.set(self.cards_remaining_key, cards_remaining)
            return card
        return None
        
    def returnLastCard(self):
        cards=db.get(self.cards_remaining_key).decode('UTF-8')
        last_card_picked = db.get(self.last_card_picked_key).decode('UTF-8')
        cards = cards + "_" + str(last_card_picked)
        db.set(self.cards_remaining_key,cards)

    def reset(self):
        cards=db.get(self.card_pack_key).decode('UTF-8')
        db.set(self.cards_remaining_key,cards)
        
    def addPoint(self, team):
        if team == "team1":
            current_score = int(db.get(self.team1_score_key).decode('UTF-8'))
            new_score = current_score + 1
            db.set(self.team1_score_key, str(new_score))
        if team == "team2":
            current_score = int(db.get(self.team2_score_key).decode('UTF-8'))
            new_score = current_score + 1
            db.set(self.team2_score_key, str(new_score))
        else:
            return "Team does not exist." # bad error handling
    
    def getScore(self):
        team1_score = db.get(self.team1_score_key).decode('UTF-8')
        team2_score = db.get(self.team2_score_key).decode('UTF-8')
        return {
            'team1_score': team1_score,
            'team2_score': team2_score
        }

    def getNumCards(self):
        if db.exists(self.cards_remaining_key):
            cards_raw=db.get(self.cards_remaining_key).decode('UTF-8').split("_")
            cards = list(filter(lambda x: x, cards_raw))
            return len(cards)
        return 0

    def sessionize(self, s, gamename):
        return '{s}_{gamename}'.format(s=s, gamename=gamename)


if __name__ == '__main__':
    app.run()