import discord
from discord.ext import commands
from discord import ui, ButtonStyle
from discord.ui import Button, View
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

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Verify Me", style=ButtonStyle.green, custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            modal = VerifyModal()
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"Button error: {e}")
            await interaction.response.send_message("An error occurred. Please try again.", ephemeral=True)

class VerifyModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Verification")
        self.id_number = discord.ui.TextInput(
            label="Enter your ID Number",
            placeholder="Enter your ID number here...",
            required=True,
            min_length=4,
            max_length=10
        )
        self.add_item(self.id_number)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            id_input = str(self.id_number.value)
            member = interaction.user

            # Check if user already has a section role
            has_section = False
            for role in member.roles:
                if role.name.startswith("Section-"):
                    await interaction.response.send_message(
                        f"You are already assigned to {role.name}. You cannot be in multiple sections!",
                        ephemeral=True
                    )
                    return

            if id_input in ID_MAPPING:
                mapping = ID_MAPPING[id_input]
                role_name = mapping["role"]
                channel_name = mapping["channel"]
                
                # Get or create role
                role = discord.utils.get(interaction.guild.roles, name=role_name)
                if not role:
                    role = await interaction.guild.create_role(name=role_name)
                
                # Assign role
                await member.add_roles(role)
                success_message = f"Successfully verified! You have been assigned to {role_name}"

                # Handle channel
                if channel_name:
                    channel = discord.utils.get(interaction.guild.channels, name=channel_name)
                    if not channel:
                        overwrites = {
                            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                            role: discord.PermissionOverwrite(
                                read_messages=True,
                                send_messages=True,
                                read_message_history=True
                            )
                        }
                        channel = await interaction.guild.create_text_channel(
                            channel_name,
                            overwrites=overwrites
                        )
                    success_message += f" with access to #{channel_name}"

                await interaction.response.send_message(success_message, ephemeral=True)

                # Try to hide verification channel
                try:
                    verification_channel = interaction.channel
                    await verification_channel.set_permissions(member,
                        read_messages=False,
                        send_messages=False
                    )
                except:
                    pass

            else:
                await interaction.response.send_message(
                    "Invalid ID number! Please try again with a valid ID.",
                    ephemeral=True
                )

        except Exception as e:
            print(f"Verification error: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred. Please try again or contact an administrator.",
                    ephemeral=True
                )

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
async def setup_verification(ctx):
    """Sets up the verification message with button"""
    embed = discord.Embed(
        title="🎓 Student Verification",
        description=(
            "Welcome to the server! To get access to your section channels:\n\n"
            "1. Click the 'Verify Me' button below\n"
            "2. Enter your Student ID when prompted\n"
            "3. You'll be automatically assigned to your section\n\n"
            "**Note:** You can only be in one section at a time."
        ),
        color=discord.Color.blue()
    )
    
    try:
        view = VerifyView()
        await ctx.send(embed=embed, view=view)
    except Exception as e:
        print(f"Setup error: {e}")
        await ctx.send("Error setting up verification. Please try again.")

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

@bot.event
async def on_member_update(before, after):
    # Check if roles were removed
    removed_roles = set(before.roles) - set(after.roles)
    
    if removed_roles:
        has_section = False
        for role in after.roles:
            if role.name.startswith("Section-"):
                has_section = True
                break
        
        # If user has no section roles, show verification channel
        if not has_section:
            verification_channel = discord.utils.get(after.guild.channels, name="verification")
            if verification_channel:
                await verification_channel.set_permissions(after,
                    read_messages=True,
                    send_messages=True
                )

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