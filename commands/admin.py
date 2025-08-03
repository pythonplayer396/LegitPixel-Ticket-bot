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
    @app_commands.checks.has_any_role(1336379731330994247)
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
    @app_commands.checks.has_any_role(1336379731330994247)
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
        user_carried="The user who was carried",
        number_of_runs="Number of runs completed",
        carry_type="Type of carry (dungeon or slayer)",
        floor_or_tier="Floor (f1-f7, m1-m7, entrance) or tier (t2-t4)",
        grade="Grade achieved (s or s+)"
    )
    @app_commands.checks.has_any_role(1274788617663025182)
    async def carried(
        self,
        interaction: discord.Interaction,
        staff: discord.Member,
        user_carried: discord.Member,
        number_of_runs: int,
        carry_type: str,
        floor_or_tier: str,
        grade: str
    ):
        """Log completed carries for approval"""
        try:
            carry_system = self.bot.get_cog('CarrySystem')
            if carry_system:
                await carry_system.carried(interaction, staff, user_carried, number_of_runs, carry_type, floor_or_tier, grade)
            else:
                await interaction.response.send_message("Carry system not available.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in carried command: {e}")
            await interaction.response.send_message("An error occurred while processing the carry request.", ephemeral=True)

    @app_commands.command(name="points", description="View total approved points for a staff member")
    @app_commands.describe(staff="The staff member to check points for")
    @app_commands.checks.has_any_role(1280539104832127008)
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
    @app_commands.checks.has_any_role(1280539104832127008)
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

    @app_commands.command(name="remove_points", description="Remove points from a staff member")
    @app_commands.describe(
        staff="The staff member to remove points from",
        points="Number of points to remove"
    )
    @app_commands.checks.has_any_role("Manager", "Admin")
    async def remove_points(self, interaction: discord.Interaction, staff: discord.Member, points: int):
        """Remove points from a staff member"""
        try:
            carry_system = self.bot.get_cog('CarrySystem')
            if carry_system:
                await carry_system.remove_points(interaction, staff, points)
            else:
                await interaction.response.send_message("Carry system not available.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in remove_points command: {e}")
            await interaction.response.send_message("An error occurred while removing points.", ephemeral=True)

    @app_commands.command(name="add_carrier", description="Replace a carrier and deduct points from original")
    @app_commands.describe(
        ticket_name="The ticket name (e.g., ticket-123)",
        original_carrier="The original carrier who needs replacement",
        reason="Reason for replacement (offline/absence)",
        replacement_staff="The staff member replacing the carrier",
        points_to_deduct="Points to deduct from original carrier"
    )
    @app_commands.checks.has_any_role("Manager", "Admin")
    async def add_carrier(
        self,
        interaction: discord.Interaction,
        ticket_name: str,
        original_carrier: discord.Member,
        reason: str,
        replacement_staff: discord.Member,
        points_to_deduct: int
    ):
        """Replace a carrier and deduct points from original carrier"""
        try:
            if points_to_deduct < 0:
                await interaction.response.send_message("Points to deduct must be positive.", ephemeral=True)
                return

            carry_system = self.bot.get_cog('CarrySystem')
            if not carry_system:
                await interaction.response.send_message("Carry system not available.", ephemeral=True)
                return

            # Deduct points from original carrier
            points_data = carry_system.load_points()
            original_carrier_id = str(original_carrier.id)
            current_points = points_data.get(original_carrier_id, 0)

            if current_points == 0 and points_to_deduct > 0:
                await interaction.response.send_message(f"{original_carrier.display_name} has no points to deduct.", ephemeral=True)
                return

            # Calculate new points (don't go below 0)
            new_points = max(0, current_points - points_to_deduct)
            actual_deducted = current_points - new_points

            # Update points
            if new_points == 0:
                if original_carrier_id in points_data:
                    del points_data[original_carrier_id]
            else:
                points_data[original_carrier_id] = new_points

            carry_system.save_points(points_data)

            # Find and update the ticket channel
            ticket_channel = None
            for channel in interaction.guild.channels:
                if channel.name == ticket_name or channel.name == f"#{ticket_name}":
                    ticket_channel = channel
                    break
            
            # Format the replacement message
            replacement_message = f"{original_carrier.mention} have been replaced by {replacement_staff.mention} in #{ticket_name}"
            
            if ticket_channel:
                # Send replacement message to ticket channel
                await ticket_channel.send(replacement_message)
                
                # Send new staff addition message to ticket channel
                new_staff_message = f"🔄 **Staff Update**: {replacement_staff.mention} has been added to assist with this ticket."
                await ticket_channel.send(new_staff_message)
                
                # Remove original carrier's permissions from the ticket channel
                try:
                    await ticket_channel.set_permissions(original_carrier, read_messages=False, send_messages=False)
                    logger.info(f"Removed {original_carrier.name} permissions from {ticket_name}")
                except Exception as e:
                    logger.error(f"Error removing permissions for {original_carrier.name}: {e}")
                
                # Add new staff member permissions to the ticket channel
                try:
                    await ticket_channel.set_permissions(replacement_staff, read_messages=True, send_messages=True)
                    logger.info(f"Added {replacement_staff.name} permissions to {ticket_name}")
                except Exception as e:
                    logger.error(f"Error adding permissions for {replacement_staff.name}: {e}")

            # Send to carrier replacement log channel
            log_channel_id = 1401473630814081145
            log_channel = interaction.guild.get_channel(log_channel_id)
            
            if log_channel:
                # Send the replacement message to log channel
                await log_channel.send(replacement_message)
                
                # Also send detailed embed for record keeping
                log_embed = discord.Embed(
                    title="🔄 Carrier Replacement Details",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                
                log_embed.add_field(name="Ticket", value=f"#{ticket_name}", inline=True)
                log_embed.add_field(name="Original Carrier", value=original_carrier.mention, inline=True)
                log_embed.add_field(name="Replacement Carrier", value=replacement_staff.mention, inline=True)
                log_embed.add_field(name="Reason", value=reason, inline=True)
                log_embed.add_field(name="Points Deducted", value=str(actual_deducted), inline=True)
                log_embed.add_field(name="Manager", value=interaction.user.mention, inline=True)
                log_embed.add_field(name="Previous Points", value=str(current_points), inline=True)
                log_embed.add_field(name="New Points", value=str(new_points), inline=True)
                log_embed.set_footer(text="Carrier Replacement System")

                await log_channel.send(embed=log_embed)

            # Create confirmation embed
            confirmation_embed = discord.Embed(
                title="🔄 Carrier Replacement Processed",
                color=discord.Color.green()
            )
            confirmation_embed.add_field(name="Ticket", value=f"#{ticket_name}", inline=True)
            confirmation_embed.add_field(name="Original Carrier", value=original_carrier.mention, inline=True)
            confirmation_embed.add_field(name="Replacement Carrier", value=replacement_staff.mention, inline=True)
            confirmation_embed.add_field(name="Reason", value=reason, inline=True)
            confirmation_embed.add_field(name="Points Deducted", value=str(actual_deducted), inline=True)
            confirmation_embed.add_field(name="New Points", value=str(new_points), inline=True)

            await interaction.response.send_message(embed=confirmation_embed, ephemeral=True)

            logger.info(f"Carrier replacement processed by {interaction.user.name}: Ticket {ticket_name}, {original_carrier.name} -> {replacement_staff.name}, {actual_deducted} points deducted")

        except Exception as e:
            logger.error(f"Error in add_carrier command: {e}")
            await interaction.response.send_message("An error occurred while processing carrier replacement.", ephemeral=True)

    @app_commands.command(name="chart", description="Display carry points chart for dungeons or slayers")
    @app_commands.describe(category="Choose between dungeon or slayer points chart")
    @app_commands.choices(category=[
        app_commands.Choice(name="Dungeon", value="dungeon"),
        app_commands.Choice(name="Slayer", value="slayer")
    ])
    async def chart(self, interaction: discord.Interaction, category: str):
        """Display carry points chart for specified category"""
        try:
            # Check if user has the required role
            required_role = discord.utils.get(interaction.user.roles, id=1336379731330994247)
            if not required_role:
                await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
                return

            if category == "dungeon":
                embed = discord.Embed(
                    title="Dungeon Carry Points Chart",
                    description=(
                        "This chart shows points awarded for successful dungeon carries. Points are based on floor difficulty and grade achieved (S or S+). "
                        "Only completed and manager-approved carries are eligible.\n\n"
                        "**Normal or failed runs do not earn any points.**"
                    ),
                    color=discord.Color.red()
                )

                # Set dungeon image
                embed.set_image(url="https://media.discordapp.net/attachments/1250029348690464820/1401464879352643605/ChatGPT_Image_Aug_3_2025_03_20_28_AM.png?ex=68905f61&is=688f0de1&hm=444a0499ca17f972533970181ed3531eaa300abe27a96562fc135d3ec36ae9a3&=&format=webp&quality=lossless&width=875&height=875")

                # Dungeon Points – Catacombs
                embed.add_field(
                    name="Catacombs – F1 to F7",
                    value=(
                        "```text\n"
                        "Floor │ S Grade │ S+ Grade\n"
                        "──────┼─────────┼──────────\n"
                        " F1   │    2    │     3    \n"
                        " F2   │    3    │     4    \n"
                        " F3   │    4    │     5    \n"
                        " F4   │    5    │     6    \n"
                        " F5   │    6    │     8    \n"
                        " F6   │    8    │    10    \n"
                        " F7   │   10    │    14    \n"
                        "```"
                    ),
                    inline=False
                )

                # Dungeon Points – Master Mode
                embed.add_field(
                    name="Master Mode – M1 to M7",
                    value=(
                        "```text\n"
                        "Floor │ S Grade │ S+ Grade\n"
                        "──────┼─────────┼──────────\n"
                        " M1   │    6    │     8    \n"
                        " M2   │    7    │     9    \n"
                        " M3   │    8    │    10    \n"
                        " M4   │    9    │    12    \n"
                        " M5   │   10    │    14    \n"
                        " M6   │   14    │    18    \n"
                        " M7   │   18    │    24    \n"
                        "```"
                    ),
                    inline=False
                )

            elif category == "slayer":
                embed = discord.Embed(
                    title="Slayer Carry Points Chart",
                    description=(
                        "This chart shows points awarded for successful slayer carries. Points are based on slayer type and tier. "
                        "Only completed and manager-approved carries are eligible.\n\n"
                        "**Normal or failed runs do not earn any points.**"
                    ),
                    color=discord.Color.red()
                )

                # Set slayer image
                embed.set_image(url="https://media.discordapp.net/attachments/1250029348690464820/1401465507491741799/slayer_carry_points_chart.png?ex=68905ff6&is=688f0e76&hm=35b0d7d6e11cfa1979e9272bcbc8efc63537b8f2429f23f2f25ba5047da5d8a6&=&format=webp&quality=lossless&width=1321&height=661")

                # Slayer – Revenant, Tarantula, Sven
                embed.add_field(
                    name="Classic Slayers",
                    value=(
                        "**Revenant Horror**\n"
                        "```text\n"
                        "Tier │ Points\n"
                        "─────┼────────\n"
                        " T2  │   2    \n"
                        " T3  │   4    \n"
                        " T4  │   5    \n"
                        " T5  │   7    \n"
                        "```\n"
                        "**Tarantula Broodfather**\n"
                        "```text\n"
                        "Tier │ Points\n"
                        "─────┼────────\n"
                        " T2  │   2    \n"
                        " T3  │   4    \n"
                        " T4  │   5    \n"
                        "```\n"
                        "**Sven Packmaster**\n"
                        "```text\n"
                        "Tier │ Points\n"
                        "─────┼────────\n"
                        " T2  │   3    \n"
                        " T3  │   5    \n"
                        " T4  │   6    \n"
                        "```"
                    ),
                    inline=False
                )

                # Slayer – Advanced
                embed.add_field(
                    name="Advanced Slayers",
                    value=(
                        "**Voidgloom Seraph**\n"
                        "```text\n"
                        "Tier │ Points\n"
                        "─────┼────────\n"
                        " T1  │   4    \n"
                        " T2  │   6    \n"
                        " T3  │   8    \n"
                        " T4  │  12    \n"
                        "```\n"
                        "**Inferno Demonlord**\n"
                        "```text\n"
                        "Tier │ Points\n"
                        "─────┼────────\n"
                        " T1  │   6    \n"
                        " T2  │  10    \n"
                        " T3  │  16    \n"
                        " T4  │  20    \n"
                        "```\n"
                        "**Riftstalker Bloodfiend**\n"
                        "```text\n"
                        "Tier │ Points\n"
                        "─────┼────────\n"
                        " T1  │   3    \n"
                        " T2  │   6    \n"
                        " T3  │   9    \n"
                        " T4  │  12    \n"
                        "```"
                    ),
                    inline=False
                )

            embed.set_footer(text="Copyright by darkwall")
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error in chart command: {e}")
            await interaction.response.send_message("An error occurred while displaying the chart.", ephemeral=True)

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