import discord
from typing import Optional
import logging

logger = logging.getLogger(__name__) # Assuming a logger is available

def create_embed(title: str, description: str, color: discord.Color = discord.Color.blue()) -> discord.Embed:
    """Create a formatted embed message"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    return embed

def error_embed(message: str) -> discord.Embed:
    """Create an error embed message"""
    return create_embed("Error", message, discord.Color.red())

def success_embed(message: str) -> discord.Embed:
    """Create a success embed message"""
    return create_embed("Success", message, discord.Color.green())

def coming_soon_embed() -> discord.Embed:
    """Create a coming soon embed message"""
    return create_embed(
        "🚧 Coming Soon!",
        "This feature is currently under development. Stay tuned for updates!",
        discord.Color.orange()
    )

def ticket_embed(user: discord.Member, category: str, ticket_number: str, details: Optional[str] = None, claimed_by: Optional[str] = None) -> discord.Embed:
    """Create a ticket embed message with improved formatting"""
    status_emoji = "🔓" if not claimed_by else "🔒"

    description = (
        f"## 🎫 Ticket #{ticket_number}\n\n"
        f"**Creator:** {user.mention}\n"
        f"**Category:** {category}\n"
        f"**Status:** {status_emoji} {claimed_by or 'Unclaimed'}\n"
    )

    if details:
        description += f"\n**Details:**\n```{details}```"

    embed = discord.Embed(
        title="✨ New Ticket Created",
        description=description,
        color=discord.Color.blue()
    )

    embed.set_footer(text=f"Created by {user.name}")
    return embed

def feedback_embed(ticket_name: str, user: discord.Member, rating: int, feedback: str, suggestions: str, 
                  claimed_by: Optional[str] = None, closed_by: Optional[str] = None) -> discord.Embed:
    """Create a feedback embed with improved formatting"""
    stars = "⭐" * rating

    description = (
        f"## Ticket Feedback Summary\n\n"
        f"**Ticket:** {ticket_name}\n"
        f"**Rating:** {stars}\n"
        f"**Creator:** {user.mention}\n\n"
        f"### Feedback\n{feedback}\n\n"
    )

    if suggestions:
        description += f"### Suggestions\n{suggestions}\n\n"

    description += (
        f"**Resolved By:** {closed_by or 'Unknown'}"
    )

    embed = discord.Embed(
        title="✨ Ticket Feedback",
        description=description,
        color=discord.Color.gold()
    )

    embed.timestamp = discord.utils.utcnow()
    return embed

def ticket_log_embed(ticket_number: str, creator: discord.Member, category: str, claimed_by: Optional[str] = None, 
                    closed_by: Optional[str] = None, duration: Optional[str] = None, details: Optional[str] = None) -> discord.Embed:
    """Create a ticket log embed with updated format"""
    logger.info(f"[DEBUG] Creating ticket log embed for ticket {ticket_number}")

    description = (
        f"# 📝 Ticket Log\n\n"
        f"**Ticket Log:** #{ticket_number}\n"
        f"**Creator:** {creator.mention}\n"
        f"**Category:** {category}\n"
        f"**Claimed By:** {claimed_by or 'Unclaimed'}\n"
        f"**Closed By:** {closed_by or 'Unknown'}\n"
    )

    if details:
        description += f"\n**Ticket Details:**\n```{details}```"
        logger.info(f"[DEBUG] Added details to embed description")
    else:
        logger.info(f"[DEBUG] No details provided for embed")

    embed = discord.Embed(
        title="📝 Ticket Log",
        description=description,
        color=discord.Color.blue()
    )

    embed.timestamp = discord.utils.utcnow()
    return embed

def transcript_embed(messages: list, ticket_number: str) -> discord.Embed:
    """Create a separate embed for ticket transcript"""
    transcript_text = "\n".join([
        f"[{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {msg.author.name}: {msg.content}"
        for msg in messages if msg.content
    ])

    embed = discord.Embed(
        title=f"📜 Ticket Transcript #{ticket_number}",
        description=f"```\n{transcript_text[:4000]}```" if transcript_text else "No messages found",
        color=discord.Color.blue()
    )

    return embed

def priority_embed(ticket_number: str, category: str, creator: discord.Member, priority: str, emoji: str) -> discord.Embed:
    """Create a modernized priority alert embed"""
    logger.info(f"[DEBUG] Creating priority embed for ticket {ticket_number} with priority {priority}")

    # Define priority colors and borders
    priority_styles = {
        "URGENT": {
            "color": discord.Color.red(),
            "border": "🔴",
            "description": "Immediate attention required"
        },
        "HIGH": {
            "color": discord.Color.orange(),
            "border": "🟠",
            "description": "High priority issue"
        },
        "MEDIUM": {
            "color": discord.Color.gold(),
            "border": "🟡",
            "description": "Standard priority"
        },
        "LOW": {
            "color": discord.Color.green(),
            "border": "🟢",
            "description": "Non-urgent issue"
        }
    }

    style = priority_styles.get(priority, {
        "color": discord.Color.blue(),
        "border": "⚪",
        "description": "Priority not specified"
    })

    logger.info(f"[DEBUG] Using style for {priority}: {style['border']} - {style['description']}")

    # Create a cleaner, more structured description
    description = (
        f"{style['border']} **Priority Level: {priority}**\n"
        f"{style['description']}\n\n"
        f"### Ticket Information\n"
        f"• **Ticket ID:** #{ticket_number}\n"
        f"• **Category:** {category}\n"
        f"• **Created By:** {creator.mention}\n\n"
        f"*Staff members will be notified based on priority level*"
    )

    embed = discord.Embed(
        title=f"{emoji} Priority Ticket Alert",
        description=description,
        color=style["color"]
    )

    # Add a themed footer
    embed.set_footer(text=f"Priority Status: {priority} | Updated")

    # Add timestamp
    embed.timestamp = discord.utils.utcnow()

    logger.info(f"[DEBUG] Created priority embed with title: {embed.title}")
    return embed