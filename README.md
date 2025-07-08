# Discord Guessing Game Bot

## Purpose
This Discord bot facilitates number guessing games for special events, contests, or community activities. Users can submit private guesses, and administrators can manage the game and determine winners. Perfect for any scenario where you need people to guess a number - from "how many jelly beans in a jar" to "guess the final score" or "how many attendees at the event."

## Features
- Private guessing system - no one can see other users' guesses
- Each user can only have one active guess (new guesses replace old ones)
- Customizable questions for any type of guessing game
- SQLite database to store all guesses
- Admin tools to manage the game and find winners

## Commands

### User Commands
- `/guess` - Start a private thread to submit your guess. The bot will ask you to enter a number.
- `/show_question` - Display the current question being asked.

### Administrator Commands
- `/set_question <question>` - Set a custom question for the guessing game.
  - Example: `/set_question How many jelly beans are in the jar?`
  - Example: `/set_question What will be the total score of the game?`
  - Example: `/set_question How many people will attend the event?`
- `/list_guesses` - Show all users who have submitted guesses and their numbers.
- `/find_closest <answer>` - Find which user has the closest guess to the actual answer.
  - Example: `/find_closest 150` (if the answer is 150)

## Setup
1. Install requirements: `pip install -r requirements.txt`
2. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_BOT_TOKEN=your_token_here
   ```
3. Run the bot: `python guesser.py`

## How It Works
1. An administrator sets up a question using `/set_question`
2. Users type `/guess` to start a private thread
3. In the private thread, users enter their numerical guess
4. The thread is automatically deleted after submission for privacy
5. When ready, administrators use `/find_closest` with the actual answer to determine the winner

## Use Cases
- Contest giveaways (guess the number to win)
- Event predictions (attendance, scores, statistics)
- Community engagement activities
- Fundraising events (guess the total raised)
- Any scenario requiring private number submissions
