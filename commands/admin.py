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

            # Create the main ticket embed
            embed = discord.Embed(
                title="🎫 Carry Service",
                description=(
                    "Need help with Slayer or Dungeon carries? Create a ticket to purchase a carry!\n\n"
                    "**How to Buy a Carry?**\n"
                    "Select the category that fits your request. Once your ticket is created, provide all necessary details for faster service.\n\n"
                    "**Categories**\n"
                    "⚔️ Slayer Carry – Get assistance with slayer bosses.\n"
                    "🏰 Dungeon Carry – Get help completing dungeons efficiently.\n\n"
                    "Fakepixel Giveaways Carrier Staff will assist you as soon as possible.\n"
                    "⏱️ Please be patient while we process your request"
                ),
                color=discord.Color.blue()
            )

            # Set the image at the top
            embed.set_image(url="https://media.discordapp.net/attachments/1250029348690464820/1401139089247440907/ChatGPT_Image_Aug_2_2025_05_24_11_AM.png?ex=688f2ff6&is=688dde76&hm=b97d6d7bef56af42ec14ca297d64175dd2eae41721ba7251346a84171ce7e290&=&format=webp&quality=lossless&width=1209&height=805")

            class TicketCategorySelect(discord.ui.Select):
                def __init__(self, bot):
                    self.bot = bot
                    options = [
                        discord.SelectOption(label="Dungeon Carry", description="Get help completing dungeons efficiently", emoji="🏰"),
                        discord.SelectOption(label="Slayer Carry", description="Get assistance with slayer bosses", emoji="⚔️")
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

                        ticket_commands = self.bot.get_cog('TicketCommands')
                        if not ticket_commands:
                            logger.error("TicketCommands cog not found")
                            await interaction.response.send_message(
                                "An error occurred while creating the ticket.",
                                ephemeral=True
                            )
                            return

                        # Show forms for Dungeon and Slayer carries, create ticket directly for others
                        if self.values[0] == "Dungeon Carry":
                            from commands.tickets import DungeonCarryForm
                            modal = DungeonCarryForm(self.bot)
                            await interaction.response.send_modal(modal)
                        elif self.values[0] == "Slayer Carry":
                            from commands.tickets import SlayerCarryForm
                            modal = SlayerCarryForm(self.bot)
                            await interaction.response.send_modal(modal)
                        else:
                            await interaction.response.send_message(
                                embed=discord.Embed(
                                    title="Creating Ticket",
                                    description="Your ticket is being created...",
                                    color=discord.Color.blue()
                                ),
                                ephemeral=True
                            )
                            await ticket_commands.create_ticket_channel(interaction, self.values[0])

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

    @app_commands.command(name="licence", description="Display bot license and ownership information")
    async def licence_command(self, interaction: discord.Interaction):
        """Display bot license information"""
        try:
            license_embed = discord.Embed(
                title="📜 Bot License & Ownership",
                description=(
                    "📜 This bot is a custom-built system created by <@&1401235304982040596>.\n\n"
                    "🔧 Made exclusively for the FakePixel Giveaways community.\n"
                    "It is not for public use, resale, replication, or redistribution.\n\n"
                    "This bot is a custom-built automation system developed by **Darkwall**, made exclusively for use within the **FakePixel Giveaways** community.\n\n"
                    "This software is not intended for public distribution or external deployment.\n\n"
                    "🛑 **Not Permitted:**\n"
                    "• Copying, mimicking, or replicating bot features or commands\n"
                    "• Reverse-engineering or extracting any internal logic\n"
                    "• Using bot output for AI training, cloning, or automation\n"
                    "• Inviting this bot to third-party servers without written permission\n"
                    "• Redistributing, reselling, or modifying the software\n\n"
                    "✅ **License & Rights:**\n"
                    "This software is protected under a **proprietary commercial license**, secured via **CertSecure™ Software Licensing Services**.\n"
                    "All rights reserved © 2025 **Darkwall**.\n"
                    "Unauthorized use will result in takedowns and legal enforcement.\n\n"
                    "📩 **Contact:**\n"
                    "For permissions or licensing inquiries, contact **Darkwall** or the FakePixel Giveaways staff team."
                ),
                color=discord.Color.from_rgb(220, 20, 60)
            )
            
            await interaction.response.send_message(embed=license_embed, ephemeral=True)
            logger.info(f"License command used by {interaction.user.name}")
            
        except Exception as e:
            logger.error(f"Error in license command: {e}")
            await interaction.response.send_message("An error occurred while displaying license information.", ephemeral=True)

    @app_commands.command(name="carried", description="Log completed carries for staff approval")
    @app_commands.describe(
        staff="The staff member who completed the carries",
        number_of_runs="Number of runs completed",
        carry_type="Type of carry (dungeon or slayer)",
        floor_or_tier="Floor (f1-f7, m1-m7, entrance) or tier (t2-t4)",
        grade="Grade achieved (s or s+)"
    )
    async def carried(
        self,
        interaction: discord.Interaction,
        staff: discord.Member,
        number_of_runs: int,
        carry_type: str,
        floor_or_tier: str,
        grade: str
    ):
        """Log completed carries for approval"""
        try:
            carry_system = self.bot.get_cog('CarrySystem')
            if carry_system:
                await carry_system.carried(interaction, staff, number_of_runs, carry_type, floor_or_tier, grade)
            else:
                await interaction.response.send_message("Carry system not available.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in carried command: {e}")
            await interaction.response.send_message("An error occurred while processing the carry request.", ephemeral=True)

    @app_commands.command(name="points", description="View total approved points for a staff member")
    @app_commands.describe(staff="The staff member to check points for")
    async def points(self, interaction: discord.Interaction, staff: discord.Member):
        """View total points for a staff member"""
        try:
            carry_system = self.bot.get_cog('CarrySystem')
            if carry_system:
                await carry_system.points(interaction, staff)
            else:
                await interaction.response.send_message("Carry system not available.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in points command: {e}")
            await interaction.response.send_message("An error occurred while retrieving points.", ephemeral=True)

    @app_commands.command(name="leaderboard", description="View top staff members by carry points")
    async def leaderboard(self, interaction: discord.Interaction):
        """Display carry points leaderboard"""
        try:
            carry_system = self.bot.get_cog('CarrySystem')
            if carry_system:
                await carry_system.leaderboard(interaction)
            else:
                await interaction.response.send_message("Carry system not available.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}")
            await interaction.response.send_message("An error occurred while retrieving the leaderboard.", ephemeral=True)

    @app_commands.command(name="pending_carries", description="View pending carry approvals")
    @app_commands.checks.has_any_role("Manager", "Admin")
    async def pending_carries(self, interaction: discord.Interaction):
        """View all pending carry approvals"""
        try:
            carry_system = self.bot.get_cog('CarrySystem')
            if carry_system:
                await carry_system.pending_carries(interaction)
            else:
                await interaction.response.send_message("Carry system not available.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in pending_carries command: {e}")
            await interaction.response.send_message("An error occurred while retrieving pending carries.", ephemeral=True)

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
            discord.SelectOption(label="Dungeon Carry", description="Get help completing dungeons efficiently", emoji="🏰"),
            discord.SelectOption(label="Slayer Carry", description="Get assistance with slayer bosses", emoji="⚔️")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        # Handle ticket creation logic here
        ticket_commands = self.bot.get_cog('TicketCommands')
        if not ticket_commands:
            await interaction.response.send_message("An error occurred while creating the ticket.", ephemeral=True)
            return

        # Show forms for Dungeon and Slayer carries, create ticket directly for others
        if select.values[0] == "Dungeon Carry":
            from commands.tickets import DungeonCarryForm
            modal = DungeonCarryForm(self.bot)
            await interaction.response.send_modal(modal)
        elif select.values[0] == "Slayer Carry":
            from commands.tickets import SlayerCarryForm
            modal = SlayerCarryForm(self.bot)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.defer(ephemeral=True)
            await ticket_commands.create_ticket_channel(interaction, select.values[0])

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))