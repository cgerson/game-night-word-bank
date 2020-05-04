from __future__ import unicode_literals

import os
import random
import redis
from flask import Flask, render_template, request

# http://clouddatafacts.com/heroku/heroku-flask-redis/flask_redis.html#pre-rerequisites 
# https://hackersandslackers.com/redis-py-python/

app = Flask(__name__)
redis_url = os.environ['REDISCLOUD_URL']

default_card_pack_string = 'Oprah_Santa Claus_Harry Potter_Beyonce_Lance Armstrong_Steve Jobs_Tom Hanks_Lil Dicky_Moses_Marge Simpson_Captain Kirk_FDR_Gandalf'

#default_game_name = "game-name"
#custom_card_pack_key = 'custom_card_pack_{0}'.format(default_game_name)

db=redis.from_url(redis_url)
db.set('default_card_pack', default_card_pack_string)
"""
db.set('custom_card_pack', '', 14400) # 4 hour ttl
db.set('cards_remaining', default_card_pack_string)
db.set('card_pack', 'default_card_pack')
db.set('game_name', default_game_name)
"""

card_pack_labels = {
    'default_card_pack': 'Default',
    'custom_card_pack': 'Custom'
}

# user enters a game name
# web.com/<gamename>/
# web.com/<gamename>/reset
# save users choices "card_pack_<gamename>" = "custom_card_pack"

@app.route('/<game_name>/')
def home(game_name, card = ""):
    numcards = get_numcards(game_name)
    current_card_pack = get_current_card_pack(game_name)
    return render_template('index.html', numcards = numcards, card_pack_label = current_card_pack, card = card, game_name = game_name)

# set back cards remaining to chosen c ardpack
@app.route('/<game_name>/reset/')
def reset(game_name):
    card_pack_key = sessionize('card_pack',game_name)
    cardpack = db.get(card_pack_key)
    cards = db.get(cardpack).decode('UTF-8')
    cards_remaining_key = sessionize('cards_remaining',game_name)
    db.set(cards_remaining_key, cards)
    return home(game_name)

@app.route('/', methods = ['POST', 'GET'])
def lobby():
    game_name = request.form.get('gamename', '')
    set_game_variables(game_name)

    root_url = "http://game-night-word-bank.herokuapp.com"
    result = "{root}/{game_name}".format(root = root_url, game_name = game_name)
    return render_template('lobby.html', result = result)

# add cards to default or custom cardpack
@app.route('/<game_name>/update/', methods = ['POST', 'GET'])
def update(game_name):
    #cardpack = db.get('card_pack')
    #cards=db.get(cardpack).decode('UTF-8')
    custom_card_pack_key = sessionize('custom_card_pack',game_name)
    cards=db.get(custom_card_pack_key).decode('UTF-8')
    
    newcard = request.form.get("newcard")
    cards = cards + "_" + str(newcard)

    db.set(custom_card_pack_key,cards)
    return render_template("addcard.html", result = "Card added: {0}".format(newcard), game_name = game_name)

@app.route('/<game_name>/add/', methods = ['POST', 'GET'])
def add(game_name):
    return render_template("addcard.html", game_name = game_name)

# select cardpack (should be selected AFTER adding cards)
@app.route('/<game_name>/updatecardpack/', methods = ['POST', 'GET'])
def updatecardpack(game_name):
    cardpack = request.form.get('cardpack')
    #cardpack_label = card_pack_labels.get(cardpack)
    
    card_pack_key = sessionize('card_pack',game_name)
    db.set(card_pack_key,cardpack) # set to chosen cardpack
    cards = db.get(cardpack).decode('UTF-8')

    cards_remaining_key = sessionize('cards_remaining',game_name)
    db.set(cards_remaining_key, cards) # set chosen cardpack to remaining cards
    return home(game_name)

@app.route('/<game_name>/setcardpack/', methods = ['POST', 'GET'])
def setcardpack(game_name):
    current_card_pack = get_current_card_pack(game_name)
    return render_template("cardpack.html", checked = current_card_pack, game_name = game_name)

@app.route('/<game_name>/emptycardpack/', methods = ['POST', 'GET'])
def emptycardpack(game_name):
    custom_card_pack_key = sessionize('custom_card_pack',game_name)
    db.set(custom_card_pack_key, '')
    cards_remaining_key = sessionize('cards_remaining',game_name)
    db.set(cards_remaining_key, '')
    return home(game_name)

# pick cards from a temp set, so that card list remains for reset
@app.route('/<game_name>/pickcard/')
def pickcard(game_name):
    cards_remaining_key = sessionize('cards_remaining',game_name)
    cards_raw = db.get(cards_remaining_key).decode('UTF-8').split("_")
    cards = list(filter(lambda x: x, cards_raw))
    numcards = 0

    if len(cards) > 0:
        card = random.choice(cards)
        cards.remove(card)
        numcards = len(cards)
        cards_remaining = "_".join(cards)
        #cards_remaining_key = sessionize('cards_remaining',game_name)
        db.set(cards_remaining_key, cards_remaining)
    else:
        card = "CLICK RESET TO BEGIN NEXT ROUND"

    return home(game_name, card = card)

def get_current_card_pack(game_name):
    card_pack_key = sessionize('card_pack',game_name)
    current_card_pack = db.get(card_pack_key).decode('UTF-8')
    #return card_pack_labels.get(current_card_pack)
    return current_card_pack.split("_")[0]

def get_numcards(game_name):
    cards_remaining_key = sessionize('cards_remaining',game_name)
    cards_raw=db.get(cards_remaining_key).decode('UTF-8').split("_")
    cards = list(filter(lambda x: x, cards_raw))
    return len(cards)

def sessionize(s, game_name):
    return '{s}_{game_name}'.format(s=s, game_name=game_name)

def set_game_variables(game_name):
    #default_card_pack_key = 'default_card_pack_{game_name}'.format(game_name = game_name)
    custom_card_pack_key = sessionize('custom_card_pack',game_name)
    cards_remaining_key = sessionize('cards_remaining',game_name)
    card_pack_key = sessionize('card_pack',game_name)
    
    #db.set(default_card_pack_key, default_card_pack_string)
    db.set(custom_card_pack_key, '', 14400) # 4 hour ttl
    db.set(cards_remaining_key, default_card_pack_string, 14400)
    db.set(card_pack_key, 'default_card_pack', 14400)
    return

if __name__ == '__main__':
    app.run()