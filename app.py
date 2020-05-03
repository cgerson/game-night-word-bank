from __future__ import unicode_literals

import os
import random
import redis
from flask import Flask, render_template, request

# http://clouddatafacts.com/heroku/heroku-flask-redis/flask_redis.html#pre-rerequisites 
# https://hackersandslackers.com/redis-py-python/

app = Flask(__name__)
local = True
if local:
    redis_url = 'redis://rediscloud:Fc4aIcY1b8uIcFIDDIkVCguFYO3rU0dI@redis-18892.c232.us-east-1-2.ec2.cloud.redislabs.com:18892'
else:
    redis_url = os.environ['REDISCLOUD_URL']

db=redis.from_url(redis_url)
db.set('cards_remaining', 'Oprah_Santa Claus_Harry Potter_Beyonce_Lance Armstrong')

@app.route('/')
def hello_world():
    numcards = get_numcards()
    return render_template('index.html', numcards = numcards)

@app.route('/reset/')
def reset():
    db.set('cards_remaining', 'Oprah_Santa Claus_Harry Potter_Beyonce_Lance Armstrong')
    numcards = get_numcards()
    return render_template('index.html', numcards = numcards)
    #return 'Cards reset.'

@app.route('/update/', methods = ['POST', 'GET'])
def update():
    cards=str(db.get('cards_remaining'))
    newcard = request.form.get("newcard")
    cards = cards + "_" + str(newcard)
    db.set('cards_remaining',cards)
    return render_template("addcard.html", result = "Card added: {0}".format(newcard))

@app.route('/add/', methods = ['POST', 'GET'])
def add():
    return render_template("addcard.html")

@app.route('/pickcard/')
def pickcard():
    cards = db.get('cards_remaining').decode('UTF-8').split("_")
    card = random.choice(cards)
    cards.remove(card)
    numcards = len(cards)
    cards_remaining = "_".join(cards)
    db.set('cards_remaining', cards_remaining)
    return render_template('index.html', card=card, numcards = numcards)

def get_numcards():
    cards=str(db.get('cards_remaining')).split("_")
    return len(cards)

if __name__ == '__main__':
    app.run()