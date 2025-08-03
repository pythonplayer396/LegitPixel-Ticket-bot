import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger('discord')

class CarrySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.points_file = "data/carry_points.json"
        self.pending_file = "data/pending_carries.json"

        # Points matrix
        self.dungeon_points = {
            "entrance": {"s": 1, "s+": 2},
            "f1": {"s": 2, "s+": 3},
            "f2": {"s": 3, "s+": 4},
            "f3": {"s": 4, "s+": 5},
            "f4": {"s": 5, "s+": 6},
            "f5": {"s": 6, "s+": 8},
            "f6": {"s": 10, "s+": 16},
            "f7": {"s": 12, "s+": 20},
            "m1": {"s": 14, "s+": 22},
            "m2": {"s": 16, "s+": 24},
            "m3": {"s": 18, "s+": 26},
            "m4": {"s": 20, "s+": 28},
            "m5": {"s": 22, "s+": 30},
            "m6": {"s": 24, "s+": 32},
            "m7": {"s": 28, "s+": 36}
        }

        self.slayer_points = {
            "revenant": {"t4": {"s": 5, "s+": 7}},
            "tarantula": {"t4": {"s": 5, "s+": 7}},
            "sven": {"t4": {"s": 6, "s+": 8}},
            "voidgloom": {"t3": {"s": 8, "s+": 10}, "t4": {"s": 12, "s+": 16}},
            "blaze": {"t2": {"s": 10, "s+": 14}, "t3": {"s": 16, "s+": 20}, "t4": {"s": 20, "s+": 26}}
        }

        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

        # Initialize JSON files if they don't exist
        self.initialize_data_files()

    def initialize_data_files(self):
        """Initialize JSON data files if they don't exist"""
        try:
            # Initialize points file
            if not os.path.exists(self.points_file):
                with open(self.points_file, 'w') as f:
                    json.dump({}, f, indent=2)
                logger.info("Created carry_points.json file")

            # Initialize pending carries file
            if not os.path.exists(self.pending_file):
                with open(self.pending_file, 'w') as f:
                    json.dump({}, f, indent=2)
                logger.info("Created pending_carries.json file")

        except Exception as e:
            logger.error(f"Error initializing data files: {e}")

    def load_points(self) -> Dict[str, int]:
        """Load points data from file"""
        try:
            if os.path.exists(self.points_file):
                with open(self.points_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading points: {e}")
            return {}

    def save_points(self, points_data: Dict[str, int]):
        """Save points data to file"""
        try:
            with open(self.points_file, 'w') as f:
                json.dump(points_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving points: {e}")

    def load_pending(self) -> Dict[str, Any]:
        """Load pending carries from file"""
        try:
            if os.path.exists(self.pending_file):
                with open(self.pending_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading pending carries: {e}")
            return {}

    def save_pending(self, pending_data: Dict[str, Any]):
        """Save pending carries to file"""
        try:
            with open(self.pending_file, 'w') as f:
                json.dump(pending_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving pending carries: {e}")

    def calculate_points(self, carry_type: str, floor_or_tier: str, grade: str, runs: int) -> int:
        """Calculate points based on carry type, floor/tier, grade, and number of runs"""
        try:
            if carry_type.lower() == "dungeon":
                base_points = self.dungeon_points.get(floor_or_tier.lower(), {}).get(grade.lower(), 0)
            elif carry_type.lower() == "slayer":
                # For slayer, format should be "slayer_type tier" like "voidgloom t4"
                parts = floor_or_tier.lower().split()
                if len(parts) >= 2:
                    slayer_type = parts[0]
                    tier = parts[1]
                else:
                    # Try with underscore format
                    parts = floor_or_tier.lower().split('_')
                    if len(parts) >= 2:
                        slayer_type = parts[0]
                        tier = parts[1]
                    else:
                        return 0

                base_points = self.slayer_points.get(slayer_type, {}).get(tier, {}).get(grade.lower(), 0)
            else:
                base_points = 0

            return base_points * runs
        except Exception as e:
            logger.error(f"Error calculating points: {e}")
            return 0

    def get_valid_options(self, carry_type: str) -> str:
        """Get valid options for floor_or_tier based on carry type"""
        if carry_type.lower() == "dungeon":
            return "entrance, f1-f7, m1-m7"
        elif carry_type.lower() == "slayer":
            return "revenant t4, tarantula t4, sven t4, voidgloom t3/t4, blaze t2/t3/t4"
        return "Unknown carry type"

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
            # Validate inputs
            if carry_type.lower() not in ["dungeon", "slayer"]:
                await interaction.response.send_message("Invalid carry type. Use 'dungeon' or 'slayer'.", ephemeral=True)
                return

            if grade.lower() not in ["s", "s+"]:
                await interaction.response.send_message("Invalid grade. Use 's' or 's+'.", ephemeral=True)
                return

            if number_of_runs <= 0:
                await interaction.response.send_message("Number of runs must be positive.", ephemeral=True)
                return

            # Calculate points
            points = self.calculate_points(carry_type, floor_or_tier, grade, number_of_runs)

            if points == 0:
                valid_options = self.get_valid_options(carry_type)
                await interaction.response.send_message(
                    f"Invalid floor/tier for {carry_type}. Valid options: {valid_options}\n"
                    f"For slayers, use format: 'slayer_name tier' (e.g., 'voidgloom t4')",
                    ephemeral=True
                )
                return

            # Find approval channel
            approval_channel = discord.utils.get(interaction.guild.channels, name="approve-request")
            if not approval_channel:
                await interaction.response.send_message("Approval channel #approve-request not found.", ephemeral=True)
                return

            # Create unique ID for this carry request
            import time
            carry_id = str(int(time.time() * 1000))

            # Store pending carry
            pending_data = self.load_pending()
            pending_data[carry_id] = {
                "staff_id": str(staff.id),
                "staff_name": staff.display_name,
                "user_carried_id": str(user_carried.id),
                "user_carried_name": user_carried.display_name,
                "requester_id": str(interaction.user.id),
                "requester_name": interaction.user.display_name,
                "runs": number_of_runs,
                "carry_type": carry_type.lower(),
                "floor_or_tier": floor_or_tier.lower(),
                "grade": grade.lower(),
                "points": points,
                "timestamp": time.time()
            }
            self.save_pending(pending_data)

            # Create approval embed
            embed = discord.Embed(
                title="🎯 Carry Approval Request",
                color=discord.Color.orange()
            )
            embed.add_field(name="Staff Member", value=staff.mention, inline=True)
            embed.add_field(name="User Carried", value=user_carried.mention, inline=True)
            embed.add_field(name="Requested by", value=interaction.user.mention, inline=True)
            embed.add_field(name="Number of Runs", value=str(number_of_runs), inline=True)
            embed.add_field(name="Carry Type", value=carry_type.title(), inline=True)
            embed.add_field(name="Floor/Tier", value=floor_or_tier.upper(), inline=True)
            embed.add_field(name="Grade", value=grade.upper(), inline=True)
            embed.add_field(name="Total Points", value=str(points), inline=True)
            embed.set_footer(text=f"Request ID: {carry_id}")

            # Create approval view
            view = CarryApprovalView(carry_id, self)

            # Send to approval channel
            await approval_channel.send(embed=embed, view=view)

            await interaction.response.send_message(
                f"Carry request submitted for approval. Points to be awarded: {points}",
                ephemeral=True
            )

            logger.info(f"Carry request submitted by {interaction.user.name} for {staff.name}: {points} points")

        except Exception as e:
            logger.error(f"Error in carried command: {e}")
            await interaction.response.send_message("An error occurred while processing the carry request.", ephemeral=True)

    async def points(self, interaction: discord.Interaction, staff: discord.Member):
        """View total points for a staff member"""
        try:
            points_data = self.load_points()
            total_points = points_data.get(str(staff.id), 0)

            embed = discord.Embed(
                title="📊 Carry Points",
                description=f"{staff.mention} has **{total_points}** total approved points.",
                color=discord.Color.blue()
            )
            
            # Handle avatar URL safely
            try:
                embed.set_thumbnail(url=staff.display_avatar.url)
            except Exception as avatar_error:
                logger.warning(f"Could not set avatar for {staff.display_name}: {avatar_error}")

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error in points command: {e}")
            await interaction.response.send_message("An error occurred while retrieving points.", ephemeral=True)

    async def leaderboard(self, interaction: discord.Interaction):
        """Display carry points leaderboard"""
        try:
            points_data = self.load_points()

            if not points_data:
                await interaction.response.send_message("No carry points recorded yet.", ephemeral=True)
                return

            # Sort by points (descending)
            sorted_points = sorted(points_data.items(), key=lambda x: x[1], reverse=True)

            embed = discord.Embed(
                title="🏆 Carry Points Leaderboard",
                color=discord.Color.gold()
            )

            leaderboard_text = ""
            for i, (user_id, points) in enumerate(sorted_points[:10], 1):
                try:
                    user = self.bot.get_user(int(user_id))
                    if user:
                        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                        leaderboard_text += f"{medal} {user.display_name}: **{points}** points\n"
                    else:
                        # Try to fetch user from Discord API if not in cache
                        try:
                            user = await self.bot.fetch_user(int(user_id))
                            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                            leaderboard_text += f"{medal} {user.display_name}: **{points}** points\n"
                        except:
                            # User not found, show with ID only
                            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                            leaderboard_text += f"{medal} Unknown User ({user_id}): **{points}** points\n"
                except Exception as e:
                    logger.error(f"Error processing user {user_id} in leaderboard: {e}")
                    continue

            if leaderboard_text:
                embed.description = leaderboard_text
            else:
                embed.description = "No valid entries found."

            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}")
            await interaction.response.send_message("An error occurred while retrieving the leaderboard.", ephemeral=True)

    async def pending_carries(self, interaction: discord.Interaction):
        """View all pending carry approvals"""
        try:
            pending_data = self.load_pending()

            if not pending_data:
                await interaction.response.send_message("No pending carry approvals.", ephemeral=True)
                return

            embed = discord.Embed(
                title="⏳ Pending Carry Approvals",
                color=discord.Color.orange()
            )

            pending_text = ""
            for carry_id, data in list(pending_data.items())[:10]:  # Show max 10
                staff_user = self.bot.get_user(int(data["staff_id"]))
                staff_name = staff_user.display_name if staff_user else data["staff_name"]
                
                # Handle user_carried (for backward compatibility with old entries)
                user_carried_name = "Unknown"
                if "user_carried_id" in data:
                    user_carried_user = self.bot.get_user(int(data["user_carried_id"]))
                    user_carried_name = user_carried_user.display_name if user_carried_user else data.get("user_carried_name", "Unknown")
                
                pending_text += (
                    f"**ID:** {carry_id}\n"
                    f"**Staff:** {staff_name}\n"
                    f"**User Carried:** {user_carried_name}\n"
                    f"**Type:** {data['carry_type'].title()} {data['floor_or_tier'].upper()}\n"
                    f"**Runs:** {data['runs']} | **Grade:** {data['grade'].upper()} | **Points:** {data['points']}\n\n"
                )

            embed.description = pending_text if pending_text else "No pending approvals."

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in pending_carries command: {e}")
            await interaction.response.send_message("An error occurred while retrieving pending carries.", ephemeral=True)

    async def remove_points(self, interaction: discord.Interaction, staff: discord.Member, points: int):
        """Remove points from a staff member"""
        try:
            if points <= 0:
                await interaction.response.send_message("Points to remove must be positive.", ephemeral=True)
                return

            points_data = self.load_points()
            staff_id = str(staff.id)
            current_points = points_data.get(staff_id, 0)

            if current_points == 0:
                await interaction.response.send_message(f"{staff.display_name} has no points to remove.", ephemeral=True)
                return

            # Calculate new points (don't go below 0)
            new_points = max(0, current_points - points)
            points_removed = current_points - new_points

            # Update points
            if new_points == 0:
                # Remove entry if points reach 0
                if staff_id in points_data:
                    del points_data[staff_id]
            else:
                points_data[staff_id] = new_points

            self.save_points(points_data)

            # Create confirmation embed
            embed = discord.Embed(
                title="📉 Points Removed",
                color=discord.Color.red()
            )
            embed.add_field(name="Staff Member", value=staff.mention, inline=True)
            embed.add_field(name="Points Removed", value=str(points_removed), inline=True)
            embed.add_field(name="Previous Points", value=str(current_points), inline=True)
            embed.add_field(name="Current Points", value=str(new_points), inline=True)
            embed.add_field(name="Removed by", value=interaction.user.mention, inline=True)

            try:
                embed.set_thumbnail(url=staff.display_avatar.url)
            except Exception as avatar_error:
                logger.warning(f"Could not set avatar for {staff.display_name}: {avatar_error}")

            await interaction.response.send_message(embed=embed)

            # Send points log for removal
            await self.send_points_log_removal(interaction, staff, current_points, new_points, points_removed)

            logger.info(f"Points removed by {interaction.user.name}: {points_removed} points from {staff.name} (was {current_points}, now {new_points})")

        except Exception as e:
            logger.error(f"Error in remove_points command: {e}")
            await interaction.response.send_message("An error occurred while removing points.", ephemeral=True)

    async def send_points_log(self, interaction: discord.Interaction, carry_data: dict, previous_points: int, new_points: int, action: str):
        """Send points change log to the main points log channel"""
        try:
            # Get the points log channel
            points_channel = interaction.guild.get_channel(1401461191028637717)
            if not points_channel:
                logger.error("Points log channel not found")
                return

            # Get staff info
            staff_user = interaction.guild.get_member(int(carry_data["staff_id"]))
            staff_name = staff_user.display_name if staff_user else carry_data["staff_name"]

            # Create log embed
            embed = discord.Embed(
                title="📊 Points Updated",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="Staff Member", value=f"{staff_name} ({staff_user.mention if staff_user else 'Unknown'})", inline=True)
            embed.add_field(name="Manager", value=interaction.user.mention, inline=True)
            embed.add_field(name="Action", value=action.title(), inline=True)
            embed.add_field(name="Points Change", value=f"+{carry_data['points']}", inline=True)
            embed.add_field(name="Previous Points", value=str(previous_points), inline=True)
            embed.add_field(name="New Points", value=str(new_points), inline=True)
            embed.add_field(name="Carry Details", value=f"{carry_data['carry_type'].title()} {carry_data['floor_or_tier'].upper()} - {carry_data['grade'].upper()} ({carry_data['runs']} runs)", inline=False)
            embed.set_footer(text=f"Request ID: {self.carry_id}")

            await points_channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error sending points log: {e}")

    async def send_points_log_removal(self, interaction: discord.Interaction, staff: discord.Member, previous_points: int, new_points: int, points_removed: int):
        """Send points removal log to the main points log channel"""
        try:
            # Get the points log channel
            points_channel = interaction.guild.get_channel(1401461191028637717)
            if not points_channel:
                logger.error("Points log channel not found")
                return

            # Create log embed
            embed = discord.Embed(
                title="📉 Points Removed",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="Staff Member", value=f"{staff.display_name} ({staff.mention})", inline=True)
            embed.add_field(name="Manager", value=interaction.user.mention, inline=True)
            embed.add_field(name="Action", value="Removed", inline=True)
            embed.add_field(name="Points Change", value=f"-{points_removed}", inline=True)
            embed.add_field(name="Previous Points", value=str(previous_points), inline=True)
            embed.add_field(name="New Points", value=str(new_points), inline=True)
            embed.set_footer(text="Manual points removal")

            await points_channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error sending points removal log: {e}")

class CarryApprovalView(discord.ui.View):
    def __init__(self, carry_id: str, carry_system: CarrySystem):
        super().__init__(timeout=None)
        self.carry_id = carry_id
        self.carry_system = carry_system

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green, emoji="✅", custom_id="approve_carry")
    async def approve_carry(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_approval(interaction, True)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red, emoji="❌", custom_id="decline_carry")
    async def decline_carry(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_approval(interaction, False)

    async def handle_approval(self, interaction: discord.Interaction, approved: bool):
        try:
            # Check if user has Manager role (using role ID)
            manager_role = discord.utils.get(interaction.user.roles, id=1274788617663025182)
            if not manager_role:
                await interaction.response.send_message("Only Managers can approve or decline carry requests.", ephemeral=True)
                return

            # Load pending carry data
            pending_data = self.carry_system.load_pending()
            carry_data = pending_data.get(self.carry_id)

            if not carry_data:
                await interaction.response.send_message("This carry request is no longer valid.", ephemeral=True)
                return

            # Check if manager is trying to approve their own carry
            if str(interaction.user.id) == carry_data["staff_id"]:
                await interaction.response.send_message("You cannot approve your own carry request.", ephemeral=True)
                return

            if approved:
                # Add points to staff member
                points_data = self.carry_system.load_points()
                staff_id = carry_data["staff_id"]
                current_points = points_data.get(staff_id, 0)
                new_points = current_points + carry_data["points"]
                points_data[staff_id] = new_points
                self.carry_system.save_points(points_data)

                # Send general points log
                await self.send_points_log(interaction, carry_data, current_points, new_points, "added")

                # Send approved log to channel
                await self.send_approved_log(interaction, carry_data)

                # Update embed
                embed = interaction.message.embeds[0]
                embed.color = discord.Color.green()
                embed.add_field(name="Status", value=f"✅ Approved by {interaction.user.mention}", inline=False)
                status_message = f"Carry request approved! {carry_data['points']} points added to {carry_data['staff_name']}."
            else:
                # Ask for decline reason
                class DeclineReasonModal(discord.ui.Modal):
                    def __init__(self, carry_approval_view):
                        super().__init__(title="Decline Reason")
                        self.carry_approval_view = carry_approval_view
                        
                        self.reason_input = discord.ui.TextInput(
                            label="Why are you declining this carry request?",
                            style=discord.TextStyle.paragraph,
                            placeholder="Enter the reason for declining...",
                            required=True,
                            max_length=500
                        )
                        self.add_item(self.reason_input)

                    async def on_submit(self, modal_interaction: discord.Interaction):
                        reason = self.reason_input.value
                        
                        # Send declined log to channel
                        await self.carry_approval_view.send_declined_log(modal_interaction, carry_data, reason)
                        
                        # Update original embed
                        embed = interaction.message.embeds[0]
                        embed.color = discord.Color.red()
                        embed.add_field(name="Status", value=f"❌ Declined by {modal_interaction.user.mention}", inline=False)
                        embed.add_field(name="Reason", value=reason, inline=False)
                        
                        # Disable buttons
                        for item in self.carry_approval_view.children:
                            item.disabled = True
                        
                        # Remove from pending
                        del pending_data[self.carry_id]
                        self.carry_approval_view.carry_system.save_pending(pending_data)
                        
                        await interaction.edit_original_response(embed=embed, view=self.carry_approval_view)
                        await modal_interaction.response.send_message("Carry request declined and logged.", ephemeral=True)
                        
                        logger.info(f"Carry request {self.carry_id} declined by {modal_interaction.user.name} - Reason: {reason}")

                modal = DeclineReasonModal(self)
                await interaction.response.send_modal(modal)
                return

            # Disable buttons for approved requests
            for item in self.children:
                item.disabled = True

            # Remove from pending for approved requests
            del pending_data[self.carry_id]
            self.carry_system.save_pending(pending_data)

            await interaction.response.edit_message(embed=embed, view=self)

            # Send follow-up message for approved requests
            await interaction.followup.send(status_message, ephemeral=True)

            logger.info(f"Carry request {self.carry_id} approved by {interaction.user.name}")

        except Exception as e:
            logger.error(f"Error handling approval: {e}")
            await interaction.response.send_message("An error occurred while processing the approval.", ephemeral=True)

    async def send_approved_log(self, interaction: discord.Interaction, carry_data: dict):
        """Send approved carry log to the approved channel"""
        try:
            # Get the approved log channel
            approved_channel = interaction.guild.get_channel(1401461706764451890)
            if not approved_channel:
                logger.error("Approved log channel not found")
                return

            # Get staff and manager info
            staff_user = interaction.guild.get_member(int(carry_data["staff_id"]))
            staff_name = staff_user.display_name if staff_user else carry_data["staff_name"]
            
            user_carried_user = interaction.guild.get_member(int(carry_data["user_carried_id"]))
            user_carried_name = user_carried_user.display_name if user_carried_user else carry_data["user_carried_name"]

            # Create log embed
            embed = discord.Embed(
                title="✅ Carry Approved",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="Staff Member", value=f"{staff_name} ({staff_user.mention if staff_user else 'Unknown'})", inline=True)
            embed.add_field(name="User Carried", value=f"{user_carried_name} ({user_carried_user.mention if user_carried_user else 'Unknown'})", inline=True)
            embed.add_field(name="Approved by", value=interaction.user.mention, inline=True)
            embed.add_field(name="Carry Type", value=carry_data["carry_type"].title(), inline=True)
            embed.add_field(name="Floor/Tier", value=carry_data["floor_or_tier"].upper(), inline=True)
            embed.add_field(name="Grade", value=carry_data["grade"].upper(), inline=True)
            embed.add_field(name="Runs", value=str(carry_data["runs"]), inline=True)
            embed.add_field(name="Points Awarded", value=str(carry_data["points"]), inline=True)
            embed.set_footer(text=f"Request ID: {self.carry_id}")

            await approved_channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error sending approved log: {e}")

    async def send_declined_log(self, interaction: discord.Interaction, carry_data: dict, reason: str):
        """Send declined carry log to the declined channel"""
        try:
            # Get the declined log channel
            declined_channel = interaction.guild.get_channel(1401461442145681519)
            if not declined_channel:
                logger.error("Declined log channel not found")
                return

            # Get staff and manager info
            staff_user = interaction.guild.get_member(int(carry_data["staff_id"]))
            staff_name = staff_user.display_name if staff_user else carry_data["staff_name"]
            
            user_carried_user = interaction.guild.get_member(int(carry_data["user_carried_id"]))
            user_carried_name = user_carried_user.display_name if user_carried_user else carry_data["user_carried_name"]

            # Create log embed
            embed = discord.Embed(
                title="❌ Carry Declined",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="Staff Member", value=f"{staff_name} ({staff_user.mention if staff_user else 'Unknown'})", inline=True)
            embed.add_field(name="User Carried", value=f"{user_carried_name} ({user_carried_user.mention if user_carried_user else 'Unknown'})", inline=True)
            embed.add_field(name="Declined by", value=interaction.user.mention, inline=True)
            embed.add_field(name="Carry Type", value=carry_data["carry_type"].title(), inline=True)
            embed.add_field(name="Floor/Tier", value=carry_data["floor_or_tier"].upper(), inline=True)
            embed.add_field(name="Grade", value=carry_data["grade"].upper(), inline=True)
            embed.add_field(name="Runs", value=str(carry_data["runs"]), inline=True)
            embed.add_field(name="Points (Not Awarded)", value=str(carry_data["points"]), inline=True)
            embed.add_field(name="Decline Reason", value=reason, inline=False)
            embed.set_footer(text=f"Request ID: {self.carry_id}")

            await declined_channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error sending declined log: {e}")

async def setup(bot):
    await bot.add_cog(CarrySystem(bot))