import discord
from discord.ext import commands
from discord import ui, ButtonStyle
from discord.ui import Button, View
import json
import os
from dotenv import load_dotenv
import logging
import asyncio  # Add this import for sleep
import openpyxl  # Add this import at the top

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
            guild = interaction.guild

            # Check if user already has a section role
            has_section = False
            for role in member.roles:
                if role.name.startswith("Section-"):
                    await interaction.response.send_message(
                        f"You are already assigned to {role.name}. You cannot be in multiple sections!",
                        ephemeral=True
                    )
                    return

            # Check if this ID is already in use by another member
            role_to_check = ID_MAPPING.get(id_input, {}).get("role")
            if role_to_check:
                for guild_member in guild.members:
                    if guild_member != member:  # Don't check the current user
                        member_roles = [role.name for role in guild_member.roles]
                        if role_to_check in member_roles:
                            await interaction.response.send_message(
                                "This ID is already verified with another user. Please contact an administrator if you think this is a mistake.",
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

# Add this class for the Marks button
class MarksView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Check Marks", style=discord.ButtonStyle.primary, custom_id="marks_button")
    async def marks_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            modal = MarksModal()
            await interaction.response.send_modal(modal)
        except Exception as e:
            print(f"Marks button error: {e}")
            await interaction.response.send_message("An error occurred. Please try again.", ephemeral=True)

# Add this class for the Marks modal
class MarksModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Check Marks")
        self.student_id = discord.ui.TextInput(
            label="Enter your Student ID",
            placeholder="Enter your ID number here...",
            required=True,
            min_length=4,
            max_length=10
        )
        self.add_item(self.student_id)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            entered_id = str(self.student_id.value).strip()
            member = interaction.user
            
            # Check if the user has been verified and get their verified ID
            verified_id = None
            for role in member.roles:
                if role.name in [mapping["role"] for mapping in ID_MAPPING.values()]:
                    # Find the ID that matches this role
                    for id_num, data in ID_MAPPING.items():
                        if data["role"] == role.name:
                            verified_id = id_num
                            break
                    break
            
            # If user is not verified or trying to access different ID
            if not verified_id:
                await interaction.response.send_message(
                    "You need to verify yourself first using the verification system!",
                    ephemeral=True
                )
                return
            
            if verified_id != entered_id:
                await interaction.response.send_message(
                    "You can only check marks for your own verified ID!",
                    ephemeral=True
                )
                return
            
            # Get student information from Excel file
            student_info = self.get_marks(entered_id)
            
            if student_info:
                # Create an embed for the student information
                embed = discord.Embed(
                    title="📊 Student Information",
                    color=discord.Color.green()
                )
                
                # Add all fields
                embed.add_field(name="Name", value=student_info["Name"], inline=False)
                embed.add_field(name="ID", value=student_info["ID"], inline=True)
                embed.add_field(name="G-suit", value=student_info["G-suit"], inline=True)
                embed.add_field(name="Section", value=student_info["Section"], inline=True)
                embed.add_field(name="Marks", value=student_info["Marks"], inline=False)
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(
                    "No information found for this ID. Please check your ID and try again.",
                    ephemeral=True
                )

        except Exception as e:
            print(f"Marks fetch error: {e}")
            await interaction.response.send_message(
                "An error occurred while fetching information. Please try again later.",
                ephemeral=True
            )

    def get_marks(self, student_id):
        try:
            print(f"Current working directory: {os.getcwd()}")
            print(f"Looking for file: markst.xlsx")
            
            # Load the Excel file
            wb = openpyxl.load_workbook('markst.xlsx')
            sheet = wb.active
            
            # Convert student_id to string and remove any whitespace
            student_id = str(student_id).strip()
            print(f"Searching for Student ID: {student_id}")
            
            # Find the student's information
            for row in sheet.iter_rows(min_row=2):  # Start from second row
                cell_value = str(row[0].value).strip() if row[0].value is not None else ""
                if cell_value == student_id:
                    # Found the student, get all their information
                    student_info = {
                        "Name": str(row[1].value) if row[1].value is not None else "N/A",
                        "ID": str(row[0].value) if row[0].value is not None else "N/A",
                        "G-suit": str(row[2].value) if row[2].value is not None else "N/A",
                        "Section": str(row[3].value) if row[3].value is not None else "N/A",
                        "Marks": str(row[4].value) if row[4].value is not None else "N/A"
                    }
                    print(f"Found student info: {student_info}")
                    return student_info

            print(f"No information found for ID: {student_id}")
            return None

        except Exception as e:
            print(f"Excel read error: {e}")
            import traceback
            traceback.print_exc()
            return None

# Add this new command for setting up the marks checker
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_marks(ctx):
    """Sets up the marks checking message with button"""
    embed = discord.Embed(
        title="📊 Check Your Marks",
        description=(
            "To check your quiz marks:\n\n"
            "1. Click the 'Check Marks' button below\n"
            "2. Enter your Student ID when prompted\n"
            "3. Your marks will be shown privately\n\n"
            "**Note:** Only you can see your marks."
        ),
        color=discord.Color.blue()
    )
    
    try:
        view = MarksView()
        await ctx.send(embed=embed, view=view)
    except Exception as e:
        print(f"Setup error: {e}")
        await ctx.send("Error setting up marks checker. Please try again.")

@bot.command()
@commands.has_permissions(administrator=True)
async def check_verifications(ctx):
    """Shows which users are verified with which IDs"""
    try:
        guild = ctx.guild
        embed = discord.Embed(
            title="🔍 Verification Status",
            description="List of verified users and their IDs",
            color=discord.Color.blue()
        )

        # Create a mapping of role names to IDs for quick lookup
        role_to_id = {data["role"]: id_num for id_num, data in ID_MAPPING.items()}
        
        verified_users = []
        for member in guild.members:
            for role in member.roles:
                if role.name in role_to_id:
                    verified_users.append({
                        "member": member,
                        "role": role.name,
                        "id": role_to_id[role.name]
                    })
        
        if verified_users:
            # Sort by role name for better organization
            verified_users.sort(key=lambda x: x["role"])
            
            # Add fields for each verified user
            for user in verified_users:
                embed.add_field(
                    name=f"{user['member'].display_name}",
                    value=f"ID: {user['id']}\nRole: {user['role']}",
                    inline=True
                )
        else:
            embed.add_field(
                name="No Verified Users",
                value="No users have been verified yet.",
                inline=False
            )

        await ctx.send(embed=embed)

    except Exception as e:
        print(f"Check verifications error: {e}")
        await ctx.send("An error occurred while checking verifications.")

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