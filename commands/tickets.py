import discord
from discord.ext import commands
from discord import app_commands
from utils import permissions, storage, responses
import logging
import asyncio
from typing import Optional

logger = logging.getLogger('discord')

class FeedbackModal(discord.ui.Modal):
    def __init__(self, ticket_name: str, guild: discord.Guild, rating: int):
        super().__init__(title="Ticket Feedback")
        self.ticket_name = ticket_name
        self.guild = guild
        self.rating = rating

        self.feedback = discord.ui.TextInput(
            label="How was your ticket support experience?",
            style=discord.TextStyle.paragraph,
            placeholder="Please share your experience with our support...",
            required=True,
            max_length=1000
        )

        self.suggestions = discord.ui.TextInput(
            label="Any suggestions for improvement?",
            style=discord.TextStyle.paragraph,
            placeholder="Optional: Share your suggestions...",
            required=False,
            max_length=1000
        )

        self.add_item(self.feedback)
        self.add_item(self.suggestions)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            logger.info(f"[DEBUG] Processing feedback submission for ticket {self.ticket_name}")

            ticket_number = self.ticket_name.split('-')[-1]  # Extract ticket number from channel name
            feedback_channel = discord.utils.get(self.guild.channels, name="feedback-logs")
            if not feedback_channel:
                await interaction.response.send_message("Feedback channel not found.", ephemeral=True)
                return

            # Store the feedback
            stored = storage.store_feedback(
                ticket_name=ticket_number,
                user_id=str(interaction.user.id),
                rating=self.rating,
                feedback=self.feedback.value,
                suggestions=self.suggestions.value
            )

            if not stored:
                await interaction.response.send_message("Failed to store feedback.", ephemeral=True)
                return

            claimed_by = storage.get_ticket_claimed_by(ticket_number) or "Unclaimed"
            closed_by = interaction.user.name

            # Create and send feedback embed
            feedback_embed = responses.feedback_embed(
                ticket_name=ticket_number,
                user=interaction.user,
                rating=self.rating,
                feedback=self.feedback.value,
                suggestions=self.suggestions.value,
                claimed_by=claimed_by,
                closed_by=closed_by
            )

            # Send to feedback log channel (use placeholder if feedback-logs doesn't exist)
            feedback_channel_id = "FEEDBACK_CHANNEL_ID_PLACEHOLDER"  # Replace with actual channel ID
            try:
                feedback_log_channel = self.guild.get_channel(int(feedback_channel_id)) if feedback_channel_id != "FEEDBACK_CHANNEL_ID_PLACEHOLDER" else feedback_channel
                if feedback_log_channel:
                    await feedback_log_channel.send(embed=feedback_embed)
            except Exception as e:
                logger.error(f"Could not send feedback to channel: {e}")
                # Fallback to original feedback-logs channel if exists
                if feedback_channel:
                    await feedback_channel.send(embed=feedback_embed)

            # Send confirmation in ticket channel
            confirmation_embed = discord.Embed(
                title="✅ Feedback Submitted",
                description="Thank you for your feedback! Your ticket will be closed in 10 seconds.",
                color=discord.Color.green()
            )

            await interaction.response.send_message(embed=confirmation_embed)

            # Close and delete the ticket channel after delay
            ticket_channel = interaction.channel
            await asyncio.sleep(10)

            try:
                await ticket_channel.delete()
            except discord.NotFound:
                pass  # Channel already deleted
            except Exception as e:
                logger.error(f"Error deleting channel: {e}")

        except Exception as e:
            logger.error(f"[DEBUG] Error submitting feedback: {str(e)}")
            await interaction.response.send_message(
                "An error occurred while submitting feedback.",
                ephemeral=True
            )

class CloseReasonModal(discord.ui.Modal):
    def __init__(self, bot, ticket_number: str, ticket_creator: discord.User):
        super().__init__(title="Close Ticket with Reason")
        self.bot = bot
        self.ticket_number = ticket_number
        self.ticket_creator = ticket_creator

        self.reason = discord.ui.TextInput(
            label="Reason for closing ticket",
            style=discord.TextStyle.paragraph,
            placeholder="Please provide a reason for closing this ticket...",
            required=True,
            max_length=500
        )

        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            logger.info(f"Processing ticket closure with reason for ticket {self.ticket_number}")

            # Create closure embed
            closure_embed = discord.Embed(
                title="🔒 Ticket Closed",
                description=(
                    f"This ticket has been closed by {interaction.user.mention}\n\n"
                    f"**Reason:** {self.reason.value}\n\n"
                    "Creating transcript and sending feedback request..."
                ),
                color=discord.Color.orange()
            )

            await interaction.response.send_message(embed=closure_embed)

            # Get ticket controls instance
            ticket_commands = self.bot.get_cog('TicketCommands')
            if ticket_commands:
                controls = ticket_commands.TicketControls(self.bot, self.ticket_number, self.ticket_creator)
                
                # Create transcript with reason
                await controls.create_and_send_transcript(interaction, f"Closed by staff - Reason: {self.reason.value}")
                
                # Delete the channel after transcript is sent
                await asyncio.sleep(5)
                await interaction.channel.delete()

        except Exception as e:
            logger.error(f"Error processing ticket closure with reason: {str(e)}")
            await interaction.response.send_message(
                "An error occurred while closing the ticket.",
                ephemeral=True
            )

class StarRatingButton(discord.ui.Button):
    def __init__(self, rating: int):
        super().__init__(
            style=discord.ButtonStyle.gray,
            label="⭐" * rating,
            custom_id=f"rating_{rating}"
        )
        self.rating = rating

    async def callback(self, interaction: discord.Interaction):
        try:
            channel_name = interaction.channel.name
            logger.info(f"[DEBUG] Processing star rating {self.rating} for channel {channel_name}")

            # Extract ticket number for feedback check
            ticket_number = channel_name.split('-')[-1]
            username = channel_name.split('-')[1]

            # Check if user is ticket creator
            if interaction.user.name != username:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Permission Denied",
                        description="Only the ticket creator can provide feedback.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return

            # Check if feedback already exists
            existing_feedback = storage.get_feedback(ticket_number)
            if existing_feedback:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Feedback Already Submitted",
                        description="You have already submitted feedback for this ticket.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return

            modal = FeedbackModal(
                ticket_name=channel_name,
                guild=interaction.guild,
                rating=self.rating
            )
            await interaction.response.send_modal(modal)
            logger.info(f"[DEBUG] Opened feedback modal for ticket {ticket_number} with rating {self.rating}")

        except Exception as e:
            logger.error(f"[DEBUG] Error processing star rating: {str(e)}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description="An error occurred while processing your rating. Please try again.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

class TicketCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_categories = ['Support Tickets', 'Connection/Server/Site Issues', 'Bug Reports', 'Ban Appeals', 'Player Reports', 'Others']
        logger.info("TicketCommands cog initialized")

    async def parse_ticket_channel(self, channel_name: str, context: str = "Unknown") -> tuple[str, str]:
        try:
            if not channel_name:
                logger.error(f"[DEBUG] {context} - Channel name is empty")
                return ("", "")

            logger.info(f"[DEBUG] {context} - Parsing channel name: {channel_name}")
            
            # New format: ticket-1
            if channel_name.startswith("ticket-"):
                parts = channel_name.split('-')
                if len(parts) >= 2:
                    ticket_number = parts[1]
                    # For new format, we need to get username from ticket storage
                    # Return empty username for now, will be handled by caller
                    logger.info(f"[DEBUG] {context} - Found ticket number: {ticket_number}")
                    return (ticket_number, "")
            
            logger.error(f"[DEBUG] {context} - Could not parse channel format")
            return ("", "")

        except Exception as e:
            logger.error(f"[DEBUG] {context} - Error parsing channel name: {str(e)}")
            return ("", "")

    async def create_ticket_channel(self, interaction: discord.Interaction, category: str, details: Optional[str] = None):
        try:
            logger.info(f"Creating ticket channel for {interaction.user.name} in category {category} with details: {details}")

            if storage.has_open_ticket(str(interaction.user.id)):
                existing_channel_id = storage.get_user_ticket_channel(str(interaction.user.id))

                # Guard against None and invalid channel ID
                if existing_channel_id:
                    try:
                        existing_channel = interaction.guild.get_channel(int(existing_channel_id))
                        if existing_channel:
                            await interaction.followup.send(
                                embed=discord.Embed(
                                    title="❌ Existing Ticket",
                                    description=f"You already have an open ticket in {existing_channel.mention}. Please close your existing ticket before creating a new one.",
                                    color=discord.Color.red()
                                ),
                                ephemeral=True
                            )
                            return None
                    except (ValueError, TypeError) as e:
                        logger.error(f"Error converting channel ID: {e}")
                        # Continue with new ticket creation since the existing one seems invalid

            category_channel = discord.utils.get(interaction.guild.categories, name=category)
            if not category_channel:
                category_channel = await interaction.guild.create_category(category)
                logger.info(f"Created new category: {category}")

            # Ensure ticket_number is always a string
            ticket_number = str(storage.get_next_ticket_number() or "ERROR")
            if ticket_number == "ERROR":
                logger.error("Failed to generate ticket number")
                await interaction.followup.send("Error creating ticket: Failed to generate ticket number", ephemeral=True)
                return None

            logger.info(f"Generated ticket number: {ticket_number}")

            channel_name = f"ticket-{ticket_number}"
            logger.info(f"Generated channel name: {channel_name}")

            staff_role = discord.utils.get(interaction.guild.roles, name="Staff")
            admin_role = discord.utils.get(interaction.guild.roles, name="Admin")

            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            ticket_channel = await category_channel.create_text_channel(
                name=channel_name,
                overwrites=overwrites
            )
            logger.info(f"Created ticket channel: {ticket_channel.name}")

            # Custom welcome message
            welcome_embed = discord.Embed(
                title="Welcome to the LegitPixel Support Server",
                description=(
                    "Thank you for contacting LegitPixel Support. Our team is here to assist you with any questions or issues you may have. We are committed to providing helpful, timely, and professional support.\n\n"
                    "Please note that during busy periods, responses may take longer than usual. If you've been waiting for more than 2 hours, kindly use the Call for Help button instead of tagging staff directly.\n\n"
                    "Please describe your issue below, and a team member will assist you as soon as possible.\n\n"
                    "Once your issue has been resolved, you will receive a message to rate your support experience. Your feedback helps us improve our service."
                ),
                color=discord.Color.from_rgb(88, 101, 242)
            )
            
            # Set the new image at the top
            welcome_embed.set_image(url="https://media.discordapp.net/attachments/1392181720651927662/1396951921281077330/Picsart_25-07-21_23-17-00-620.png?ex=68809d1c&is=687f4b9c&hm=939d0e939dedb62b47f36161aec06dac4ec53ddde3701e0e9bbf00286376b884&=&format=webp&quality=lossless&width=1317&height=327")
            
            # Add user avatar as thumbnail
            welcome_embed.set_thumbnail(url=interaction.user.display_avatar.url)

            controls = self.TicketControls(self.bot, ticket_number, interaction.user)
            control_message = await ticket_channel.send(
                embed=welcome_embed,
                view=controls
            )
            # Store message reference for timeout handling
            controls.message = control_message

            # Store ticket information
            stored = storage.create_ticket(
                ticket_number=ticket_number,  # Now guaranteed to be a string
                user_id=str(interaction.user.id),
                channel_id=str(ticket_channel.id),
                category=category,
                details=details or ""  # Ensure details is never None
            )
            logger.info(f"[DEBUG] Ticket {ticket_number} stored with details: {details}")

            await interaction.followup.send(
                embed=discord.Embed(
                    title="✨ Ticket Created",
                    description=f"Your ticket has been created in {ticket_channel.mention}",
                    color=discord.Color.green()
                ),
                ephemeral=True
            )

            logger.info(f"Ticket creation completed for user {interaction.user.name}")
            return ticket_channel

        except Exception as e:
            logger.error(f"Error creating ticket channel: {str(e)}")
            import traceback
            logger.error(f"Full error traceback: {traceback.format_exc()}")

            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error",
                    description="An error occurred while creating the ticket. Please try again or contact an administrator.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return None

    class TicketControls(discord.ui.View):
        def __init__(self, bot, ticket_number: str, user: discord.User):
            super().__init__(timeout=86400)  # Set 24 hour timeout
            self.bot = bot
            self.ticket_number = ticket_number
            self.user = user
            self.claimed_by = None
            self.message: Optional[discord.Message] = None
            logger.info(f"Initializing TicketControls for ticket {ticket_number}")

        async def on_timeout(self) -> None:  # Add return type annotation
            try:
                logger.info("TicketControls timeout triggered - refreshing view")

                if not isinstance(self.message, discord.Message):
                    logger.error("Invalid message reference in TicketControls")
                    return

                # Use self.__class__ to avoid TicketControls reference error
                new_view = self.__class__(self.bot)
                await self.message.edit(view=new_view)
                logger.info("Successfully refreshed TicketControls view after timeout")
            except Exception as e:
                logger.error(f"Error refreshing TicketControls view after timeout: {e}")

        async def parse_ticket_channel(self, channel_name: str, context: str = "Unknown") -> tuple[str, str]:
            return await self.bot.get_cog('TicketCommands').parse_ticket_channel(channel_name, context)

        

        @discord.ui.button(label="📞 Call for help!", style=discord.ButtonStyle.red, custom_id="call_help", row=0)
        async def call_help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                # Only ticket creator can call for help
                if interaction.user != self.user:
                    await interaction.response.send_message(
                        "Only the ticket creator can call for help!",
                        ephemeral=True
                    )
                    return

                # Check if the user has already called for help in the last 2 hours
                last_called = storage.get_last_call_for_help(self.ticket_number)
                if last_called:
                    import datetime
                    time_difference = datetime.datetime.utcnow() - last_called
                    if time_difference < datetime.timedelta(hours=2):
                        remaining_time = datetime.timedelta(hours=2) - time_difference
                        minutes, seconds = divmod(remaining_time.seconds, 60)
                        hours, minutes = divmod(minutes, 60)
                        await interaction.response.send_message(
                            f"You can only call for help every 2 hours. Please wait {hours} hours, {minutes} minutes, and {seconds} seconds.",
                            ephemeral=True
                        )
                        return

                staff_role = discord.utils.get(interaction.guild.roles, name="Staff")
                if staff_role:
                    ping_embed = discord.Embed(
                        title="🚨 Help Requested",
                        description=f"{interaction.user.mention} has requested urgent help in this ticket!",
                        color=discord.Color.red()
                    )
                    await interaction.channel.send(content=f"{staff_role.mention}", embed=ping_embed)
                    
                    # Disable the button after use
                    button.disabled = True
                    await interaction.response.edit_message(view=self)
                    
                    await interaction.followup.send("Staff has been notified!", ephemeral=True)

                    # Store the time the user called for help
                    storage.store_last_call_for_help(self.ticket_number, datetime.datetime.utcnow())

            except Exception as e:
                logger.error(f"Error in call help button: {e}")
                await interaction.response.send_message("An error occurred.", ephemeral=True)

        @discord.ui.button(label="🎫 Get ticket and start helping", style=discord.ButtonStyle.green, custom_id="claim_ticket", row=0)
        async def claim_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                # Check if user has staff permissions
                has_permission = False
                required_roles = ["Staff", "Ticket Support", "Ticket Admin", "Admin"]

                for role in interaction.user.roles:
                    if role.name in required_roles:
                        has_permission = True
                        break

                if not has_permission:
                    await interaction.response.send_message(
                        "You don't have permission to claim tickets!",
                        ephemeral=True
                    )
                    return

                if self.claimed_by is None:
                    # Claim the ticket
                    self.claimed_by = interaction.user
                    button.label = "🔓 Unclaim"
                    button.style = discord.ButtonStyle.red
                    storage.claim_ticket(self.ticket_number, interaction.user.name)

                    # Update delete button to close button
                    for item in self.children:
                        if hasattr(item, 'custom_id') and item.custom_id == "delete":
                            item.label = "🔒 Close ticket"
                            break

                    await interaction.response.edit_message(view=self)
                    # Random claim messages
                    import random
                    claim_messages = [
                        f"{self.user.mention} don't fall for {interaction.user.mention}'s smooth typing — Flexxy sees everything",
                        f"{interaction.user.mention} is here to help, not steal hearts — back off, {self.user.mention}",
                        f"Flexxy said: {self.user.mention}, focus on the issue, not the rizz",
                        f"{self.user.mention} opened a support ticket and got emotionally supported by {interaction.user.mention}",
                        f"{interaction.user.mention} isn't your tech bae, {self.user.mention} — Flexxy already claimed them",
                        f"{self.user.mention} googled the issue, but found feelings instead — watch out",
                        f"{interaction.user.mention} helped with your problem and your heartbeat — but stay loyal to Flexxy",
                        f"Flexxy ain't running a dating sim — {self.user.mention} calm down",
                        f"{interaction.user.mention} pulled up with answers and unspoken game — dangerous combo",
                        f"{self.user.mention} don't get too cozy in this ticket, {interaction.user.mention} belongs to the network... and Flexxy",
                        f"{interaction.user.mention} said \"try restarting\" and {self.user.mention} fell in love",
                        f"{self.user.mention} this is a support ticket, not a fan club",
                        f"{interaction.user.mention} helped you and now you blushing — Flexxy disapproves",
                        f"{self.user.mention} opened a ticket, {interaction.user.mention} opened their heart — yikes",
                        f"{interaction.user.mention} showed up and {self.user.mention} forgot what they needed",
                        f"This ain't therapy, {self.user.mention} — stop trauma dumping on {interaction.user.mention}",
                        f"{interaction.user.mention} fixed your issue and your trust issues — impressive",
                        f"{self.user.mention} don't catch feelings, catch updates",
                        f"{interaction.user.mention} is not your emotional support staff — Flexxy keeps 'em busy",
                        f"Flexxy watching you flirt in a support ticket like: \"not again…\""
                    ]
                    random_message = random.choice(claim_messages)
                    await interaction.followup.send(random_message)

                else:
                    # Unclaim the ticket
                    if interaction.user == self.claimed_by or any(role.name == "Admin" for role in interaction.user.roles):
                        self.claimed_by = None
                        button.label = "🎫 Get ticket and start helping"
                        button.style = discord.ButtonStyle.green
                        storage.claim_ticket(self.ticket_number, "Unclaimed")

                        # Update close button back to delete button
                        for item in self.children:
                            if hasattr(item, 'custom_id') and item.custom_id == "delete":
                                item.label = "🗑️ Delete ticket"
                                break

                        await interaction.response.edit_message(view=self)
                        await interaction.followup.send("Ticket has been unclaimed.")
                    else:
                        await interaction.response.send_message(
                            "You cannot unclaim a ticket claimed by someone else!",
                            ephemeral=True
                        )

            except Exception as e:
                logger.error(f"Error in claim ticket button: {e}")
                await interaction.response.send_message("An error occurred.", ephemeral=True)

        

        @discord.ui.button(label="🔒 Close with Reason", style=discord.ButtonStyle.secondary, custom_id="close_reason", row=1)
        async def close_with_reason_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                # Permission check
                has_permission = False
                required_roles = ["Staff", "Ticket Support", "Ticket Admin", "Admin"]

                for role in interaction.user.roles:
                    if role.name in required_roles:
                        has_permission = True
                        break

                if not has_permission:
                    await interaction.response.send_message(
                        "You don't have permission to close tickets!",
                        ephemeral=True
                    )
                    return

                # Show modal for reason input
                modal = CloseReasonModal(self.bot, self.ticket_number, self.user)
                await interaction.response.send_modal(modal)

            except Exception as e:
                logger.error(f"Error in close with reason button: {e}")
                await interaction.response.send_message("An error occurred.", ephemeral=True)

        @discord.ui.button(label="🗑️ Delete ticket", style=discord.ButtonStyle.red, custom_id="delete", row=1)
        async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                # Permission check
                has_permission = False
                required_roles = ["Staff", "Ticket Support", "Ticket Admin", "Admin"]

                for role in interaction.user.roles:
                    if role.name in required_roles:
                        has_permission = True
                        break

                if not has_permission:
                    await interaction.response.send_message(
                        "You don't have permission to delete tickets!",
                        ephemeral=True
                    )
                    return

                await interaction.response.send_message("Creating transcript and closing ticket...", ephemeral=True)
                
                # Create transcript
                await self.create_and_send_transcript(interaction, "Manual closure by staff")
                
                # Delete the channel after transcript is sent
                await asyncio.sleep(3)
                await interaction.channel.delete()

            except Exception as e:
                logger.error(f"Error in delete button: {e}")
                await interaction.response.send_message("An error occurred.", ephemeral=True)

        async def create_and_send_transcript(self, interaction: discord.Interaction, closing_reason: str = "Ticket closed"):
            try:
                # Create transcript file
                transcript_content = f"Ticket {self.ticket_number} Transcript\n"
                transcript_content += f"Created by: {self.user.display_name} ({self.user.id})\n"
                transcript_content += f"Closed by: {interaction.user.display_name} ({interaction.user.id})\n"
                transcript_content += f"Closing reason: {closing_reason}\n"
                transcript_content += f"Created at: {interaction.channel.created_at}\n"
                transcript_content += f"Closed at: {interaction.created_at}\n"
                transcript_content += "=" * 50 + "\n\n"
                
                # Get messages from channel
                messages = []
                async for message in interaction.channel.history(limit=None, oldest_first=True):
                    if not message.author.bot or message.embeds:  # Include bot messages with embeds
                        timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        content = message.content or "[Embed/File]"
                        transcript_content += f"[{timestamp}] {message.author.display_name}: {content}\n"
                
                # Save transcript file
                transcript_filename = f"transcripts/ticket_{self.ticket_number}.txt"
                import os
                os.makedirs("transcripts", exist_ok=True)
                
                with open(transcript_filename, "w", encoding="utf-8") as f:
                    f.write(transcript_content)
                
                # Send transcript to user
                transcript_embed = discord.Embed(
                    title=f"Here's the Ticket {self.ticket_number} transcript",
                    description=(
                        f"{self.user.mention}, if you had something important in your ticket or you have faced "
                        f"with some problems while getting help from our Staff, use this transcript which contains "
                        f"of every single message which was sent there.\n\n"
                        f"Ticket closing reason: {closing_reason}"
                    ),
                    color=discord.Color.green()
                )
                
                try:
                    with open(transcript_filename, 'rb') as f:
                        file = discord.File(f, filename=f"ticket_{self.ticket_number}_transcript.txt")
                        await self.user.send(embed=transcript_embed, file=file)
                except discord.Forbidden:
                    logger.warning(f"Could not send transcript to {self.user.display_name}")
                
                # Send transcript to transcript channel (placeholder for channel ID)
                transcript_channel_id = "TRANSCRIPT_CHANNEL_ID_PLACEHOLDER"  # Replace with actual channel ID
                try:
                    transcript_channel = interaction.guild.get_channel(int(transcript_channel_id)) if transcript_channel_id != "TRANSCRIPT_CHANNEL_ID_PLACEHOLDER" else None
                    if transcript_channel:
                        with open(transcript_filename, 'rb') as f:
                            file = discord.File(f, filename=f"ticket_{self.ticket_number}_transcript.txt")
                            await transcript_channel.send(embed=transcript_embed, file=file)
                except Exception as e:
                    logger.error(f"Could not send transcript to channel: {e}")
                
                # Send feedback request
                await self.send_feedback_request(interaction.user)
                
            except Exception as e:
                logger.error(f"Error creating transcript: {e}")

        async def send_feedback_request(self, closer: discord.User):
            try:
                feedback_embed = discord.Embed(
                    title="How do you rate our help?",
                    description=(
                        f"{self.user.mention}, recently you were contacting Staff by creating a ticket with "
                        f"ID {self.ticket_number} on LegitPixel Support Server. How would you rate the help of {closer.mention}?\n\n"
                        "You have 24 hours to give a review.\n"
                        "Thank you for contacting us!"
                    ),
                    color=discord.Color.blue()
                )
                feedback_embed.set_thumbnail(url=self.user.display_avatar.url)

                # Create rating buttons
                feedback_view = discord.ui.View(timeout=86400)  # 24 hours
                for i in range(1, 6):
                    feedback_view.add_item(StarRatingButton(i))

                # Send DM to user
                try:
                    await self.user.send(embed=feedback_embed, view=feedback_view)
                except discord.Forbidden:
                    logger.warning(f"Could not send feedback request to {self.user.display_name}")
                    
            except Exception as e:
                logger.error(f"Error sending feedback request: {e}")

        async def send_feedback_and_transcript(self, creator: discord.User, closer: discord.User, transcript_file: str):
            try:
                # Send feedback request
                feedback_embed = discord.Embed(
                    title="How do you rate our help?",
                    description=(
                        f"{creator.mention}, recently you were contacting Staff by creating a ticket with "
                        f"ID {self.ticket_number} on LegitPixel Support Server. How would you rate the help of {closer.mention}?\n\n"
                        "You have 24 hours to give a review.\n"
                        "Thank you for contacting us!"
                    ),
                    color=discord.Color.blue()
                )
                feedback_embed.set_thumbnail(url=creator.display_avatar.url)

                # Create rating buttons
                feedback_view = discord.ui.View(timeout=86400)  # 24 hours
                for i in range(1, 6):
                    feedback_view.add_item(StarRatingButton(i))

                # Send DM to user
                try:
                    await creator.send(embed=feedback_embed, view=feedback_view)
                except discord.Forbidden:
                    logger.warning(f"Could not send DM to {creator.display_name}")

                # Send transcript
                transcript_embed = discord.Embed(
                    title=f"Here's the Ticket {self.ticket_number} transcript",
                    description=(
                        f"{creator.mention}, if you had something important in your ticket or you have faced "
                        f"with some problems while getting help from our Staff, use this transcript which contains "
                        f"of every single message which was sent there.\n\n"
                        f"Ticket was closed by {closer.mention}\n"
                        f"Open the link to see the transcript."
                    ),
                    color=discord.Color.green()
                )

                try:
                    with open(transcript_file, 'rb') as f:
                        file = discord.File(f, filename=f"ticket_{self.ticket_number}_transcript.txt")
                        await creator.send(embed=transcript_embed, file=file)
                except discord.Forbidden:
                    logger.warning(f"Could not send transcript to {creator.display_name}")

            except Exception as e:
                logger.error(f"Error sending feedback and transcript: {e}")

        class FeedbackView(discord.ui.View):
            def __init__(self, ticket_name: str):
                super().__init__()
                self.ticket_name = ticket_name
                self.feedback_sent = False

                for i in range(1, 6):
                    button = StarRatingButton(rating=i)
                    self.add_item(button)

async def setup(bot):
    await bot.add_cog(TicketCommands(bot))