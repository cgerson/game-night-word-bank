import random
import redis 
import os

redis_url = os.environ['REDISCLOUD_URL']
db=redis.from_url(redis_url)

placeholder_cards = 'Oprah_Santa Claus_Harry Potter_Beyonce_Lance Armstrong_Steve Jobs_Tom Hanks_Lil Dicky_Moses_Marge Simpson_Captain Kirk_FDR_Gandalf_Netanyahu_Beatrice Potter_Peter Pan'

db.set('default_card_pack', placeholder_cards)

class Game:
    def __init__(self, gamename, cardpack = "custom"):
        self.gamename = gamename
        self.cardpack = cardpack
        self.team1_score_key = self.sessionize('team1_score',self.gamename)
        self.team2_score_key = self.sessionize('team2_score',self.gamename)
        self.rounds_key = self.sessionize('rounds',self.gamename)
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
        db.set(self.rounds_key, '0', 14400)
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

    def startRound(self):
        # reset card pack
        cards=db.get(self.card_pack_key).decode('UTF-8')
        db.set(self.cards_remaining_key,cards)
        self.incrRound()

    def hardReset(self):
        # reset card pack
        cards=db.get(self.card_pack_key).decode('UTF-8')
        db.set(self.cards_remaining_key,cards)
        # reset score
        db.set(self.team1_score_key, '0')
        db.set(self.team2_score_key, '0')
        # reset rounds
        db.set(self.rounds_key, '0')

    def incrRound(self):
        current_round = int(db.get(self.rounds_key).decode('UTF-8'))
        new_round = current_round + 1
        db.set(self.rounds_key, str(new_round))

    def getRound(self):
        return db.get(self.rounds_key).decode('UTF-8')

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

    def getNumCardsRemaining(self):
        if db.exists(self.cards_remaining_key):
            cards_raw=db.get(self.cards_remaining_key).decode('UTF-8').split("_")
            cards = list(filter(lambda x: x, cards_raw))
            return len(cards)
        return 0
    
    def getNumCards(self):
        if db.exists(self.card_pack_key):
            cards_raw=db.get(self.card_pack_key).decode('UTF-8').split("_")
            cards = list(filter(lambda x: x, cards_raw))
            return len(cards)
        return 0

    def sessionize(self, s, gamename):
        return '{s}_{gamename}'.format(s=s, gamename=gamename)