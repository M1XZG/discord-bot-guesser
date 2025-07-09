# Discord Guessing Game Bot

## Table of Contents
- [Purpose](#purpose)
- [Features](#features)
- [Commands](#commands)
  - [User Commands](#user-commands)
  - [Administrator Commands](#administrator-commands)
- [Setup](#setup)
- [How It Works](#how-it-works)
- [Use Cases](#use-cases)
- [Technical Details](#technical-details)
- [License](#license)

## Purpose
This Discord bot facilitates guessing games for special events, contests, or community activities. Users can submit private guesses, and administrators can manage the game and determine winners. Perfect for any scenario where you need people to guess - from numbers like "how many jelly beans in a jar" to text answers like "name your favorite movie" or "what will be the winning team."

## Features
- Private guessing system - no one can see other users' guesses
- Each user can only have one active guess (new guesses replace old ones)
- Supports both numeric and text-based questions
- Customizable questions for any type of guessing game
- SQLite database to store all guesses
- Admin tools to manage the game and find winners
- Event control - admins can open/close guessing periods
- Automatic database migration when updating the bot
- Comprehensive logging to discord.log file
- Thread-based private submissions that auto-delete for privacy
- Safe game reset with double confirmation
- Starts with no question set - admins must configure before use

## Commands

### User Commands
- `/guess` - Start a private thread to submit your guess (only works when guessing is open).
- `/show_question` - Display the current question being asked.
- `/guessing_status` - Check if guessing is currently open or closed and what type of answer is expected.
- `/guesshelp` - Show available commands (shows admin commands only if you're an administrator).

### Administrator Commands
- `/set_question <question> [numeric_only]` - Set a custom question for the guessing game.
  - `numeric_only` parameter (optional): Set to True for number-only answers, False for text answers (default: True)
  - Example: `/set_question How many jelly beans are in the jar? numeric_only:True`
  - Example: `/set_question What's your favorite movie from 2023? numeric_only:False`
  - Example: `/set_question Name a country starting with 'B' numeric_only:False`
- `/open_guessing` - Open the guessing event and allow users to submit guesses (requires a question to be set first).
- `/close_guessing` - Close the guessing event and prevent new submissions (shows total number of guesses).
- `/list_guesses` - Show all users who have submitted guesses and their answers.
- `/find_closest <answer>` - Find winners based on the answer:
  - For numeric questions: Finds the closest guess to the number
  - For text questions: Shows exact matches or all answers for review
  - Example: `/find_closest 150` (for numeric questions)
  - Example: `/find_closest Brazil` (for text questions)
- `/reset_game` - Clear all guesses and reset the game:
  - Can only be used when guessing is closed
  - Opens a private thread for confirmation
  - Shows current game statistics before deletion
  - Requires typing "DELETE" then "CONFIRM RESET" to proceed
  - Clears all data including the question

## Setup
1. Install requirements: `pip install -r requirements.txt`
2. Create a `.env` file with your Discord bot token:
   ```
   DISCORD_BOT_TOKEN=your_token_here
   ```
3. Run the bot: `python guesser.py`

## How It Works
1. An administrator sets up a question using `/set_question` (choosing numeric or text mode)
2. An administrator opens guessing with `/open_guessing`
3. Users type `/guess` to start a private thread
4. The bot provides a clickable link to jump directly to the private thread
5. In the private thread, users enter their answer (number or text based on question type)
6. The thread is automatically deleted after submission for privacy
7. When ready, administrators close guessing with `/close_guessing`
8. Administrators use `/find_closest` with the actual answer to determine winners
9. Optionally, administrators can `/reset_game` to clear all data and start fresh

## Use Cases
- **Numeric Guessing**:
  - Contest giveaways (guess the number to win)
  - Event predictions (attendance, scores, statistics)
  - Fundraising events (guess the total raised)
  - Sports predictions (final scores, player stats)
  
- **Text-Based Guessing**:
  - Trivia contests
  - Opinion polls (favorite movie, song, etc.)
  - Prediction games (Oscar winners, sports champions)
  - Creative contests (best name suggestions)

## Technical Details
- **Database**: SQLite with automatic schema migration
- **Privacy**: Uses Discord private threads that auto-delete after submission
- **Logging**: All bot activity logged to `discord.log` file with session separators
- **Commands**: Uses Discord slash commands with autocomplete
- **Permissions**: Admin commands require Discord administrator permissions
- **Answer Types**: Dynamically switches between numeric and text validation
- **Data Safety**: Reset command requires double confirmation to prevent accidental deletion
- **Initial State**: Bot starts with no question set and guessing closed

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
