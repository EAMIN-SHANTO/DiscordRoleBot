# Discord Role Bot

A Discord bot that assigns roles based on ID verification.

## Features
- Assigns roles based on ID verification
- Supports multiple role types (Student, Teacher)
- Administrator-only commands

## Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
4. Add your Discord bot token to `.env`
5. Run the bot:
   ```bash
   python bot.py
   ```

## Commands
- `!verify @user ID_NUMBER` - Assigns role based on ID (Admin only)

## Required Permissions
- Administrator permission for role assignment
- Bot requires Manage Roles permission

## Configuration
Edit the `ID_ROLE_MAPPING` in `bot.py` to customize ID to role mappings. 