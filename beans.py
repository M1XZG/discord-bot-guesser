import discord
from discord.ext import commands
import sqlite3
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Set up the database
conn = sqlite3.connect('guesses.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS guesses (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        guess INTEGER
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS question (
        id INTEGER PRIMARY KEY DEFAULT 1,
        question_text TEXT DEFAULT 'How many jelly beans are in the jar?'
    )
''')
# Initialize with default question if not exists
c.execute('INSERT OR IGNORE INTO question (id, question_text) VALUES (1, ?)', 
          ('How many jelly beans are in the jar?',))
conn.commit()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def guess(ctx):
    # Get the current question
    c.execute('SELECT question_text FROM question WHERE id = 1')
    question = c.fetchone()[0]
    
    # Create a private thread for the user
    thread = await ctx.channel.create_thread(
        name=f"Private guess - {ctx.author.name}",
        type=discord.ChannelType.private_thread,
        auto_archive_duration=60,
        invitable=False
    )
    
    # Add only the user and the bot to the thread
    await thread.add_user(ctx.author)
    
    await thread.send(f"**{question}**\nPlease enter your guess (just type a number):")
    
    def check(m):
        return m.author == ctx.author and m.channel == thread and m.content.isdigit()
    
    try:
        msg = await bot.wait_for('message', timeout=60.0, check=check)
        number = int(msg.content)
        
        # Save the guess
        user_id = ctx.author.id
        username = str(ctx.author)
        c.execute('REPLACE INTO guesses (user_id, username, guess) VALUES (?, ?, ?)', (user_id, username, number))
        conn.commit()
        
        await thread.send(f"✅ Your guess of **{number}** has been recorded!")
        await ctx.send(f"{ctx.author.mention}, your guess has been recorded privately!", delete_after=5)
        
        # Delete the thread after a short delay
        await asyncio.sleep(5)
        await thread.delete()
        
    except asyncio.TimeoutError:
        await thread.send("⏰ Time's up! Please use `/guess` again if you want to make a guess.")
        await asyncio.sleep(3)
        await thread.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def set_question(ctx, *, question_text: str):
    c.execute('UPDATE question SET question_text = ? WHERE id = 1', (question_text,))
    conn.commit()
    await ctx.send(f'Question updated to: "{question_text}"')

@bot.command()
async def show_question(ctx):
    c.execute('SELECT question_text FROM question WHERE id = 1')
    question = c.fetchone()[0]
    await ctx.send(f'Current question: {question}')

@bot.command()
@commands.has_permissions(administrator=True)
async def list_guesses(ctx):
    c.execute('SELECT username, guess FROM guesses')
    rows = c.fetchall()
    if not rows:
        await ctx.send('No guesses have been made yet.')
        return
    msg = '\n'.join([f'{username}: {guess}' for username, guess in rows])
    await ctx.send(f'Guesses so far:\n{msg}')

@bot.command()
@commands.has_permissions(administrator=True)
async def find_closest(ctx, answer: int):
    c.execute('SELECT username, guess FROM guesses')
    rows = c.fetchall()
    
    if not rows:
        await ctx.send('No guesses have been made yet.')
        return
    
    # Find the closest guess
    closest_user = None
    closest_guess = None
    min_difference = float('inf')
    
    for username, guess in rows:
        difference = abs(guess - answer)
        if difference < min_difference:
            min_difference = difference
            closest_user = username
            closest_guess = guess
    
    await ctx.send(f'The closest guess was {closest_guess} by {closest_user} (off by {min_difference})')

# Run the bot using the token from the .env file
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: DISCORD_BOT_TOKEN not found in .env file.")