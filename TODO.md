# TODO - Discord Guessing Bot Features

## High Priority

### 1. Multiple Questions Support
- [ ] Allow admins to create multiple active questions simultaneously
- [ ] Add question categories or tags
- [ ] Let users choose which question to answer via dropdown menu
- [ ] Track which questions each user has answered
- [ ] Command: `/add_question <category> <question> [numeric_only]`
- [ ] Command: `/list_questions` - Show all active questions
- [ ] Command: `/remove_question <question_id>` - Remove a specific question
- [ ] Update `/guess` to show question selector if multiple are active

### 2. Per-Server Multi-Guild Support Fixes
- [ ] Update remaining commands to use guild_id properly:
  - [ ] `/close_guessing` - Currently uses `id = 1` instead of guild_id
  - [ ] `/guessing_status` - Currently uses `id = 1` instead of guild_id
  - [ ] `/find_closest` - Not filtering by guild_id
  - [ ] `/reset_game` - Not filtering by guild_id

## Medium Priority

### 3. Statistics and Analytics
- [ ] Command: `/stats` - Show participation statistics
- [ ] Track guess timestamps
- [ ] Show average, median, mode for numeric questions
- [ ] Show most common answers for text questions
- [ ] Leaderboard for users with most correct/closest guesses

### 4. Enhanced Winner Selection
- [ ] Support for multiple winners (top 3 closest)
- [ ] Tie-breaker logic (earliest submission wins)
- [ ] Random winner selection from all participants
- [ ] Winner history tracking

### 5. Question Templates
- [ ] Pre-made question templates for common scenarios
- [ ] Schedule questions to auto-open/close at specific times
- [ ] Recurring questions (daily/weekly trivia)

## Low Priority

### 6. User Experience Improvements
- [ ] Add reaction-based guessing for simple yes/no or multiple choice
- [ ] Allow users to change their guess before closing
- [ ] Send DM notifications when guessing opens/closes (opt-in)
- [ ] Custom embed colors per server

### 7. Export and Backup Features
- [ ] Export guesses to CSV
- [ ] Backup/restore game state
- [ ] Generate result reports with graphs

### 8. Advanced Features
- [ ] Team-based guessing competitions
- [ ] Points/scoring system across multiple rounds
- [ ] Integration with other bots for prizes/rewards
- [ ] Web dashboard for administrators

### 9. Quality of Life
- [ ] Add command aliases for convenience
- [ ] Autocomplete for question selection
- [ ] Bulk operations (reset multiple questions at once)
- [ ] Question preview before setting

## Bug Fixes Needed
- [ ] Ensure all error messages are user-friendly
- [ ] Add rate limiting to prevent spam
- [ ] Handle edge cases for very long answers
- [ ] Improve thread cleanup if bot goes offline

## Code Improvements
- [ ] Add unit tests
- [ ] Implement proper error handling throughout
- [ ] Create a config file for customizable settings
- [ ] Add database indexes for better performance
- [ ] Implement connection pooling for database

## Documentation
- [ ] Create a wiki with detailed examples
- [ ] Add screenshots to README
- [ ] Create video tutorial
- [ ] Add troubleshooting guide