import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Store ID to role mappings
ID_ROLE_MAPPING = {
    "12345": "Student",
    "67890": "Teacher",
    # Add more ID to role mappings as needed
}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print(f'Connected to {len(bot.guilds)} guilds:')
    for guild in bot.guilds:
        print(f'- {guild.name} (ID: {guild.id})')
    print('------')

@bot.event
async def on_connect():
    print("Bot connected to Discord!")

@bot.event
async def on_disconnect():
    print("Bot disconnected from Discord!")

@bot.event
async def on_error(event, *args, **kwargs):
    logging.error(f'Error in {event}:', exc_info=True)

@bot.event
async def on_message(message):
    print(f"Message received: {message.content}")  # Debug print
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def verify(ctx, member: discord.Member, id_number: str):
    print(f"Verify command received: {ctx.author} trying to verify {member} with ID {id_number}")  # Debug print
    if id_number in ID_ROLE_MAPPING:
        role_name = ID_ROLE_MAPPING[id_number]
        print(f"Found role mapping: {role_name}")  # Debug print
        
        # Get the role object
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        print(f"Found role object: {role}")  # Debug print
        
        if role is None:
            print("Role not found, creating new one")  # Debug print
            role = await ctx.guild.create_role(name=role_name)
        
        # Assign the role to the member
        await member.add_roles(role)
        await ctx.send(f"Successfully verified {member.mention} and assigned {role_name} role!")
    else:
        await ctx.send("Invalid ID number!")

@bot.event
async def on_command_error(ctx, error):
    print(f"Error occurred: {str(error)}")  # Debug print
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required arguments! Usage: !verify @user ID_NUMBER")

# Load token and run bot
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

if not token:
    print("ERROR: No token found in .env file!")
    exit(1)

try:
    bot.run(token)
except discord.LoginFailure:
    print("ERROR: Invalid token or improper privileges!")
except discord.PrivilegedIntentsRequired:
    print("ERROR: Required privileged intents are not enabled!")
except Exception as e:
    print(f"ERROR: An unexpected error occurred: {str(e)}")