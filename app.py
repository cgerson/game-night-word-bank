import os
import random
import redis
from flask import Flask, render_template

# http://clouddatafacts.com/heroku/heroku-flask-redis/flask_redis.html#pre-rerequisites 
# https://hackersandslackers.com/redis-py-python/

app = Flask(__name__)
local = True
if local:
    redis_url = 'redis://rediscloud:Fc4aIcY1b8uIcFIDDIkVCguFYO3rU0dI@redis-18892.c232.us-east-1-2.ec2.cloud.redislabs.com:18892'
else:
    redis_url = os.environ['REDISCLOUD_URL']

db=redis.from_url(redis_url)
db.set('cards_remaining', "Oprah_Santa Claus_Harry Potter")

@app.route('/')
def hello_world():
    numcards = get_numcards()
    return render_template('index.html', numcards = numcards)

@app.route('/reset/')
def reset():
    db.set('cards_remaining', "Oprah_Santa Claus_Harry Potter")
    return 'Cards reset.'

@app.route('/add/<newcard>')
def add(newcard):
    cards=str(db.get('cards_remaining'))
    cards = cards + "_" + str(newcard)
    db.set('cards_remaining',cards)
    return 'Cards updated.'

@app.route('/pickcard/', methods=['POST', 'GET'])
def pickcard():
    cards=str(db.get('cards_remaining')).split("_")
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