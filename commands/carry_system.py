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
            embed.set_thumbnail(url=staff.display_avatar.url)

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
                except:
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
                pending_text += (
                    f"**ID:** {carry_id}\n"
                    f"**Staff:** {staff_name}\n"
                    f"**Type:** {data['carry_type'].title()} {data['floor_or_tier'].upper()}\n"
                    f"**Runs:** {data['runs']} | **Grade:** {data['grade'].upper()} | **Points:** {data['points']}\n\n"
                )

            embed.description = pending_text if pending_text else "No pending approvals."

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in pending_carries command: {e}")
            await interaction.response.send_message("An error occurred while retrieving pending carries.", ephemeral=True)

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

            # Update embed
            embed = interaction.message.embeds[0]

            if approved:
                # Add points to staff member
                points_data = self.carry_system.load_points()
                staff_id = carry_data["staff_id"]
                current_points = points_data.get(staff_id, 0)
                points_data[staff_id] = current_points + carry_data["points"]
                self.carry_system.save_points(points_data)

                embed.color = discord.Color.green()
                embed.add_field(name="Status", value=f"✅ Approved by {interaction.user.mention}", inline=False)
                status_message = f"Carry request approved! {carry_data['points']} points added to {carry_data['staff_name']}."
            else:
                embed.color = discord.Color.red()
                embed.add_field(name="Status", value=f"❌ Declined by {interaction.user.mention}", inline=False)
                status_message = "Carry request declined. No points awarded."

            # Disable buttons
            for item in self.children:
                item.disabled = True

            # Remove from pending
            del pending_data[self.carry_id]
            self.carry_system.save_pending(pending_data)

            await interaction.response.edit_message(embed=embed, view=self)

            # Send follow-up message
            await interaction.followup.send(status_message, ephemeral=True)

            logger.info(f"Carry request {self.carry_id} {'approved' if approved else 'declined'} by {interaction.user.name}")

        except Exception as e:
            logger.error(f"Error handling approval: {e}")
            await interaction.response.send_message("An error occurred while processing the approval.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CarrySystem(bot))