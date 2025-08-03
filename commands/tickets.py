import discord
from discord.ext import commands
from discord import app_commands
from utils import permissions, storage, responses
import logging
import asyncio
from typing import Optional

logger = logging.getLogger('discord')

class DungeonCarryForm(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="🏰 Dungeon Carry Request")
        self.bot = bot

        self.ingame_name = discord.ui.TextInput(
            label="What's your In-Game Name?",
            style=discord.TextStyle.short,
            placeholder="Enter your Minecraft username...",
            required=True,
            max_length=16
        )

        self.dungeon_floor = discord.ui.TextInput(
            label="Which dungeon floor carry you wanna purchase?",
            style=discord.TextStyle.short,
            placeholder="e.g., Floor 7, Master 5, etc...",
            required=True,
            max_length=50
        )

        self.quantity = discord.ui.TextInput(
            label="How much carries you want? (Quantity)",
            style=discord.TextStyle.short,
            placeholder="Enter number of carries...",
            required=True,
            max_length=10
        )

        self.additional_notes = discord.ui.TextInput(
            label="Any additional note? (Not required)",
            style=discord.TextStyle.paragraph,
            placeholder="Any special requirements or notes...",
            required=False,
            max_length=500
        )

        self.add_item(self.ingame_name)
        self.add_item(self.dungeon_floor)
        self.add_item(self.quantity)
        self.add_item(self.additional_notes)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Create the details string
            details = (
                f"**🏰 Dungeon Carry Request**\n"
                f"**In-Game Name:** {self.ingame_name.value}\n"
                f"**Dungeon Floor:** {self.dungeon_floor.value}\n"
                f"**Quantity:** {self.quantity.value}\n"
                f"**Additional Notes:** {self.additional_notes.value or 'None'}"
            )

            ticket_commands = self.bot.get_cog('TicketCommands')
            if ticket_commands:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Creating Dungeon Carry Ticket",
                        description="Your ticket is being created...",
                        color=discord.Color.blue()
                    ),
                    ephemeral=True
                )
                await ticket_commands.create_ticket_channel(interaction, "Dungeon Carry", details)
            else:
                await interaction.response.send_message(
                    "An error occurred while creating the ticket.",
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Error in DungeonCarryForm submission: {e}")
            await interaction.response.send_message(
                "An error occurred while processing your request.",
                ephemeral=True
            )

class SlayerCarryForm(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="⚔️ Slayer Carry Request")
        self.bot = bot

        self.ingame_name = discord.ui.TextInput(
            label="What's your In-Game Name?",
            style=discord.TextStyle.short,
            placeholder="Enter your Minecraft username...",
            required=True,
            max_length=16
        )

        self.slayer_type = discord.ui.TextInput(
            label="Which slayer you wanna purchase?",
            style=discord.TextStyle.short,
            placeholder="e.g., Revenant Horror, Tarantula Broodfather, etc...",
            required=True,
            max_length=50
        )

        self.tier = discord.ui.TextInput(
            label="Which tier you wanna purchase?",
            style=discord.TextStyle.short,
            placeholder="e.g., Tier 1, Tier 4, etc...",
            required=True,
            max_length=20
        )

        self.quantity = discord.ui.TextInput(
            label="How much carries you want? (Quantity)",
            style=discord.TextStyle.short,
            placeholder="Enter number of carries...",
            required=True,
            max_length=10
        )

        self.additional_notes = discord.ui.TextInput(
            label="Any additional note? (Not required)",
            style=discord.TextStyle.paragraph,
            placeholder="Any special requirements or notes...",
            required=False,
            max_length=500
        )

        self.add_item(self.ingame_name)
        self.add_item(self.slayer_type)
        self.add_item(self.tier)
        self.add_item(self.quantity)
        self.add_item(self.additional_notes)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Create the details string
            details = (
                f"**⚔️ Slayer Carry Request**\n"
                f"**In-Game Name:** {self.ingame_name.value}\n"
                f"**Slayer Type:** {self.slayer_type.value}\n"
                f"**Tier:** {self.tier.value}\n"
                f"**Quantity:** {self.quantity.value}\n"
                f"**Additional Notes:** {self.additional_notes.value or 'None'}"
            )

            ticket_commands = self.bot.get_cog('TicketCommands')
            if ticket_commands:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Creating Slayer Carry Ticket",
                        description="Your ticket is being created...",
                        color=discord.Color.blue()
                    ),
                    ephemeral=True
                )
                await ticket_commands.create_ticket_channel(interaction, "Slayer Carry", details)
            else:
                await interaction.response.send_message(
                    "An error occurred while creating the ticket.",
                    ephemeral=True
                )
        except Exception as e:
            logger.error(f"Error in SlayerCarryForm submission: {e}")
            await interaction.response.send_message(
                "An error occurred while processing your request.",
                ephemeral=True
            )

class PrioritySelectView(discord.ui.View):
    def __init__(self, bot, ticket_number: str):
        super().__init__(timeout=300)  # 5 minute timeout
        self.bot = bot
        self.ticket_number = ticket_number

    @discord.ui.button(label="Low", style=discord.ButtonStyle.green, emoji="🟢", custom_id="low_priority_{ticket_number}")
    async def low_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_priority(interaction, "Low", "🟢")

    @discord.ui.button(label="Medium", style=discord.ButtonStyle.primary, emoji="🟡", custom_id="medium_priority_{ticket_number}")
    async def medium_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_priority(interaction, "Medium", "🟡")

    @discord.ui.button(label="High", style=discord.ButtonStyle.danger, emoji="🟠", custom_id="high_priority_{ticket_number}")
    async def high_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_priority(interaction, "High", "🟠")

    @discord.ui.button(label="Urgent", style=discord.ButtonStyle.danger, emoji="🔴", custom_id="urgent_priority_{ticket_number}")
    async def urgent_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_priority(interaction, "Urgent", "🔴")

    async def set_priority(self, interaction: discord.Interaction, priority: str, emoji: str):
        try:
            # Check if priority has already been set for this ticket
            existing_priority = storage.get_ticket_priority(self.ticket_number)
            if existing_priority:
                await interaction.response.send_message(
                    f"Priority has already been set for this ticket to **{existing_priority}**. Priority can only be selected once per ticket.",
                    ephemeral=True
                )
                return

            # Respond to interaction immediately to prevent timeout
            await interaction.response.send_message(
                f"Setting priority to **{priority}** {emoji}...",
                ephemeral=True
            )

            # Store the priority
            storage.set_ticket_priority(self.ticket_number, priority)
            
            # Disable all priority buttons after selection
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
            
            # Update the message with disabled buttons
            try:
                await interaction.edit_original_response(
                    content=f"Priority set to **{priority}** {emoji}",
                    view=self
                )
            except Exception as e:
                logger.error(f"Error updating message with disabled buttons: {e}")
            
            priority_embed = discord.Embed(
                title=f"{emoji} Priority Set: {priority}",
                description=f"Ticket priority has been set to **{priority}** by {interaction.user.mention}",
                color=discord.Color.blue()
            )
            
            # Send to the ticket channel
            ticket_channel = None
            for channel in interaction.guild.channels:
                if channel.name == f"ticket-{self.ticket_number}" or channel.name.endswith(f"ticket-{self.ticket_number}"):
                    ticket_channel = channel
                    break
            
            if ticket_channel:
                await ticket_channel.send(embed=priority_embed)
                
                # Update ticket channel name with priority color
                new_channel_name = f"{emoji}ticket-{self.ticket_number}"
                try:
                    await ticket_channel.edit(name=new_channel_name)
                except Exception as e:
                    logger.error(f"Error updating channel name: {e}")
            
            # Send notification to priority history channel
            try:
                # Look for existing priority history channel
                priority_channel = discord.utils.get(interaction.guild.channels, name="priority-history")
                
                # Create the channel if it doesn't exist
                if not priority_channel:
                    try:
                        priority_channel = await interaction.guild.create_text_channel(
                            name="priority-history",
                            topic="Channel for tracking ticket priority changes"
                        )
                        logger.info("Created priority-history channel")
                    except Exception as e:
                        logger.error(f"Error creating priority-history channel: {e}")
                
                # Send notification if channel exists or was created
                if priority_channel:
                    # Get the Carriers role
                    carriers_role = discord.utils.get(interaction.guild.roles, id=1280539104832127008)
                    carriers_mention = f"<@&1280539104832127008>" if carriers_role else "@Carriers"
                    
                    # Create priority-specific message
                    if priority.lower() == "urgent":
                        priority_message = f"{carriers_mention} {interaction.user.mention} has set ticket-{self.ticket_number} priority to **{priority}** {emoji}. **URGENT ATTENTION REQUIRED!**"
                    elif priority.lower() == "high":
                        priority_message = f"{carriers_mention} {interaction.user.mention} has set ticket-{self.ticket_number} priority to **{priority}** {emoji}. **High priority assistance needed.**"
                    else:
                        priority_message = f"{carriers_mention} {interaction.user.mention} has set ticket-{self.ticket_number} priority to **{priority}** {emoji}."
                    
                    await priority_channel.send(priority_message)
                    
            except Exception as e:
                logger.error(f"Error sending priority notification: {e}")

        except discord.NotFound:
            logger.error(f"Interaction expired for priority setting on ticket {self.ticket_number}")
        except Exception as e:
            logger.error(f"Error setting priority: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("An error occurred while setting priority.", ephemeral=True)
                else:
                    await interaction.followup.send("An error occurred while setting priority.", ephemeral=True)
            except:
                pass

class FeedbackModal(discord.ui.Modal):
    def __init__(self, ticket_name: str, guild_id: int):
        super().__init__(title="Ticket Feedback & Rating")
        self.ticket_name = ticket_name
        self.guild_id = guild_id

        self.rating = discord.ui.TextInput(
            label="Rate your support experience (1-5 stars)",
            style=discord.TextStyle.short,
            placeholder="Enter a number from 1 to 5",
            required=True,
            min_length=1,
            max_length=1

        )

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

        self.add_item(self.rating)
        self.add_item(self.feedback)
        self.add_item(self.suggestions)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            logger.info(f"[DEBUG] Processing feedback submission for ticket {self.ticket_name}")

            # Validate rating input
            try:
                rating_value = int(self.rating.value)
                if rating_value < 1 or rating_value > 5:
                    raise ValueError("Rating must be between 1 and 5")
            except ValueError:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Invalid Rating",
                        description="Please enter a valid rating between 1 and 5.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return

            ticket_number = self.ticket_name if not self.ticket_name.startswith("ticket-") else self.ticket_name.split('-')[-1]
            
            # Get the guild using the bot instance
            guild = interaction.client.get_guild(self.guild_id)
            if not guild:
                await interaction.response.send_message("Guild not found.", ephemeral=True)
                return

            # Store the feedback
            stored = storage.store_feedback(
                ticket_name=ticket_number,
                user_id=str(interaction.user.id),
                rating=rating_value,
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
                rating=rating_value,
                feedback=self.feedback.value,
                suggestions=self.suggestions.value,
                claimed_by=claimed_by,
                closed_by=closed_by
            )

            # Send to feedback log channel
            feedback_channel_id = 1401276435439554580  # Feedback channel ID
            try:
                feedback_log_channel = guild.get_channel(feedback_channel_id)
                if feedback_log_channel:
                    await feedback_log_channel.send(embed=feedback_embed)
                else:
                    logger.error(f"Feedback channel {feedback_channel_id} not found")
            except Exception as e:
                logger.error(f"Could not send feedback to channel: {e}")

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

class FeedbackButton(discord.ui.Button):
    def __init__(self, ticket_number: str):
        super().__init__(
            style=discord.ButtonStyle.green,
            label="✨ Rate & Give Feedback",
            custom_id=f"feedback_{ticket_number}"
        )
        self.ticket_number = ticket_number

    async def callback(self, interaction: discord.Interaction):
        try:
            logger.info(f"[DEBUG] Opening feedback modal for ticket {self.ticket_number}")

            # Check if feedback already exists
            existing_feedback = storage.get_feedback(self.ticket_number)
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

            # Use the guild ID for FakePixel Giveaways
            guild_id = 1246452712653062175
            modal = FeedbackModal(
                ticket_name=self.ticket_number,
                guild_id=guild_id
            )
            await interaction.response.send_modal(modal)
            logger.info(f"[DEBUG] Opened feedback modal for ticket {self.ticket_number}")

        except Exception as e:
            logger.error(f"[DEBUG] Error opening feedback modal: {str(e)}")
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description="An error occurred while opening feedback form. Please try again.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

class TicketCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_categories = ['Dungeon Carry', 'Slayer Carry']
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
            carriers_role = discord.utils.get(interaction.guild.roles, id=1280539104832127008)

            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            if carriers_role:
                overwrites[carriers_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            ticket_channel = await category_channel.create_text_channel(
                name=channel_name,
                overwrites=overwrites
            )
            logger.info(f"Created ticket channel: {ticket_channel.name}")

            # Create welcome message for carry tickets - mention Carriers role
            carrier_role = discord.utils.get(interaction.guild.roles, id=1280539104832127008)
            carrier_mention = f"<@&1280539104832127008>" if carrier_role else "@Carriers (role not found)"
            
            # Format details nicely
            formatted_details = details.replace("**", "").replace("🏰 Dungeon Carry Request", "🏰 Dungeon Carry Request").replace("⚔️ Slayer Carry Request", "⚔️ Slayer Carry Request") if details else "No details provided"
            
            welcome_embed = discord.Embed(
                title=f" Welcome @{interaction.user.display_name}! Carriers will be with you shortly.",
                description=(
                    f"🏰 New {category} Request\n"
                    f"┌─────────────────────────────────┐\n"
                    f"│ Welcome to FxG Carry Service │\n"
                    f"└─────────────────────────────────┘\n\n"
                    f"🎯 Service Type: {category}\n"
                    f"🔖 Ticket ID: #{ticket_number}\n"
                    f"👤 Customer: @{interaction.user.display_name}\n\n"
                    f"📞 Next Steps:\n"
                    f"• One of our professional carriers will assist you shortly\n"
                    f"• Please provide any additional details if needed\n"
                    f"• Use priority settings only when absolutely necessary\n\n"
                    f"⏰ Estimated Response Time: 5-15 minutes\n\n"
                    f"📋 Service Details:\n"
                    f"{formatted_details}\n\n"
                    f"Fakepixel Giveaways Carry Service •"
                ),
                color=discord.Color.from_rgb(88, 101, 242)
            )

            # Set the new image at the top
            welcome_embed.set_image(url="https://media.discordapp.net/attachments/1250029348690464820/1401139089985634405/ChatGPT_Image_Aug_2_2025_05_44_48_AM.png?ex=688f2ff6&is=688dde76&hm=eb399c9e3f14002c638894af3e51e3b1cd35e9c8e85c4132e59c9ec56ebefaf5&=&format=webp&quality=lossless&width=1209&height=805")

            # Add user avatar as thumbnail
            welcome_embed.set_thumbnail(url=interaction.user.display_avatar.url)

            # Send role mention first
            await ticket_channel.send(f"{carrier_mention}")
            
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

            # Button will always be enabled and check cooldown when clicked

            logger.info(f"Initializing TicketControls for ticket {ticket_number}")

        def _update_call_help_button_state(self):
            """Update the call for help button state based on cooldown"""
            # Keep button always enabled - cooldown check will be done when clicked
            pass

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



        

        

        @discord.ui.button(label="Close", style=discord.ButtonStyle.red, custom_id="close", row=1)
        async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                # Permission check - only Carriers role and above can close tickets
                has_permission = False
                required_roles = ["Carriers", "Staff", "Ticket Support", "Ticket Admin", "Admin"]

                for role in interaction.user.roles:
                    if role.name in required_roles:
                        has_permission = True
                        break

                if not has_permission:
                    await interaction.response.send_message(
                        "Only Carriers and higher roles can close tickets!",
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
                  logger.error(f"Error in close ticket button: {e}")
                  await interaction.response.send_message("An error occurred.", ephemeral=True)

        # Priority select button
        @discord.ui.button(label="Priority Select", style=discord.ButtonStyle.grey, custom_id="priority_select", row=1)
        async def priority_select(self, interaction: discord.Interaction, button: discord.ui.Button):
            try:
                # Everyone can select priority
                priority_view = PrioritySelectView(self.bot, self.ticket_number)
                await interaction.response.send_message(
                    "Select the priority level for this ticket:",
                    view=priority_view,
                    ephemeral=True
                )

            except Exception as e:
                logger.error(f"Error in priority select button: {e}")
                await interaction.response.send_message("An error occurred.", ephemeral=True)

        #Only close button remains

        #@discord.ui.button(label="🔒 Close with Reason", style=discord.ButtonStyle.secondary, custom_id="close_reason", row=1)
        #async def close_with_reason_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        #    try:
        #        # Permission check
        #        has_permission = False
        #        required_roles = ["Staff", "Ticket Support", "Ticket Admin", "Admin"]

        #        for role in interaction.user.roles:
        #            if role.name in required_roles:
        #                has_permission = True
        #                break

        #        if not has_permission:
        #            await interaction.response.send_message(
        #                "You don't have permission to close tickets!",
        #                ephemeral=True
        #            )
        #            return

        #        # Show modal for reason input
        #        modal = CloseReasonModal(self.bot, self.ticket_number, self.user)
        #        await interaction.response.send_modal(modal)

        #    except Exception as e:
        #        logger.error(f"Error in close with reason button: {e}")
        #        await interaction.response.send_message("An error occurred.", ephemeral=True)

        #@discord.ui.button(label="🗑️ Delete ticket", style=discord.ButtonStyle.red, custom_id="delete", row=1)
        #async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        #    try:
        #        # Permission check
        #        has_permission = False
        #        required_roles = ["Staff", "Ticket Support", "Ticket Admin", "Admin"]

        #        for role in interaction.user.roles:
        #            if role.name in required_roles:
        #                has_permission = True
        #                break

        #        if not has_permission:
        #            await interaction.response.send_message(
        #                "You don't have permission to delete tickets!",
        #                ephemeral=True
        #            )
        #            return

        #        await interaction.response.send_message("Creating transcript and closing ticket...", ephemeral=True)

        #        # Create transcript
        #        await self.create_and_send_transcript(interaction, "Manual closure by staff")

        #        # Delete the channel after transcript is sent
        #        await asyncio.sleep(3)
        #        await interaction.channel.delete()

        #    except Exception as e:
        #        logger.error(f"Error in delete button: {e}")
        #        await interaction.response.send_message("An error occurred.", ephemeral=True)

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

                # Get messages from channel and store for web portal
                messages = []
                web_messages = []
                async for message in interaction.channel.history(limit=None, oldest_first=True):
                    if not message.author.bot or message.embeds:  # Include bot messages with embeds
                        timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        content = message.content or "[Embed/File]"
                        transcript_content += f"[{timestamp}] {message.author.display_name}: {content}\n"
                        
                        # Store for web portal
                        web_messages.append({
                            "author": message.author.display_name,
                            "content": content,
                            "timestamp": timestamp
                        })

                # Save transcript file
                transcript_filename = f"transcripts/ticket_{self.ticket_number}.txt"
                import os
                os.makedirs("transcripts", exist_ok=True)

                with open(transcript_filename, "w", encoding="utf-8") as f:
                    f.write(transcript_content)

                # Store web transcript data
                await self.store_web_transcript(web_messages, closing_reason, interaction)

                # Send transcript to user
                transcript_embed = discord.Embed(
                    title=f"FakePixel Carrier Service - Ticket #{self.ticket_number} Transcript",
                    description=(
                        f"{self.user.mention}, if you had something important in your ticket or you have faced "
                        f"with some problems while getting help from our Staff, use this transcript which contains "
                        f"of every single message which was sent there.\n\n"
                        f"Ticket closing reason: {closing_reason}\n\n"
                        f"Thank you for choosing FakePixel Carrier Service!"
                    ),
                    color=discord.Color.from_rgb(88, 101, 242)
                )
                transcript_embed.set_image(url="https://media.discordapp.net/attachments/1250029348690464820/1401226777485119529/ChatGPT_Image_Aug_2_2025_11_34_17_AM.png?ex=688f81a1&is=688e3021&hm=c5cc9782fd8c48a43d3f45fa62ef293a62fd6847c996be0714d57dbfc053d0d6&=&format=webp&quality=lossless&width=1208&height=805")

                try:
                    with open(transcript_filename, 'rb') as f:
                        file = discord.File(f, filename=f"ticket_{self.ticket_number}_transcript.txt")
                        await self.user.send(embed=transcript_embed, file=file)
                except discord.Forbidden:
                    logger.warning(f"Could not send transcript to {self.user.display_name}")

                # Send transcript to transcript channel
                transcript_channel_id = "1282718429161197600"  # Updated transcript channel ID
                try:
                    transcript_channel = interaction.guild.get_channel(int(transcript_channel_id))
                    if transcript_channel:
                        # Create a separate embed for the transcript channel
                        channel_transcript_embed = discord.Embed(
                            title=f"FakePixel Carrier Service - Ticket #{self.ticket_number} Transcript",
                            description=(
                                f"Ticket created by: {self.user.mention}\n"
                                f"Closed by: {interaction.user.mention}\n"
                                f"Closing reason: {closing_reason}"
                            ),
                            color=discord.Color.from_rgb(88, 101, 242)
                        )
                        channel_transcript_embed.set_image(url="https://media.discordapp.net/attachments/1250029348690464820/1401226777485119529/ChatGPT_Image_Aug_2_2025_11_34_17_AM.png?ex=688f81a1&is=688e3021&hm=c5cc9782fd8c48a43d3f45fa62ef293a62fd6847c996be0714d57dbfc053d0d6&=&format=webp&quality=lossless&width=1208&height=805")
                        
                        with open(transcript_filename, 'rb') as f:
                            file = discord.File(f, filename=f"ticket_{self.ticket_number}_transcript.txt")
                            await transcript_channel.send(embed=channel_transcript_embed, file=file)
                except Exception as e:
                    logger.error(f"Could not send transcript to channel: {e}")

                # Send feedback request
                await self.send_feedback_request(interaction.user)

            except Exception as e:
                logger.error(f"Error creating transcript: {e}")

        async def store_web_transcript(self, messages, closing_reason, interaction):
            """Store transcript data via MongoDB API"""
            try:
                import requests
                from datetime import datetime
                
                # Get ticket details from storage
                ticket_info = storage.tickets.get(self.ticket_number, {})
                claimed_by = storage.get_ticket_claimed_by(self.ticket_number)
                
                transcript_data = {
                    "ticket_number": self.ticket_number,
                    "user_id": str(self.user.id),
                    "category": ticket_info.get('category', 'Unknown'),
                    "status": "Closed",
                    "created_at": ticket_info.get('created_at', datetime.utcnow().isoformat()),
                    "closed_at": datetime.utcnow().isoformat(),
                    "closed_by": interaction.user.display_name,
                    "closing_reason": closing_reason,
                    "messages": messages,
                    "details": ticket_info.get('details', ''),
                    "claimed_by": claimed_by
                }
                
                # Send to MongoDB API
                try:
                    response = requests.post(
                        'http://localhost:8000/api/transcripts',
                        json=transcript_data,
                        timeout=10
                    )
                    
                    if response.status_code == 201:
                        logger.info(f"Successfully saved transcript for ticket {self.ticket_number} to MongoDB")
                    else:
                        logger.error(f"Failed to save transcript to MongoDB: {response.status_code} - {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error connecting to MongoDB API: {e}")
                    # Fallback to local storage if API is unavailable
                    await self.fallback_store_transcript(transcript_data)
                    
            except Exception as e:
                logger.error(f"Error storing web transcript: {e}")

        async def fallback_store_transcript(self, transcript_data):
            """Fallback method to store transcript locally if API is unavailable"""
            try:
                import json
                import os
                
                os.makedirs("data", exist_ok=True)
                transcript_file = "data/web_transcripts.json"
                
                web_transcripts = []
                if os.path.exists(transcript_file):
                    with open(transcript_file, 'r') as f:
                        web_transcripts = json.load(f)
                
                # Convert to old format for compatibility
                fallback_data = {
                    "number": transcript_data["ticket_number"],
                    "user_id": transcript_data["user_id"],
                    "category": transcript_data["category"],
                    "status": transcript_data["status"],
                    "created_at": transcript_data["created_at"],
                    "closed_at": transcript_data["closed_at"],
                    "closed_by": transcript_data["closed_by"],
                    "closing_reason": transcript_data["closing_reason"],
                    "messages": transcript_data["messages"],
                    "date": transcript_data["closed_at"]
                }
                
                web_transcripts.append(fallback_data)
                
                with open(transcript_file, 'w') as f:
                    json.dump(web_transcripts, f, indent=2)
                    
                logger.info(f"Stored transcript as fallback for ticket {transcript_data['ticket_number']}")
                
            except Exception as e:
                logger.error(f"Error in fallback transcript storage: {e}")
                
                # Add new transcript
                web_transcripts.append(web_transcript)
                
                # Save updated transcripts
                with open(transcript_file, 'w') as f:
                    json.dump(web_transcripts, f, indent=2)
                
                logger.info(f"Stored web transcript for ticket {self.ticket_number}")
                
            except Exception as e:
                logger.error(f"Error storing web transcript: {e}")

        async def send_feedback_request(self, closer: discord.User):
            try:
                feedback_embed = discord.Embed(
                    title="Rate & Give Feedback",
                    description=(
                        f"{self.user.mention}, recently you were contacting Staff by creating a ticket with "
                        f"ID {self.ticket_number} on FakePixel Giveaways. How would you rate the help of {closer.mention}?\n\n"
                        "You have 24 hours to give a review.\n"
                        "Thank you for contacting us!"
                    ),
                    color=discord.Color.blue()
                )
                feedback_embed.set_thumbnail(url=self.user.display_avatar.url)

                # Create single feedback button
                feedback_view = discord.ui.View(timeout=86400)  # 24 hours
                feedback_view.add_item(FeedbackButton(self.ticket_number))

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
                        f"ID {self.ticket_number} on FakePixel Giveaways. How would you rate the help of {closer.mention}?\n\n"
                        "You have 24 hours to give a review.\n"
                        "Thank you for contacting us!"
                    ),
                    color=discord.Color.blue()
                )
                feedback_embed.set_thumbnail(url=creator.display_avatar.url)

                # Create single feedback button
                feedback_view = discord.ui.View(timeout=86400)  # 24 hours
                feedback_view.add_item(FeedbackButton(self.ticket_number))

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