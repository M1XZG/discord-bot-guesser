# bean-guesser
How many jelly beans in the jar?

## Purpose
This Discord bot facilitates a guessing game where users try to guess a number (e.g., how many jelly beans are in a jar). Each user can submit one guess privately, and administrators can manage the game and find the winner.

## Features
- Private guessing system - no one can see other users' guesses
- Each user can only have one active guess (new guesses replace old ones)
- Customizable questions
- SQLite database to store all guesses
- Admin tools to manage the game and find winners

## Commands

### User Commands
- `/guess` - Start a private thread to submit your guess. The bot will ask you to enter a number.
- `/show_question` - Display the current question being asked.

### Administrator Commands
- `/set_question <question>` - Set a custom question for the guessing game.
  - Example: `/set_question How many marbles are in the bowl?`
- `/list_guesses` - Show all users who have submitted guesses and their numbers.
- `/find_closest <answer>` - Find which user has the closest guess to the actual answer.
  - Example: `/find_closest 150` (if the answer is 150)

## Setup
1. Install requirements: `pip install -r requirements.txt`
2. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_BOT_TOKEN=your_token_here
   ```
3. Run the bot: `python beans.py`

## How It Works
1. An administrator sets up a question using `/set_question`
2. Users type `/guess` to start a private thread
3. In the private thread, users enter their numerical guess
4. The thread is automatically deleted after submission for privacy
5. When ready, administrators use `/find_closest` with the actual answer to determine the winner.
