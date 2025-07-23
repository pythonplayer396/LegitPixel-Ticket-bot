import discord
from discord.ext import commands
from discord import app_commands
from utils import permissions, storage, responses
import logging
import asyncio
from typing import Optional
import json
import os
from datetime import datetime, timedelta
import re

logger = logging.getLogger('discord')

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        asyncio.create_task(self.setup_defaults())

    async def setup_defaults(self):
        """Set up default messages and configurations"""
        try:
            # Set default confirmation message if not already set
            if not storage.get_confirmation_message():
                default_msg = "Are you sure to call staff? Please wait for 24 hours before using this button."
                storage.set_confirmation_message(default_msg)
                logger.info("Set default confirmation message")
        except Exception as e:
            logger.error(f"Error setting up defaults: {e}")

    @app_commands.command(name="ticket_setup")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set up the ticket system in a specific channel"""
        try:
            logger.info(f"Setting up ticket system in channel: {channel.name}")

            # Delete existing messages in the channel
            try:
                async for message in channel.history(limit=100):
                    if message.author == self.bot.user:
                        await message.delete()
                logger.info("Deleted existing ticket panel messages")
            except Exception as e:
                logger.error(f"Error deleting old messages: {e}")

            embed = discord.Embed(
                title="",
                description=(
                    "**Welcome to Legitpixel Support Discord Server!**\n"
                    "This is a place where everyone gets help in any situation!\n"
                    "Our Team is happy to help you every day :heart:\n\n"
                    "However we're trying our best, we know we're not on time sometimes due to big amount of concurrent tickets. If you're waiting for our help for more than 2 hours, don't be afraid to click on the Call for help! button to receive a message from our Staff faster. Please do this instead of mentioning Staff, even if they're\n\n"
                    "After your ticket's closed, we'd be very happy if you rate our work from 1 to 5 stars. This can be made in the message this bot has sent to your DMs, in case they're open. Thank you for contacting us!"
                ),
                color=discord.Color.from_rgb(88, 101, 242)
            )

            # Set the main image at the top
            embed.set_image(url="https://media.discordapp.net/attachments/1392181720651927662/1396951978009170091/Picsart_25-07-21_23-27-22-499.png?ex=68809d29&is=687f4ba9&hm=89e8aaa2cd3b68864d5bc13331fb99a048fd8a0816325b9e065a597dce5e9f11&=&format=webp&quality=lossless&width=1317&height=317")

            class TicketCategorySelect(discord.ui.Select):
                def __init__(self, bot):
                    self.bot = bot
                    options = [
                        discord.SelectOption(label="Support Tickets", description="Get help with general issues"),
                        discord.SelectOption(label="Connection/Server/Site Issues", description="Report connection or server problems"),
                        discord.SelectOption(label="Bug Reports", description="Report bugs or technical issues"),
                        discord.SelectOption(label="Ban Appeals", description="Appeal a punishment"),
                        discord.SelectOption(label="Player Reports", description="Report a player"),
                        discord.SelectOption(label="Others", description="General inquiries and other matters")
                    ]
                    super().__init__(placeholder="Select ticket category...", options=options, custom_id="persistent_category_select")

                async def callback(self, interaction: discord.Interaction):
                    try:
                        logger.info(f"Ticket category selected: {self.values[0]} by user: {interaction.user.name}")

                        # Check if user already has an open ticket
                        for channel in interaction.guild.channels:
                            if (channel.name.startswith('ticket-') and 
                                str(interaction.user.id) in channel.name):
                                await interaction.response.send_message(
                                    embed=discord.Embed(
                                        title="Existing Ticket",
                                        description="Please close your previous ticket before creating a new one.",
                                        color=discord.Color.red()
                                    ),
                                    ephemeral=True
                                )
                                return

                        # Create ticket directly for all categories (no forms)
                        ticket_commands = self.bot.get_cog('TicketCommands')
                        if ticket_commands:
                            await interaction.response.send_message(
                                embed=discord.Embed(
                                    title="Creating Ticket",
                                    description="Your ticket is being created...",
                                    color=discord.Color.blue()
                                ),
                                ephemeral=True
                            )
                            await ticket_commands.create_ticket_channel(interaction, self.values[0])
                        else:
                            logger.error("TicketCommands cog not found")
                            await interaction.response.send_message(
                                "An error occurred while creating the ticket.",
                                ephemeral=True
                            )

                    except Exception as e:
                        logger.error(f"Error in ticket creation callback: {e}")
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="❌ Error",
                                description="An error occurred while creating the ticket.",
                                color=discord.Color.red()
                            ),
                            ephemeral=True
                        )

            view = discord.ui.View(timeout=None)  # Persistent view with no timeout
            view.add_item(TicketCategorySelect(self.bot))

            # Send the merged embed with the view
            message = await channel.send(embed=embed, view=view)
            self.bot.add_view(view)
            await interaction.response.send_message("Ticket system set up successfully!", ephemeral=True)
            logger.info(f"Ticket system successfully set up in channel: {channel.name}")
        except Exception as e:
            logger.error(f"Error setting up ticket system: {e}")
            await interaction.response.send_message("An error occurred while setting up the ticket system.", ephemeral=True)

    @app_commands.command(name="sendmsg")
    @app_commands.checks.has_permissions(administrator=True)
    async def send_message(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        """Send a custom message to a channel"""
        try:
            logger.info(f"Sending custom message to channel: {channel.name}")
            await channel.send(message)
            await interaction.response.send_message("Custom message sent successfully!", ephemeral=True)
            logger.info(f"Custom message sent successfully to channel: {channel.name}")
        except Exception as e:
            logger.error(f"Error sending custom message: {e}")
            await interaction.response.send_message("An error occurred while sending the custom message.", ephemeral=True)

    @app_commands.command(name="setconfirmationmsg")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_confirmation_message(self, interaction: discord.Interaction, message: str):
        """Set the confirmation message for the call staff button"""
        try:
            logger.info(f"Setting new confirmation message: {message}")
            storage.set_confirmation_message(message)
            # Create embed to show the new message
            embed = discord.Embed(
                title="Confirmation Message Updated",
                description=f"New message:\n{message}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info("Confirmation message updated successfully")
        except Exception as e:
            logger.error(f"Error setting confirmation message: {e}")
            await interaction.response.send_message("An error occurred while updating the confirmation message.", ephemeral=True)

    async def cog_load(self):
        pass  # Persistent views are handled automatically by discord.py

class PersistentTicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(
        placeholder="Select ticket category...",
        custom_id="persistent_category_select",
        options=[
            discord.SelectOption(label="Support Tickets", description="Get help with general issues"),
            discord.SelectOption(label="Connection/Server/Site Issues", description="Report connection or server problems"),
            discord.SelectOption(label="Bug Reports", description="Report bugs or technical issues"),
            discord.SelectOption(label="Ban Appeals", description="Appeal a punishment"),
            discord.SelectOption(label="Player Reports", description="Report a player"),
            discord.SelectOption(label="Others", description="General inquiries and other matters")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        # Handle ticket creation logic here
        ticket_commands = self.bot.get_cog('TicketCommands')
        if ticket_commands:
            await interaction.response.defer(ephemeral=True)
            await ticket_commands.create_ticket_channel(interaction, select.values[0])

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))