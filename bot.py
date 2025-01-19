import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
import logging
import asyncio  # Add this import for sleep

# Set up logging
logging.basicConfig(level=logging.INFO)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Store ID to role and channel mappings
ID_MAPPING = {
    "12345": {"role": "Student", "channel": None},  # General student with no specific channel
    "67890": {"role": "Teacher", "channel": None},  # General teacher with no specific channel
    "21301429": {"role": "Section-10", "channel": "section-10"},  # Student with specific channel access
    "2221021": {"role": "Section-11", "channel": "section-11"},  # Section 11 student
    "2221023": {"role": "Section-11", "channel": "section-11"},  # Section 11 student
    # Add more mappings as needed
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
async def verify(ctx, id_number: str):
    print(f"Verify command received: {ctx.author} trying to verify with ID {id_number}")
    print(f"Available IDs: {list(ID_MAPPING.keys())}")  # Debug print to see available IDs
    
    # Convert ID to string to ensure consistent comparison
    id_number = str(id_number)
    
    # Get the member who used the command
    member = ctx.author

    if id_number in ID_MAPPING:
        mapping = ID_MAPPING[id_number]
        role_name = mapping["role"]
        channel_name = mapping["channel"]
        
        # Get or create the role
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role is None:
            try:
                print(f"Creating new role: {role_name}")
                role = await ctx.guild.create_role(name=role_name)
            except Exception as e:
                print(f"Could not create role: {e}")
                await ctx.send("Error: Could not create role. Please contact an administrator.")
                return
        
        try:
            # Assign the role
            await member.add_roles(role)
            
            # Handle channel permissions if specified
            if channel_name:
                channel = discord.utils.get(ctx.guild.channels, name=channel_name)
                
                # Create the channel if it doesn't exist
                if channel is None:
                    try:
                        # Create a new text channel in the server
                        overwrites = {
                            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                            role: discord.PermissionOverwrite(
                                read_messages=True,
                                send_messages=True,
                                read_message_history=True
                            )
                        }
                        
                        channel = await ctx.guild.create_text_channel(
                            channel_name,
                            overwrites=overwrites,
                            reason=f"Auto-created for {role_name}"
                        )
                        print(f"Created new channel: {channel_name}")
                        response = f"Successfully verified {member.mention}, assigned {role_name} role, and created new channel #{channel_name}!"
                    except Exception as e:
                        print(f"Could not create channel: {e}")
                        response = f"Role assigned but couldn't create channel. Please contact an administrator."
                else:
                    try:
                        # Set permissions for existing channel
                        await channel.set_permissions(role,
                            read_messages=True,
                            send_messages=True,
                            read_message_history=True
                        )
                        response = f"Successfully verified {member.mention} and assigned {role_name} role with access to #{channel_name}!"
                    except Exception as e:
                        print(f"Could not set channel permissions: {e}")
                        response = f"Role assigned but couldn't set channel permissions. Please contact an administrator."
            else:
                response = f"Successfully verified {member.mention} and assigned {role_name} role!"
            
            # Send response message
            response_msg = await ctx.send(response)
            
            # Try to delete the original command
            try:
                await ctx.message.delete()
            except Exception as e:
                print(f"Could not delete command message: {e}")
            
            # Try to delete the response after 10 seconds
            try:
                await asyncio.sleep(10)
                await response_msg.delete()
            except Exception as e:
                print(f"Could not delete response message: {e}")
                
        except discord.Forbidden as e:
            print(f"Permission error: {e}")
            await ctx.send("Error: Bot doesn't have required permissions. Please contact an administrator.")
        except Exception as e:
            print(f"Error assigning role/channel: {e}")
            await ctx.send("An error occurred. Please contact an administrator.")
    else:
        error_msg = await ctx.send("Invalid ID number!")
        await asyncio.sleep(10)
        try:
            await error_msg.delete()
        except Exception as e:
            print(f"Could not delete error message: {e}")

@bot.event
async def on_command_error(ctx, error):
    print(f"Error occurred: {str(error)}")  # Debug print
    try:
        if isinstance(error, commands.MissingRequiredArgument):
            error_msg = await ctx.send("Missing required arguments! Usage: !verify ID_NUMBER")
            await asyncio.sleep(10)
            await error_msg.delete()
        
        # Try to delete the command message that caused the error
        try:
            await ctx.message.delete()
        except Exception as e:
            print(f"Could not delete command message: {e}")
    except Exception as e:
        print(f"Error in error handling: {e}")

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