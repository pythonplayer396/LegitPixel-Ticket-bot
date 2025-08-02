import random
import logging
import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger('discord')

# In-memory storage for bot data
confirmation_message = "✨ Ticket created successfully!"  # Default ticket message
staff_confirmation_message = "We recommend to wait for 24 hours after creating ticket."  # New staff confirmation message
custom_messages = {}  # Store custom messages per category
claimed_tickets = {}  # Store claimed ticket information
tickets: Dict[str, Dict[str, Any]] = {}  # Store ticket information
ticket_counter = 1  # Starting ticket number
feedback_storage = {}  # Store feedback information
ticket_logs = {}  # Store ticket logs

def get_next_ticket_number() -> str:
    """Get next sequential ticket number"""
    global ticket_counter
    try:
        current_tickets = list(tickets.keys())
        if current_tickets:
            # Convert existing ticket numbers to integers and find the maximum
            max_ticket = max(int(num) for num in current_tickets)
            ticket_counter = max(ticket_counter, max_ticket + 1)
        else:
            # If no tickets exist, start from initial counter
            ticket_counter = max(ticket_counter, 1)

        logger.info(f"Generated sequential ticket number: {ticket_counter}")
        return str(ticket_counter)
    except Exception as e:
        logger.error(f"Error generating ticket number: {e}")
        # Return a fallback number in case of error
        return str(random.randint(90000, 99999))

def has_open_ticket(user_id: str) -> bool:
    """Check if a user has any open tickets"""
    try:
        for ticket_info in tickets.values():
            if ticket_info['user_id'] == user_id and ticket_info['status'] == 'open':
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking open tickets: {e}")
        return False

def get_user_ticket_channel(user_id: str) -> Optional[str]:
    """Get the channel ID of user's open ticket if exists"""
    try:
        for ticket_info in tickets.values():
            if ticket_info['user_id'] == user_id and ticket_info['status'] == 'open':
                return ticket_info['channel_id']
        return None
    except Exception as e:
        logger.error(f"Error getting user ticket channel: {e}")
        return None

def add_rank(rank: str, color: str, emoji: str) -> None:
    ranks[rank] = {"color": color, "emoji": emoji}

def remove_rank(rank: str) -> bool:
    if rank in ranks:
        del ranks[rank]
        return True
    return False

def add_method(method: str, emoji: str) -> None:
    methods[method] = {"emoji": emoji}

def remove_method(method: str) -> bool:
    if method in methods:
        del methods[method]
        return True
    return False

def set_price(method: str, rank: str, price: float) -> None:
    if method not in prices:
        prices[method] = {}
    prices[method][rank] = price

def get_price(method: str, rank: str) -> float:
    return prices.get(method, {}).get(rank, 0.0)

def get_ranks() -> dict:
    return ranks

def get_methods() -> dict:
    return methods

def set_confirmation_message(message: str) -> None:
    global confirmation_message
    confirmation_message = message
    logger.info(f"Updated confirmation message: {message}")

def get_confirmation_message() -> str:
    """Get the confirmation message for ticket creation"""
    global confirmation_message
    try:
        logger.info(f"Retrieving confirmation message: {confirmation_message}")
        return confirmation_message
    except Exception as e:
        logger.error(f"Error retrieving confirmation message: {e}")
        return "✨ Ticket created successfully!"  # Default fallback message

def get_staff_confirmation_message() -> str:
    """Get the staff confirmation message"""
    global staff_confirmation_message
    try:
        logger.info(f"Retrieving staff confirmation message: {staff_confirmation_message}")
        return staff_confirmation_message
    except Exception as e:
        logger.error(f"Error retrieving staff confirmation message: {e}")
        return "We recommend to wait for 24 hours after creating ticket."

def set_category_message(category: str, message: str) -> None:
    """Set a custom message for a specific category"""
    custom_messages[category] = message
    logger.info(f"Set custom message for category {category}: {message}")

def get_category_message(category: str) -> Optional[str]:
    """Get the custom message for a specific category"""
    return custom_messages.get(category, None)

def claim_ticket(ticket_id: str, staff_member: str) -> None:
    """Claim a ticket"""
    try:
        claimed_tickets[ticket_id] = staff_member
        logger.info(f"Ticket {ticket_id} claimed by {staff_member}")
    except Exception as e:
        logger.error(f"Error claiming ticket: {e}")

def get_ticket_claimed_by(ticket_id: str) -> str:
    """Get who claimed a ticket"""
    try:
        claimer = claimed_tickets.get(ticket_id, "Unclaimed")
        logger.info(f"Retrieved claimer for ticket {ticket_id}: {claimer}")
        return claimer
    except Exception as e:
        logger.error(f"Error getting ticket claimer: {e}")
        return "Unclaimed"

def get_ticket_claimer(ticket_id: str) -> str:
    """Get who claimed a ticket (alias for backwards compatibility)"""
    return get_ticket_claimed_by(ticket_id)

def create_ticket(ticket_number: str, user_id: str, channel_id: str, category: str, details: Optional[str] = None) -> bool:
    """Create a new ticket entry in storage"""
    try:
        logger.info(f"[DEBUG] Creating ticket {ticket_number} with details: {details}")
        tickets[ticket_number] = {
            "user_id": user_id,
            "channel_id": channel_id,
            "category": category,
            "status": "open",
            "created_at": datetime.datetime.utcnow().isoformat(),
            "details": details or ""  # Ensure details is never None
        }
        logger.info(f"Created ticket {ticket_number} for user {user_id} in category {category}")
        logger.info(f"[DEBUG] Ticket data stored: {tickets[ticket_number]}")
        return True
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        return False

def store_feedback(ticket_name: str, user_id: str, rating: int, feedback: str, suggestions: str = "") -> bool:
    """Store feedback for a ticket"""
    try:
        feedback_storage[ticket_name] = {
            "user_id": user_id,
            "rating": rating,
            "feedback": feedback,
            "suggestions": suggestions or "",  # Ensure suggestions is never None
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        logger.info(f"Stored feedback for ticket {ticket_name} from user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error storing feedback: {e}")
        return False

def get_feedback(ticket_name: str) -> Dict[str, Any]:
    """Get feedback for a ticket"""
    try:
        feedback = feedback_storage.get(ticket_name, {})
        logger.info(f"Retrieved feedback for ticket {ticket_name}: {bool(feedback)}")
        return feedback
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        return {}

def store_ticket_log(ticket_number: str, messages: list, creator_id: str, category: str, 
                    claimed_by: Optional[str] = None, closed_by: Optional[str] = None, details: Optional[str] = None) -> bool:
    """Store ticket log information"""
    try:
        logger.info(f"[DEBUG] Storing ticket log for {ticket_number} with details: {details}")
        ticket_logs[ticket_number] = {
            "messages": messages,
            "creator_id": creator_id,
            "category": category,
            "claimed_by": claimed_by,
            "closed_by": closed_by,
            "closed_at": datetime.datetime.utcnow().isoformat(),
            "details": details
        }
        logger.info(f"[DEBUG] Ticket log data stored: {ticket_logs[ticket_number]}")
        logger.info(f"Stored log for ticket {ticket_number}")
        return True
    except Exception as e:
        logger.error(f"Error storing ticket log: {e}")
        return False

def get_ticket_log(ticket_number: str) -> Dict[str, Any]:
    """Get ticket log information"""
    try:
        logger.info(f"[DEBUG] Retrieving ticket log for {ticket_number}")
        log = ticket_logs.get(ticket_number)
        logger.info(f"[DEBUG] Retrieved ticket log data: {log}")
        return log if log else {}
    except Exception as e:
        logger.error(f"Error retrieving ticket log: {e}")
        return {}

def close_ticket(ticket_number: str) -> bool:
    """Mark a ticket as closed"""
    try:
        if ticket_number in tickets:
            tickets[ticket_number]["status"] = "closed"
            tickets[ticket_number]["closed_at"] = datetime.datetime.utcnow().isoformat()
            logger.info(f"Marked ticket {ticket_number} as closed")
            return True
        logger.warning(f"Attempted to close non-existent ticket: {ticket_number}")
        return False
    except Exception as e:
        logger.error(f"Error closing ticket: {e}")
        return False

def add_ticket_to_history(user_id: str, ticket_number: str, category: str, claimed_by: str = "Unclaimed") -> bool:
    """Add a ticket to user's history"""
    try:
        import json
        import os

        history_file = "data/ticket_history.json"
        history_data = {}

        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history_data = json.load(f)

        if user_id not in history_data:
            history_data[user_id] = []

        history_data[user_id].append({
            "number": ticket_number,
            "category": category,
            "status": "Closed",
            "date": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "claimed_by": claimed_by
        })

        with open(history_file, 'w') as f:
            json.dump(history_data, f, indent=2)

        logger.info(f"Added ticket {ticket_number} to history for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error adding ticket to history: {e}")
        return False

def get_user_ticket_history(user_id: str) -> list:
    """Get user's ticket history"""
    try:
        import json
        import os

        history_file = "data/ticket_history.json"
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history_data = json.load(f)
                return history_data.get(user_id, [])
        return []
    except Exception as e:
        logger.error(f"Error getting ticket history: {e}")
        return []

# utils/storage.py
HELP_CALLS_FILE = "data/help_calls.json"
TICKETS_FILE = "data/tickets.json"

def store_last_call_for_help(ticket_number: str, timestamp: datetime) -> None:
    """Store the timestamp when user last called for help"""
    try:
        import json
        import os

        # Load existing data
        help_calls = {}
        if os.path.exists(HELP_CALLS_FILE):
            with open(HELP_CALLS_FILE, 'r') as f:
                help_calls = json.load(f)

        # Store the timestamp as ISO format string
        help_calls[ticket_number] = timestamp.isoformat()

        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

        # Save back to file
        with open(HELP_CALLS_FILE, 'w') as f:
            json.dump(help_calls, f, indent=2)

        logger.info(f"Stored call for help timestamp for ticket {ticket_number}")

    except Exception as e:
        logger.error(f"Error storing call for help timestamp: {e}")

def get_last_call_for_help(ticket_number: str) -> Optional[datetime]:
    """Get the timestamp when user last called for help"""
    try:
        import json
        import os
        from datetime import datetime

        if not os.path.exists(HELP_CALLS_FILE):
            return None

        with open(HELP_CALLS_FILE, 'r') as f:
            help_calls = json.load(f)

        timestamp_str = help_calls.get(ticket_number)
        if timestamp_str:
            return datetime.fromisoformat(timestamp_str)

        return None

    except Exception as e:
        logger.error(f"Error getting call for help timestamp: {e}")
        return None

def load_tickets():
    """Load ticket data from file."""
    import json
    import os
    if not os.path.exists(TICKETS_FILE):
        return {}
    with open(TICKETS_FILE, 'r') as f:
        return json.load(f)

def save_tickets(tickets):
    """Save ticket data to file."""
    import json
    import os
    os.makedirs("data", exist_ok=True)
    with open(TICKETS_FILE, 'w') as f:
        json.dump(tickets, f, indent=2)

def set_ticket_priority(ticket_number: str, priority: str) -> None:
    """Set priority for a ticket (can only be set once)"""
    try:
        tickets = load_tickets()
        if ticket_number in tickets:
            tickets[ticket_number]['priority'] = priority
            save_tickets(tickets)
            logger.info(f"Set priority {priority} for ticket {ticket_number}")
    except Exception as e:
        logger.error(f"Error setting ticket priority: {e}")

def get_ticket_priority(ticket_number: str) -> Optional[str]:
    """Get the priority of a ticket"""
    try:
        tickets = load_tickets()
        ticket_data = tickets.get(ticket_number, {})
        return ticket_data.get('priority')
    except Exception as e:
        logger.error(f"Error getting ticket priority: {e}")
        return None
```import random
import logging
import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger('discord')

# In-memory storage for bot data
confirmation_message = "✨ Ticket created successfully!"  # Default ticket message
staff_confirmation_message = "We recommend to wait for 24 hours after creating ticket."  # New staff confirmation message
custom_messages = {}  # Store custom messages per category
claimed_tickets = {}  # Store claimed ticket information
tickets: Dict[str, Dict[str, Any]] = {}  # Store ticket information
ticket_counter = 1  # Starting ticket number
feedback_storage = {}  # Store feedback information
ticket_logs = {}  # Store ticket logs

def get_next_ticket_number() -> str:
    """Get next sequential ticket number"""
    global ticket_counter
    try:
        current_tickets = list(tickets.keys())
        if current_tickets:
            # Convert existing ticket numbers to integers and find the maximum
            max_ticket = max(int(num) for num in current_tickets)
            ticket_counter = max(ticket_counter, max_ticket + 1)
        else:
            # If no tickets exist, start from initial counter
            ticket_counter = max(ticket_counter, 1)

        logger.info(f"Generated sequential ticket number: {ticket_counter}")
        return str(ticket_counter)
    except Exception as e:
        logger.error(f"Error generating ticket number: {e}")
        # Return a fallback number in case of error
        return str(random.randint(90000, 99999))

def has_open_ticket(user_id: str) -> bool:
    """Check if a user has any open tickets"""
    try:
        for ticket_info in tickets.values():
            if ticket_info['user_id'] == user_id and ticket_info['status'] == 'open':
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking open tickets: {e}")
        return False

def get_user_ticket_channel(user_id: str) -> Optional[str]:
    """Get the channel ID of user's open ticket if exists"""
    try:
        for ticket_info in tickets.values():
            if ticket_info['user_id'] == user_id and ticket_info['status'] == 'open':
                return ticket_info['channel_id']
        return None
    except Exception as e:
        logger.error(f"Error getting user ticket channel: {e}")
        return None

def add_rank(rank: str, color: str, emoji: str) -> None:
    ranks[rank] = {"color": color, "emoji": emoji}

def remove_rank(rank: str) -> bool:
    if rank in ranks:
        del ranks[rank]
        return True
    return False

def add_method(method: str, emoji: str) -> None:
    methods[method] = {"emoji": emoji}

def remove_method(method: str) -> bool:
    if method in methods:
        del methods[method]
        return True
    return False

def set_price(method: str, rank: str, price: float) -> None:
    if method not in prices:
        prices[method] = {}
    prices[method][rank] = price

def get_price(method: str, rank: str) -> float:
    return prices.get(method, {}).get(rank, 0.0)

def get_ranks() -> dict:
    return ranks

def get_methods() -> dict:
    return methods

def set_confirmation_message(message: str) -> None:
    global confirmation_message
    confirmation_message = message
    logger.info(f"Updated confirmation message: {message}")

def get_confirmation_message() -> str:
    """Get the confirmation message for ticket creation"""
    global confirmation_message
    try:
        logger.info(f"Retrieving confirmation message: {confirmation_message}")
        return confirmation_message
    except Exception as e:
        logger.error(f"Error retrieving confirmation message: {e}")
        return "✨ Ticket created successfully!"  # Default fallback message

def get_staff_confirmation_message() -> str:
    """Get the staff confirmation message"""
    global staff_confirmation_message
    try:
        logger.info(f"Retrieving staff confirmation message: {staff_confirmation_message}")
        return staff_confirmation_message
    except Exception as e:
        logger.error(f"Error retrieving staff confirmation message: {e}")
        return "We recommend to wait for 24 hours after creating ticket."

def set_category_message(category: str, message: str) -> None:
    """Set a custom message for a specific category"""
    custom_messages[category] = message
    logger.info(f"Set custom message for category {category}: {message}")

def get_category_message(category: str) -> Optional[str]:
    """Get the custom message for a specific category"""
    return custom_messages.get(category, None)

def claim_ticket(ticket_id: str, staff_member: str) -> None:
    """Claim a ticket"""
    try:
        claimed_tickets[ticket_id] = staff_member
        logger.info(f"Ticket {ticket_id} claimed by {staff_member}")
    except Exception as e:
        logger.error(f"Error claiming ticket: {e}")

def get_ticket_claimed_by(ticket_id: str) -> str:
    """Get who claimed a ticket"""
    try:
        claimer = claimed_tickets.get(ticket_id, "Unclaimed")
        logger.info(f"Retrieved claimer for ticket {ticket_id}: {claimer}")
        return claimer
    except Exception as e:
        logger.error(f"Error getting ticket claimer: {e}")
        return "Unclaimed"

def get_ticket_claimer(ticket_id: str) -> str:
    """Get who claimed a ticket (alias for backwards compatibility)"""
    return get_ticket_claimed_by(ticket_id)

def create_ticket(ticket_number: str, user_id: str, channel_id: str, category: str, details: Optional[str] = None) -> bool:
    """Create a new ticket entry in storage"""
    try:
        logger.info(f"[DEBUG] Creating ticket {ticket_number} with details: {details}")
        tickets[ticket_number] = {
            "user_id": user_id,
            "channel_id": channel_id,
            "category": category,
            "status": "open",
            "created_at": datetime.datetime.utcnow().isoformat(),
            "details": details or ""  # Ensure details is never None
        }
        logger.info(f"Created ticket {ticket_number} for user {user_id} in category {category}")
        logger.info(f"[DEBUG] Ticket data stored: {tickets[ticket_number]}")
        return True
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        return False

def store_feedback(ticket_name: str, user_id: str, rating: int, feedback: str, suggestions: str = "") -> bool:
    """Store feedback for a ticket"""
    try:
        feedback_storage[ticket_name] = {
            "user_id": user_id,
            "rating": rating,
            "feedback": feedback,
            "suggestions": suggestions or "",  # Ensure suggestions is never None
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        logger.info(f"Stored feedback for ticket {ticket_name} from user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error storing feedback: {e}")
        return False

def get_feedback(ticket_name: str) -> Dict[str, Any]:
    """Get feedback for a ticket"""
    try:
        feedback = feedback_storage.get(ticket_name, {})
        logger.info(f"Retrieved feedback for ticket {ticket_name}: {bool(feedback)}")
        return feedback
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        return {}

def store_ticket_log(ticket_number: str, messages: list, creator_id: str, category: str, 
                    claimed_by: Optional[str] = None, closed_by: Optional[str] = None, details: Optional[str] = None) -> bool:
    """Store ticket log information"""
    try:
        logger.info(f"[DEBUG] Storing ticket log for {ticket_number} with details: {details}")
        ticket_logs[ticket_number] = {
            "messages": messages,
            "creator_id": creator_id,
            "category": category,
            "claimed_by": claimed_by,
            "closed_by": closed_by,
            "closed_at": datetime.datetime.utcnow().isoformat(),
            "details": details
        }
        logger.info(f"[DEBUG] Ticket log data stored: {ticket_logs[ticket_number]}")
        logger.info(f"Stored log for ticket {ticket_number}")
        return True
    except Exception as e:
        logger.error(f"Error storing ticket log: {e}")
        return False

def get_ticket_log(ticket_number: str) -> Dict[str, Any]:
    """Get ticket log information"""
    try:
        logger.info(f"[DEBUG] Retrieving ticket log for {ticket_number}")
        log = ticket_logs.get(ticket_number)
        logger.info(f"[DEBUG] Retrieved ticket log data: {log}")
        return log if log else {}
    except Exception as e:
        logger.error(f"Error retrieving ticket log: {e}")
        return {}

def close_ticket(ticket_number: str) -> bool:
    """Mark a ticket as closed"""
    try:
        if ticket_number in tickets:
            tickets[ticket_number]["status"] = "closed"
            tickets[ticket_number]["closed_at"] = datetime.datetime.utcnow().isoformat()
            logger.info(f"Marked ticket {ticket_number} as closed")
            return True
        logger.warning(f"Attempted to close non-existent ticket: {ticket_number}")
        return False
    except Exception as e:
        logger.error(f"Error closing ticket: {e}")
        return False

def add_ticket_to_history(user_id: str, ticket_number: str, category: str, claimed_by: str = "Unclaimed") -> bool:
    """Add a ticket to user's history"""
    try:
        import json
        import os

        history_file = "data/ticket_history.json"
        history_data = {}

        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history_data = json.load(f)

        if user_id not in history_data:
            history_data[user_id] = []

        history_data[user_id].append({
            "number": ticket_number,
            "category": category,
            "status": "Closed",
            "date": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "claimed_by": claimed_by
        })

        with open(history_file, 'w') as f:
            json.dump(history_data, f, indent=2)

        logger.info(f"Added ticket {ticket_number} to history for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error adding ticket to history: {e}")
        return False

def get_user_ticket_history(user_id: str) -> list:
    """Get user's ticket history"""
    try:
        import json
        import os

        history_file = "data/ticket_history.json"
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history_data = json.load(f)
                return history_data.get(user_id, [])
        return []
    except Exception as e:
        logger.error(f"Error getting ticket history: {e}")
        return []

# utils/storage.py
HELP_CALLS_FILE = "data/help_calls.json"
TICKETS_FILE = "data/tickets.json"

def store_last_call_for_help(ticket_number: str, timestamp: datetime) -> None:
    """Store the timestamp when user last called for help"""
    try:
        import json
        import os

        # Load existing data
        help_calls = {}
        if os.path.exists(HELP_CALLS_FILE):
            with open(HELP_CALLS_FILE, 'r') as f:
                help_calls = json.load(f)

        # Store the timestamp as ISO format string
        help_calls[ticket_number] = timestamp.isoformat()

        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

        # Save back to file
        with open(HELP_CALLS_FILE, 'w') as f:
            json.dump(help_calls, f, indent=2)

        logger.info(f"Stored call for help timestamp for ticket {ticket_number}")

    except Exception as e:
        logger.error(f"Error storing call for help timestamp: {e}")

def get_last_call_for_help(ticket_number: str) -> Optional[datetime]:
    """Get the timestamp when user last called for help"""
    try:
        import json
        import os
        from datetime import datetime

        if not os.path.exists(HELP_CALLS_FILE):
            return None

        with open(HELP_CALLS_FILE, 'r') as f:
            help_calls = json.load(f)

        timestamp_str = help_calls.get(ticket_number)
        if timestamp_str:
            return datetime.fromisoformat(timestamp_str)

        return None

    except Exception as e:
        logger.error(f"Error getting call for help timestamp: {e}")
        return None

def load_tickets():
    """Load ticket data from file."""
    import json
    import os
    if not os.path.exists(TICKETS_FILE):
        return {}
    with open(TICKETS_FILE, 'r') as f:
        return json.load(f)

def save_tickets(tickets):
    """Save ticket data to file."""
    import json
    import os
    os.makedirs("data", exist_ok=True)
    with open(TICKETS_FILE, 'w') as f:
        json.dump(tickets, f, indent=2)

def set_ticket_priority(ticket_number: str, priority: str) -> None:
    """Set priority for a ticket (can only be set once)"""
    try:
        tickets = load_tickets()
        if ticket_number in tickets:
            tickets[ticket_number]['priority'] = priority
            save_tickets(tickets)
            logger.info(f"Set priority {priority} for ticket {ticket_number}")
    except Exception as e:
        logger.error(f"Error setting ticket priority: {e}")

def get_ticket_priority(ticket_number: str) -> Optional[str]:
    """Get the priority of a ticket"""
    try:
        tickets = load_tickets()
        ticket_data = tickets.get(ticket_number, {})
        return ticket_data.get('priority')
    except Exception as e:
        logger.error(f"Error getting ticket priority: {e}")
        return None