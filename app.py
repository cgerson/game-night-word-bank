from __future__ import unicode_literals

import os
import random
import redis
from flask import Flask, render_template, request

# http://clouddatafacts.com/heroku/heroku-flask-redis/flask_redis.html#pre-rerequisites 
# https://hackersandslackers.com/redis-py-python/

app = Flask(__name__)
debug = True
if debug: 
    redis_url= "redis://rediscloud:Fc4aIcY1b8uIcFIDDIkVCguFYO3rU0dI@redis-18892.c232.us-east-1-2.ec2.cloud.redislabs.com:18892"
else:
    redis_url = os.environ['REDISCLOUD_URL']

db=redis.from_url(redis_url)
db.set('default_card_pack', 'Oprah_Santa Claus_Harry Potter_Beyonce_Lance Armstrong_Steve Jobs_Tom Hanks_Lil Dicky_Moses_Marge Simpson_Captain Kirk_FDR_Gandalf')
db.set('custom_card_pack', '', 14400) # 4 hour ttl
db.set('cards_remaining', 'Oprah_Santa Claus_Harry Potter_Beyonce_Lance Armstrong_Steve Jobs_Tom Hanks_Lil Dicky_Moses_Marge Simpson_Captain Kirk_FDR_Gandalf')
db.set('card_pack', 'default_card_pack')
card_pack_labels = {
    'default_card_pack': 'Default',
    'custom_card_pack': 'Custom'
}

@app.route('/')
def hello_world():
    numcards = get_numcards()
    current_card_pack = get_current_card_pack()
    return render_template('index.html', numcards = numcards, card_pack_label = current_card_pack)

# set back cards remaining to chosen cardpack
@app.route('/reset/')
def reset():
    cardpack = db.get('card_pack')
    cards = db.get(cardpack).decode('UTF-8')
    db.set('cards_remaining', cards)
    numcards = get_numcards()
    current_card_pack = get_current_card_pack()
    return render_template('index.html', numcards = numcards, card_pack_label = current_card_pack)

# add cards to default or custom cardpack
@app.route('/update/', methods = ['POST', 'GET'])
def update():
    #cardpack = db.get('card_pack')
    #cards=db.get(cardpack).decode('UTF-8')
    cards=db.get('custom_card_pack').decode('UTF-8')
    newcard = request.form.get("newcard")
    cards = cards + "_" + str(newcard)
    db.set('custom_card_pack',cards)
    return render_template("addcard.html", result = "Card added: {0}".format(newcard))

@app.route('/add/', methods = ['POST', 'GET'])
def add():
    return render_template("addcard.html")

# select cardpack (should be selected AFTER adding cards)
@app.route('/updatecardpack/', methods = ['POST', 'GET'])
def updatecardpack():
    #cards=db.get('cards_remaining').decode('UTF-8')
    cardpack = request.form.get('cardpack')
    cardpack_label = card_pack_labels.get(cardpack)
    db.set('card_pack',cardpack) # set to chosen cardpack
    cards = db.get(cardpack).decode('UTF-8')
    db.set('cards_remaining', cards) # set chosen cardpack to remaining cards
    return render_template("cardpack.html", result = "Card Pack Selected: {0}".format(cardpack_label), checked = cardpack_label)

@app.route('/setcardpack/', methods = ['POST', 'GET'])
def setcardpack():
    current_card_pack = get_current_card_pack()
    return render_template("cardpack.html", checked = current_card_pack)

# pick cards from a temp set, so that card list remains for reset
@app.route('/pickcard/')
def pickcard():
    cards_raw = db.get('cards_remaining').decode('UTF-8').split("_")
    cards = list(filter(lambda x: x, cards_raw))

    numcards = 0
    current_card_pack = get_current_card_pack()

    if len(cards) > 0:
        card = random.choice(cards)
        cards.remove(card)
        numcards = len(cards)
        cards_remaining = "_".join(cards)
        db.set('cards_remaining', cards_remaining)
    else:
        card = "CLICK RESET TO BEGIN NEXT ROUND"

    return render_template('index.html', card = card, numcards = numcards, card_pack_label = current_card_pack)

def get_current_card_pack():
    current_card_pack = db.get('card_pack').decode('UTF-8')
    return card_pack_labels.get(current_card_pack)

def get_numcards():
    cards_raw=db.get('cards_remaining').decode('UTF-8').split("_")
    cards = list(filter(lambda x: x, cards_raw))
    return len(cards)

if __name__ == '__main__':
    app.run()