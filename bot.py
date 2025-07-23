import discord
from discord.ext import commands
import os
import logging
from commands import admin, tickets
from utils import permissions, storage, responses

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='^', intents=intents)

# Register commands
async def setup_commands():
    try:
        # Create instances of command cogs
        admin_commands = admin.AdminCommands(bot)
        ticket_commands = tickets.TicketCommands(bot)

        # Add cogs to bot
        await bot.add_cog(admin_commands)
        await bot.add_cog(ticket_commands)

        # Sync command tree
        await bot.tree.sync()

        logger.info("Commands registered and synced successfully")
    except Exception as e:
        logger.error(f"Error setting up commands: {e}")
        raise  # Re-raise to ensure we catch setup failures

@bot.event
async def on_ready():
    try:
        logger.info(f'Bot is ready: {bot.user.name}')
        await setup_commands()
        
        # Register persistent views for existing tickets and setup menus
        ticket_commands = bot.get_cog('TicketCommands')
        admin_commands = bot.get_cog('AdminCommands')
        
        if ticket_commands:
            # Add persistent views for existing ticket channels
            for guild in bot.guilds:
                for channel in guild.channels:
                    if hasattr(channel, 'name') and channel.name.startswith('🎫-') and 'ticket-' in channel.name:
                        # Extract ticket number from channel name
                        parts = channel.name.split('-')
                        if len(parts) >= 3:
                            ticket_number = parts[-1]  # Last part is ticket number
                            username = parts[1]  # Second part is username
                            user = discord.utils.get(guild.members, name=username)
                            if user:
                                view = ticket_commands.TicketControls(bot, ticket_number, user)
                                bot.add_view(view)
                                logger.info(f"Registered persistent view for ticket {ticket_number}")
        
        if admin_commands:
            # Register persistent views for setup menus
            from commands.admin import PersistentTicketView
            bot.add_view(PersistentTicketView(bot))
            logger.info("Registered persistent setup menu view")
            
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Don't exit, let the bot continue running even if command setup fails
        # This allows for manual intervention if needed

# Error handling
@bot.event
async def on_command_error(ctx, error):
    try:
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command!")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found!")
        else:
            logger.error(f"Command error: {str(error)}")
            await ctx.send(f"An error occurred: {str(error)}")
    except Exception as e:
        logger.error(f"Error in error handler: {e}")

# Run the bot
try:
    bot.run("MTMyMDk5OTcwNTg4NjQ2MjA2NA.Gdwopr.zOOwicWf97B8CgtxUbOQd55QJWhstGZAz48HOs")

except discord.errors.LoginFailure as e:
    logger.error(f"Discord login failure: {e}")
except Exception as e:
    logger.error(f"Bot failed to start: {e}")