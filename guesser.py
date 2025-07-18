import discord
from discord.ext import commands
import sqlite3
import os
from dotenv import load_dotenv
import asyncio
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('discord.log', mode='a')  # 'a' for append mode
    ]
)
logger = logging.getLogger('discord')

# Add separator for new bot session
logger.info('='*60)
logger.info(f'NEW BOT SESSION STARTED - {datetime.now()}')
logger.info('='*60)

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Set up the database
conn = sqlite3.connect('guesses.db')
c = conn.cursor()

# Function to check and update database schema
def migrate_database():
    logger.info('Checking database schema...')
    
    # Check if tables exist
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='guesses'")
    if not c.fetchone():
        logger.info('Creating guesses table...')
        c.execute('''
            CREATE TABLE guesses (
                guild_id INTEGER,
                user_id INTEGER,
                username TEXT,
                guess TEXT,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
    else:
        # Check if guild_id column exists in guesses table
        c.execute('PRAGMA table_info(guesses)')
        columns = [column[1] for column in c.fetchall()]
        
        if 'guild_id' not in columns:
            logger.info('Migrating guesses table to support multiple servers...')
            # Create new table with guild_id
            c.execute('''
                CREATE TABLE guesses_new (
                    guild_id INTEGER,
                    user_id INTEGER,
                    username TEXT,
                    guess TEXT,
                    PRIMARY KEY (guild_id, user_id)
                )
            ''')
            # Migrate existing data (set guild_id to 0 for old data)
            c.execute('INSERT INTO guesses_new (guild_id, user_id, username, guess) SELECT 0, user_id, username, guess FROM guesses')
            c.execute('DROP TABLE guesses')
            c.execute('ALTER TABLE guesses_new RENAME TO guesses')
    
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='question'")
    if not c.fetchone():
        logger.info('Creating question table...')
        c.execute('''
            CREATE TABLE question (
                guild_id INTEGER PRIMARY KEY,
                question_text TEXT DEFAULT '',
                is_open INTEGER DEFAULT 0,
                is_numeric INTEGER DEFAULT 1
            )
        ''')
    else:
        # Check for guild_id in question table
        c.execute('PRAGMA table_info(question)')
        columns = [column[1] for column in c.fetchall()]
        
        if 'guild_id' not in columns or 'id' in columns:
            logger.info('Migrating question table to support multiple servers...')
            # Create new table with guild_id
            c.execute('''
                CREATE TABLE question_new (
                    guild_id INTEGER PRIMARY KEY,
                    question_text TEXT DEFAULT '',
                    is_open INTEGER DEFAULT 0,
                    is_numeric INTEGER DEFAULT 1
                )
            ''')
            # Try to migrate existing data
            try:
                c.execute('INSERT INTO question_new (guild_id, question_text, is_open, is_numeric) SELECT 0, question_text, is_open, is_numeric FROM question WHERE id = 1')
            except:
                pass  # If migration fails, just continue
            c.execute('DROP TABLE question')
            c.execute('ALTER TABLE question_new RENAME TO question')
    
    # Check guesses table columns for other migrations
    c.execute('PRAGMA table_info(guesses)')
    columns = {col[1]: col[2] for col in c.fetchall()}
    
    # If guess column is INTEGER, we need to recreate the table with TEXT
    if 'guess' in columns and columns['guess'] == 'INTEGER':
        logger.info('Migrating guesses table to support text answers...')
        c.execute('''
            CREATE TABLE guesses_new (
                guild_id INTEGER,
                user_id INTEGER,
                username TEXT,
                guess TEXT,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        c.execute('INSERT INTO guesses_new SELECT guild_id, user_id, username, CAST(guess AS TEXT) FROM guesses')
        c.execute('DROP TABLE guesses')
        c.execute('ALTER TABLE guesses_new RENAME TO guesses')
    
    conn.commit()
    logger.info('Database schema check complete.')

# Run database migration
migrate_database()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.tree.command(name="guesshelp", description="Show available commands")
async def guesshelp(interaction: discord.Interaction):
    """Shows available commands based on user permissions"""
    embed = discord.Embed(
        title="🎯 Guessing Game Bot Commands",
        color=discord.Color.blue()
    )
    
    # User commands (everyone can see these)
    embed.add_field(
        name="📝 User Commands",
        value=(
            "**/guess** - Start a private thread to submit your guess\n"
            "**/show_question** - Display the current question\n"
            "**/guessing_status** - Check if guessing is open or closed\n"
            "**/guesshelp** - Show this help message\n"
            "**/botinfo** - Show info about this bot"
        ),
        inline=False
    )
    
    # Check if user is an admin
    if interaction.user.guild_permissions.administrator:
        embed.add_field(
            name="🛠️ Administrator Commands",
            value=(
                "**/open_guessing** - Open the guessing event\n"
                "**/close_guessing** - Close the guessing event\n"
                "**/set_question <question>** - Set a new question for the game\n"
                "**/list_guesses** - Show all submitted guesses\n"
                "**/find_closest <answer>** - Find the closest guess to the answer\n"
                "**/reset_game** - Clear all guesses and reset the game"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📌 Admin Examples",
            value=(
                "`/set_question How many jelly beans are in the jar?`\n"
                "`/find_closest 150` - If the answer is 150"
            ),
            inline=False
        )
    
    embed.set_footer(text="Only admins can see admin commands")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="botinfo", description="Show info about this bot")
async def botinfo(interaction: discord.Interaction):
    """Shows information about the bot"""
    import sys
    import subprocess
    
    # Try to get the current git branch
    branch = "unknown"
    commit_hash = "unknown"
    commit_date = "unknown"
    
    try:
        # Get current branch
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()
        
        # Get current commit hash (short)
        commit_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()
        
        # Get commit date
        commit_date = subprocess.check_output(["git", "log", "-1", "--format=%cd", "--date=short"]).decode("utf-8").strip()
    except Exception:
        pass

    # Git info formatting
    git_info = f"**Branch:** `{branch}`\n**Commit:** `{commit_hash}` ({commit_date})"

    # Count lines of code in this file
    total_lines = 0
    try:
        with open(__file__, "r", encoding="utf-8") as f:
            total_lines = sum(1 for _ in f)
    except Exception:
        pass

    # Get bot uptime
    uptime_str = "Unknown"
    if hasattr(bot, 'start_time'):
        uptime = datetime.now() - bot.start_time
        days = uptime.days
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        if days > 0:
            uptime_str = f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            uptime_str = f"{hours}h {minutes}m"
        else:
            uptime_str = f"{minutes}m"
    
    # Server count
    server_count = len(bot.guilds)
    total_users = sum(guild.member_count for guild in bot.guilds)
    
    # Database stats
    c.execute('SELECT COUNT(*) FROM guesses')
    total_guesses = c.fetchone()[0]
    c.execute('SELECT COUNT(DISTINCT guild_id) FROM guesses')
    servers_with_guesses = c.fetchone()[0]
    
    # Create embed for better formatting
    embed = discord.Embed(
        title="Discord Guessing Game Bot 🎯",
        description="A fun guessing game for your Discord server!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📊 Bot Statistics",
        value=f"Servers: **{server_count}**\nUsers: **{total_users:,}**\nUptime: **{uptime_str}**",
        inline=True
    )
    
    embed.add_field(
        name="🎮 Game Statistics",
        value=f"Total Guesses: **{total_guesses}**\nActive Servers: **{servers_with_guesses}**",
        inline=True
    )
    
    embed.add_field(
        name="🔧 Version Info",
        value=f"Branch: **{branch}**\nCommit: **{commit_hash}**\nPython: **{sys.version.split()[0]}**",
        inline=True
    )
    
    embed.add_field(
        name="📝 Code Stats",
        value=f"Lines: **{total_lines}**\nFile: **guesser.py**",
        inline=True
    )
    
    embed.add_field(
        name="🔗 Links",
        value="[GitHub Repository](https://github.com/M1XZG/discord-bot-guesser)",
        inline=False
    )
    
    embed.set_footer(text=f"Last commit: {commit_date}")
    
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    # Store bot start time for uptime calculation
    if not hasattr(bot, 'start_time'):
        bot.start_time = datetime.now()
    
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

# Remove this duplicate guesshelp command definition
# @bot.tree.command(name="guesshelp", description="Show available commands")
# async def guesshelp(interaction: discord.Interaction):
#     """Shows available commands based on user permissions"""
#     embed = discord.Embed(
#         title="🎯 Guessing Game Bot Commands",
#         color=discord.Color.blue()
#     )
#     
#     # User commands (everyone can see these)
#     embed.add_field(
#         name="📝 User Commands",
#         value=(
#             "**/guess** - Start a private thread to submit your guess\n"
#             "**/show_question** - Display the current question\n"
#             "**/guessing_status** - Check if guessing is open or closed\n"
#             "**/guesshelp** - Show this help message\n"
#             "**/botinfo** - Show info about this bot"
#         ),
#         inline=False
#     )
#     
#     # Check if user is an admin
#     if interaction.user.guild_permissions.administrator:
#         embed.add_field(
#             name="🛠️ Administrator Commands",
#             value=(
#                 "**/open_guessing** - Open the guessing event\n"
#                 "**/close_guessing** - Close the guessing event\n"
#                 "**/set_question <question>** - Set a new question for the game\n"
#                 "**/list_guesses** - Show all submitted guesses\n"
#                 "**/find_closest <answer>** - Find the closest guess to the answer\n"
#                 "**/reset_game** - Clear all guesses and reset the game"
#             ),
#             inline=False
#         )
#         
#         embed.add_field(
#             name="📌 Admin Examples",
#             value=(
#                 "`/set_question How many jelly beans are in the jar?`\n"
#                 "`/find_closest 150` - If the answer is 150"
#             ),
#             inline=False
#         )
#     
#     embed.set_footer(text="Only admins can see admin commands")
#     await interaction.response.send_message(embed=embed)

@bot.tree.command(name="guess", description="Submit your private guess")
async def guess(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    logger.info(f'User {interaction.user} (ID: {interaction.user.id}) initiated guess command in guild {guild_id}')
    
    # Check if guessing is open for this guild
    c.execute('SELECT is_open, is_numeric FROM question WHERE guild_id = ?', (guild_id,))
    result = c.fetchone()
    
    if not result:
        await interaction.response.send_message(
            "❌ No question has been set for this server yet. An admin needs to use `/set_question` first.", 
            ephemeral=True
        )
        return
    
    is_open = result[0]
    is_numeric = result[1]
    
    if not is_open:
        await interaction.response.send_message(
            "❌ Guessing is currently closed. There's nothing to guess at right now!", 
            ephemeral=True
        )
        logger.info(f'User {interaction.user} tried to guess but event is closed in guild {guild_id}')
        return
    
    # Defer the response to avoid timeout
    await interaction.response.defer(ephemeral=True)
    
    # Get the current question for this guild
    c.execute('SELECT question_text FROM question WHERE guild_id = ?', (guild_id,))
    question = c.fetchone()[0]
    
    # Create a private thread for the user
    thread = await interaction.channel.create_thread(
        name=f"Private guess - {interaction.user.name}",
        type=discord.ChannelType.private_thread,
        auto_archive_duration=60,
        invitable=False
    )
    logger.info(f'Created private thread for {interaction.user} (Thread ID: {thread.id}) in guild {guild_id}')
    
    # Add only the user and the bot to the thread
    await thread.add_user(interaction.user)
    
    if is_numeric:
        await thread.send(f"**{question}**\nPlease enter your guess (just type a number):")
    else:
        await thread.send(f"**{question}**\nPlease enter your answer:")
    
    # Send a message with a link to the thread that will take them directly there
    await interaction.followup.send(
        f"Click here to submit your guess: {thread.jump_url}", 
        ephemeral=True
    )
    
    def check(m):
        if m.author != interaction.user or m.channel != thread:
            return False
        if is_numeric:
            return m.content.isdigit()
        else:
            return len(m.content.strip()) > 0  # Any non-empty text is valid
    
    try:
        msg = await bot.wait_for('message', timeout=120.0, check=check)
        
        if is_numeric:
            guess_value = int(msg.content)
        else:
            guess_value = msg.content.strip()
        
        # Save the guess with guild_id
        user_id = interaction.user.id
        
        # Get server nickname if available, otherwise use global username
        member = interaction.guild.get_member(user_id)
        if member and member.nick:
            display_name = member.nick
            logger.info(f'Using server nickname: {display_name} for user {interaction.user}')
        else:
            display_name = interaction.user.name
            logger.info(f'Using Discord username: {display_name} (no server nickname set)')
        
        c.execute('REPLACE INTO guesses (guild_id, user_id, username, guess) VALUES (?, ?, ?, ?)', 
                  (guild_id, user_id, display_name, str(guess_value)))
        conn.commit()
        logger.info(f'User {display_name} (ID: {user_id}) guessed: {guess_value} in guild {guild_id}')
        
        await thread.send(f"✅ Your {'guess' if is_numeric else 'answer'} of **{guess_value}** has been recorded!")
        
        # Delete the thread after a short delay
        await asyncio.sleep(5)
        await thread.delete()
        
    except asyncio.TimeoutError:
        logger.warning(f'Guess timeout for user {interaction.user} (ID: {interaction.user.id}) in guild {guild_id}')
        await thread.send("⏰ Time's up! Please use `/guess` again if you want to make a guess.")
        await asyncio.sleep(3)
        await thread.delete()

@bot.tree.command(name="set_question", description="Set a new question for the guessing game")
@discord.app_commands.describe(
    question="The new question to ask",
    numeric_only="Whether to accept only numeric answers (default: True)"
)
async def set_question(interaction: discord.Interaction, question: str, numeric_only: bool = True):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need administrator permissions to use this command.", ephemeral=True)
        return
    
    guild_id = interaction.guild_id
    logger.info(f'Admin {interaction.user} (ID: {interaction.user.id}) set new question in guild {guild_id}: "{question}" (numeric_only: {numeric_only})')
    
    # Insert or update question for this guild
    c.execute('INSERT OR REPLACE INTO question (guild_id, question_text, is_numeric, is_open) VALUES (?, ?, ?, ?)', 
              (guild_id, question, 1 if numeric_only else 0, 0))
    conn.commit()
    
    response_type = "numeric answers only" if numeric_only else "text or numeric answers"
    await interaction.response.send_message(
        f'Question updated to: "{question}"\nAccepting: {response_type}'
    )

@bot.tree.command(name="show_question", description="Display the current question")
async def show_question(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    logger.info(f'User {interaction.user} (ID: {interaction.user.id}) requested current question in guild {guild_id}')
    c.execute('SELECT question_text FROM question WHERE guild_id = ?', (guild_id,))
    result = c.fetchone()
    
    if not result or not result[0] or result[0].strip() == '':
        await interaction.response.send_message('❌ No question has been set yet. An admin needs to use `/set_question` first.')
    else:
        await interaction.response.send_message(f'Current question: **{result[0]}**')

@bot.tree.command(name="list_guesses", description="Show all submitted guesses (Admin only)")
async def list_guesses(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need administrator permissions to use this command.", ephemeral=True)
        return
    
    guild_id = interaction.guild_id
    logger.info(f'Admin {interaction.user} (ID: {interaction.user.id}) requested list of guesses in guild {guild_id}')
    c.execute('SELECT username, guess FROM guesses WHERE guild_id = ?', (guild_id,))
    rows = c.fetchall()
    
    if not rows:
        await interaction.response.send_message('No guesses have been made yet.')
        return
    
    # If there are few guesses, show them in a single embed
    if len(rows) <= 20:
        embed = discord.Embed(
            title=f"All Guesses ({len(rows)} total)",
            color=discord.Color.green()
        )
        guess_list = '\n'.join([f'**{username}**: {guess}' for username, guess in rows])
        embed.description = guess_list
        await interaction.response.send_message(embed=embed)
    else:
        # For many guesses, send multiple embeds
        await interaction.response.defer()
        
        # Split guesses into chunks of 20
        chunks = [rows[i:i+20] for i in range(0, len(rows), 20)]
        
        for i, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=f"All Guesses - Part {i+1}/{len(chunks)} ({len(rows)} total)",
                color=discord.Color.green()
            )
            
            # Create the guess list for this chunk
            guess_list = '\n'.join([f'**{username}**: {guess}' for username, guess in chunk])
            
            # Split into fields if even this chunk is too long
            if len(guess_list) > 4000:
                # Split into smaller sections for fields
                lines = [f'**{username}**: {guess}' for username, guess in chunk]
                field_content = []
                current_field = []
                current_length = 0
                
                for line in lines:
                    if current_length + len(line) + 1 > 1000:  # Leave room for newlines
                        field_content.append('\n'.join(current_field))
                        current_field = [line]
                        current_length = len(line)
                    else:
                        current_field.append(line)
                        current_length += len(line) + 1
                
                if current_field:
                    field_content.append('\n'.join(current_field))
                
                # Add fields to embed
                for j, content in enumerate(field_content[:25]):  # Discord limit: 25 fields
                    field_name = f"Guesses {i*20 + j*5 + 1}-{min(i*20 + (j+1)*5, len(rows))}"
                    embed.add_field(name=field_name, value=content, inline=False)
            else:
                embed.description = guess_list
            
            # Add navigation info to footer
            embed.set_footer(text=f"Showing guesses {i*20 + 1}-{min((i+1)*20, len(rows))} of {len(rows)}")
            
            # Send the embed
            if i == 0:
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(embed=embed)
            
            # Add a small delay to avoid rate limiting for very large lists
            if len(chunks) > 10 and i < len(chunks) - 1:
                await asyncio.sleep(0.5)

@bot.tree.command(name="find_closest", description="Find the closest guess to the actual answer (Admin only)")
@discord.app_commands.describe(answer="The actual answer to compare guesses against")
async def find_closest(interaction: discord.Interaction, answer: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need administrator permissions to use this command.", ephemeral=True)
        return
    
    guild_id = interaction.guild_id
    
    # Check if the question is numeric
    c.execute('SELECT is_numeric FROM question WHERE guild_id = ?', (guild_id,))
    result = c.fetchone()
    if not result:
        await interaction.response.send_message("No question has been set for this server yet.", ephemeral=True)
        return
    
    is_numeric = result[0]
    
    if is_numeric:
        # Try to convert answer to int for numeric comparison
        try:
            answer_num = int(answer)
        except ValueError:
            await interaction.response.send_message("The current question expects numeric answers. Please provide a number.", ephemeral=True)
            return
        
        logger.info(f'Admin {interaction.user} (ID: {interaction.user.id}) finding closest guesses to answer: {answer_num} in guild {guild_id}')
        c.execute('SELECT username, guess FROM guesses WHERE guild_id = ?', (guild_id,))
        rows = c.fetchall()
        
        if not rows:
            await interaction.response.send_message('No guesses have been made yet.')
            return
        
        # Calculate differences for all valid numeric guesses
        valid_guesses = []
        for username, guess in rows:
            try:
                guess_num = int(guess)
                difference = abs(guess_num - answer_num)
                valid_guesses.append((username, guess_num, difference))
            except ValueError:
                continue  # Skip non-numeric guesses
        
        if not valid_guesses:
            await interaction.response.send_message('No valid numeric guesses found.')
            return
        
        # Sort by difference and get top 5
        valid_guesses.sort(key=lambda x: x[2])
        top_5 = valid_guesses[:5]
        
        logger.info(f'Top 5 guesses to {answer_num}: {[(u, g, d) for u, g, d in top_5]}')
        
        embed = discord.Embed(
            title="🎯 Top 5 Closest Guesses!",
            color=discord.Color.gold(),
            description=f"The actual answer was **{answer_num}**"
        )
        
        # Medal/rank emojis for top 5
        rank_emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        
        for i, (username, guess, difference) in enumerate(top_5):
            embed.add_field(
                name=f"{rank_emojis[i]} #{i+1} Place",
                value=f"**{username}**\nGuess: {guess}\nDifference: {difference}",
                inline=True
            )
        
        # Add empty field for better formatting if needed
        if len(top_5) % 3 == 2:
            embed.add_field(name="\u200b", value="\u200b", inline=True)
        
        # Add a note if there are ties
        if len(valid_guesses) > 5:
            tied_with_fifth = [g for g in valid_guesses[5:] if g[2] == top_5[4][2]]
            if tied_with_fifth:
                tied_names = [g[0] for g in tied_with_fifth]
                embed.add_field(
                    name="📌 Note",
                    value=f"Also tied for 5th place: {', '.join(tied_names[:5])}{'...' if len(tied_names) > 5 else ''}",
                    inline=False
                )
        
        await interaction.response.send_message(embed=embed)
    else:
        # For text-based questions, show exact matches and closest matches
        logger.info(f'Admin {interaction.user} (ID: {interaction.user.id}) checking for matches: "{answer}" in guild {guild_id}')
        
        # First check for exact matches
        c.execute('SELECT username, guess FROM guesses WHERE guild_id = ? AND LOWER(guess) = LOWER(?)', (guild_id, answer))
        exact_matches = c.fetchall()
        
        if exact_matches:
            embed = discord.Embed(
                title="🎯 Exact Matches Found!",
                color=discord.Color.gold(),
                description=f"The answer was: **{answer}**"
            )
            
            # Show up to first 10 exact matches
            winners = '\n'.join([f"• {username}" for username, _ in exact_matches[:10]])
            embed.add_field(
                name=f"Users who got it exactly right ({len(exact_matches)} total):",
                value=winners,
                inline=False
            )
            
            if len(exact_matches) > 10:
                embed.add_field(
                    name="Note",
                    value=f"Showing first 10 of {len(exact_matches)} exact matches",
                    inline=False
                )
        else:
            embed = discord.Embed(
                title="📝 No Exact Matches",
                color=discord.Color.blue(),
                description=f"The answer was: **{answer}**"
            )
        
        # Show all answers for manual review
        c.execute('SELECT username, guess FROM guesses WHERE guild_id = ?', (guild_id,))
        all_rows = c.fetchall()
        
        if all_rows and not exact_matches:
            answers_list = '\n'.join([f'**{username}**: {guess}' for username, guess in all_rows[:20]])
            embed.add_field(name="All Responses", value=answers_list, inline=False)
            if len(all_rows) > 20:
                embed.add_field(name="Note", value=f"Showing first 20 of {len(all_rows)} responses", inline=False)
        
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="open_guessing", description="Open the guessing event (Admin only)")
async def open_guessing(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need administrator permissions to use this command.", ephemeral=True)
        return
    
    guild_id = interaction.guild_id
    
    # Check if a question has been set for this guild
    c.execute('SELECT question_text FROM question WHERE guild_id = ?', (guild_id,))
    result = c.fetchone()
    
    if not result or not result[0] or result[0].strip() == '':
        await interaction.response.send_message(
            "❌ Cannot open guessing without a question!\n\n"
            "Please use `/set_question` to set a question first.", 
            ephemeral=True
        )
        logger.info(f'Admin {interaction.user} tried to open guessing but no question is set in guild {guild_id}')
        return
    
    question = result[0]
    
    logger.info(f'Admin {interaction.user} (ID: {interaction.user.id}) opened guessing in guild {guild_id}')
    c.execute('UPDATE question SET is_open = 1 WHERE guild_id = ?', (guild_id,))
    conn.commit()
    
    embed = discord.Embed(
        title="🎯 Guessing is Now OPEN!",
        description=f"**Current Question:** {question}\n\nUse `/guess` to submit your answer!",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="close_guessing", description="Close the guessing event (Admin only)")
async def close_guessing(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need administrator permissions to use this command.", ephemeral=True)
        return
    
    guild_id = interaction.guild_id
    logger.info(f'Admin {interaction.user} (ID: {interaction.user.id}) closed guessing in guild {guild_id}')
    c.execute('UPDATE question SET is_open = 0 WHERE guild_id = ?', (guild_id,))
    conn.commit()
    
    # Get total number of guesses for this guild
    c.execute('SELECT COUNT(*) FROM guesses WHERE guild_id = ?', (guild_id,))
    total_guesses = c.fetchone()[0]
    
    embed = discord.Embed(
        title="🔒 Guessing is Now CLOSED!",
        description=f"No more guesses will be accepted.\n\n**Total guesses received:** {total_guesses}",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="guessing_status", description="Check if guessing is open or closed")
async def guessing_status(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    c.execute('SELECT is_open, question_text, is_numeric FROM question WHERE guild_id = ?', (guild_id,))
    result = c.fetchone()
    
    if not result:
        embed = discord.Embed(
            title="❌ No Game Set Up",
            description="No question has been set yet. An admin needs to use `/set_question` first.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    is_open = result[0]
    question = result[1]
    is_numeric = result[2]
    
    if is_open:
        answer_type = "Number" if is_numeric else "Text or Number"
        embed = discord.Embed(
            title="✅ Guessing is OPEN",
            description=f"**Current Question:** {question}\n**Answer Type:** {answer_type}\n\nUse `/guess` to submit your answer!",
            color=discord.Color.green()
        )
    else:
        # Check if there's even a question set
        if not question or question.strip() == '':
            embed = discord.Embed(
                title="❌ Guessing is CLOSED",
                description="No question has been set yet. An admin needs to use `/set_question` first.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Guessing is CLOSED",
                description="There's a question set, but guessing is not open yet. Wait for an admin to open guessing!",
                color=discord.Color.red()
            )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="reset_game", description="Clear all guesses and reset the game (Admin only)")
async def reset_game(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need administrator permissions to use this command.", ephemeral=True)
        return
    
    guild_id = interaction.guild_id
    logger.info(f'Admin {interaction.user} (ID: {interaction.user.id}) initiated reset_game command in guild {guild_id}')
    
    # Check if guessing is still open
    c.execute('SELECT is_open FROM question WHERE guild_id = ?', (guild_id,))
    result = c.fetchone()
    
    if not result:
        await interaction.response.send_message(
            "❌ No game has been set up for this server yet.", 
            ephemeral=True
        )
        return
    
    is_open = result[0]
    
    if is_open:
        await interaction.response.send_message(
            "❌ Cannot reset the game while guessing is still open!\n\n"
            "Please use `/close_guessing` first before resetting the game.", 
            ephemeral=True
        )
        logger.info(f'Admin {interaction.user} tried to reset but guessing is still open in guild {guild_id}')
        return
    
    # Get current stats before reset
    c.execute('SELECT COUNT(*) FROM guesses WHERE guild_id = ?', (guild_id,))
    total_guesses = c.fetchone()[0]
    c.execute('SELECT question_text FROM question WHERE guild_id = ?', (guild_id,))
    result = c.fetchone()
    current_question = result[0] if result else "No question set"
    
    # Defer the response to avoid timeout
    await interaction.response.defer(ephemeral=True)
    
    # Create a private thread for confirmation
    thread = await interaction.channel.create_thread(
        name=f"Reset Confirmation - {interaction.user.name}",
        type=discord.ChannelType.private_thread,
        auto_archive_duration=60,
        invitable=False
    )
    
    # Add only the admin to the thread
    await thread.add_user(interaction.user)
    
    # Send initial warning
    embed = discord.Embed(
        title="⚠️ RESET GAME - CONFIRMATION REQUIRED",
        description="This action will permanently delete all data for this server!",
        color=discord.Color.red()
    )
    embed.add_field(name="Current Question", value=current_question, inline=False)
    embed.add_field(name="Total Guesses", value=str(total_guesses), inline=False)
    embed.add_field(
        name="What will be deleted:",
        value="• All user guesses\n• The current question\n• Open/closed status",
        inline=False
    )
    
    await thread.send(embed=embed)
    await thread.send("**First Confirmation**: Type `DELETE` to proceed with clearing all guesses.")
    
    # Send link to thread
    await interaction.followup.send(
        f"Please complete the reset process here: {thread.jump_url}", 
        ephemeral=True
    )
    
    def check_delete(m):
        return m.author == interaction.user and m.channel == thread and m.content.upper() == "DELETE"
    
    try:
        # First confirmation
        await bot.wait_for('message', timeout=30.0, check=check_delete)
        
        # Second confirmation
        embed2 = discord.Embed(
            title="🔴 FINAL CONFIRMATION",
            description=f"**{total_guesses} guesses** will be permanently deleted!",
            color=discord.Color.dark_red()
        )
        embed2.add_field(
            name="⚠️ This cannot be undone!",
            value="Type `CONFIRM RESET` to permanently delete all game data.",
            inline=False
        )
        
        await thread.send(embed=embed2)
        
        def check_confirm(m):
            return m.author == interaction.user and m.channel == thread and m.content.upper() == "CONFIRM RESET"
        
        # Second confirmation
        await bot.wait_for('message', timeout=30.0, check=check_confirm)
        
        # Perform the reset
        logger.info(f'Admin {interaction.user} confirmed game reset. Deleting {total_guesses} guesses in guild {guild_id}.')
        
        # Clear all guesses for this guild
        c.execute('DELETE FROM guesses WHERE guild_id = ?', (guild_id,))
        
        # Clear the question and ensure guessing is closed for this guild
        c.execute('''
            UPDATE question 
            SET question_text = '',
                is_open = 0,
                is_numeric = 1
            WHERE guild_id = ?
        ''', (guild_id,))
        
        conn.commit()
        
        # Send success message
        success_embed = discord.Embed(
            title="✅ Game Successfully Reset",
            description="All data has been cleared.",
            color=discord.Color.green()
        )
        success_embed.add_field(name="Guesses Deleted", value=str(total_guesses), inline=True)
        success_embed.add_field(name="Question", value="Cleared", inline=True)
        success_embed.add_field(name="Status", value="Closed", inline=True)
        
        await thread.send(embed=success_embed)
        logger.info(f'Game reset completed in guild {guild_id}. {total_guesses} guesses deleted. Question cleared.')
        
        # Delete thread after a delay
        await asyncio.sleep(10)
        await thread.delete()
        
    except asyncio.TimeoutError:
        logger.warning(f'Reset timeout for admin {interaction.user} (ID: {interaction.user.id}) in guild {guild_id}')
        await thread.send("❌ Reset cancelled due to timeout. No data was deleted.")
        await asyncio.sleep(5)
        await thread.delete()

# Run the bot using the token from the .env file
if TOKEN:
    logger.info('Starting bot...')
    bot.run(TOKEN)
else:
    logger.error('DISCORD_BOT_TOKEN not found in .env file')