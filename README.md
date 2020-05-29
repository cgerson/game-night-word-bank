## https://game-night-word-bank.herokuapp.com/

This is a Python / Flask / Redis implementation of the fun game Celebrities (also known as Celebrity, Salad Bowl... the list goes on).

# Setup
1. Hop onto Zoom with friends / family.
2. Create a game at the link provided.
3. Share the unique game name with the other players, and instruct them to join game via same link.
4. Every player adds cards to the word bank. 
5. When all players have finished adding cards, players should be split into two teams.

# How to Play
- When a player is ready to give clues, they will draw a card by selecting their team in the dropdown and pressing "Start".
- After pressing "Start", said player will see a card appear on their screen (and not on any other player's screen). They will also see a countdown appear, signaling their time left to give clues.
- The player giving clues will press the checkmark if their team guesses the card correctly, otherwise they can skip by clicking the arrow. 
- Once their time is up, the player giving clues should press "Stop". This will ensure that any card remaining on their screen will return to the word bank.