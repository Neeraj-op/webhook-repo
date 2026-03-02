"""
Utility functions for parsing webhooks and formatting data
"""

from datetime import datetime, timedelta
import pytz
import hashlib


ist = pytz.timezone('Asia/Kolkata')


def parse_push_event(payload):
    """
    Parse GitHub push event payload

    Args:
        payload: GitHub webhook payload (dict)

    Returns:
        dict: Parsed event data
    """
    try:
        # Extract branch name from ref (e.g., "refs/heads/main" -> "main")
        ref = payload.get('ref', '')
        to_branch = ref.split('/')[-1] if '/' in ref else ref

        pusher = payload.get('pusher', {})
        author = pusher.get('name', 'Unknown')

        # Get commit hash (use 'after' which is the new HEAD commit)
        request_id = payload.get('after', hashlib.md5(
            str(payload).encode()).hexdigest())

        # Get timestamp from head commit or use current time
        head_commit = payload.get('head_commit', {})
        timestamp = head_commit.get(
            'timestamp', datetime.utcnow().isoformat() + 'Z')

        return {
            'request_id': request_id,
            'author': author,
            'action': 'PUSH',
            'from_branch': None,  # Push not have from_branch
            'to_branch': to_branch,
            'timestamp': timestamp
        }
    except Exception as e:
        print(f"Error parsing push event: {e}")
        raise


def parse_pull_request_event(payload):
    """
    Parse GitHub pull request event payload

    Args:
        payload: GitHub webhook payload (dict)

    Returns:
        dict: Parsed event data
    """
    try:
        pull_request = payload.get('pull_request', {})
        action = payload.get('action', '')

        # Get author
        user = pull_request.get('user', {})
        author = user.get('login', 'Unknown')

        # Get branches
        head = pull_request.get('head', {})
        base = pull_request.get('base', {})
        from_branch = head.get('ref', 'unknown')
        to_branch = base.get('ref', 'unknown')

        # Get PR ID as request_id
        request_id = str(pull_request.get(
            'id', hashlib.md5(str(payload).encode()).hexdigest()))

        if action == 'closed' and pull_request.get('merged'):
            merged_by = pull_request.get('merged_by', {})
            author = merged_by.get('login', author)
            timestamp = pull_request.get(
                'merged_at', datetime.utcnow().isoformat() + 'Z')
            event_action = 'MERGE'
        else:
            timestamp = pull_request.get(
                'created_at', datetime.utcnow().isoformat() + 'Z')
            event_action = 'PULL_REQUEST'

        return {
            'request_id': request_id,
            'author': author,
            'action': event_action,
            'from_branch': from_branch,
            'to_branch': to_branch,
            'timestamp': timestamp
        }
    except Exception as e:
        print(f"Error parsing pull request event: {e}")
        raise


# def format_timestamp(iso_timestamp):
#     """
#     Format ISO timestamp to human-readable IST format

#     Args:
#         iso_timestamp: ISO 8601 timestamp string (UTC)

#     Returns:
#         str: Formatted timestamp in IST (e.g., "2nd March 2026 - 9:32 PM IST")
#     """
#     try:
#         dt_utc = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))

#         dt_ist = dt_utc

#         day = dt_ist.day
#         if 11 <= day <= 13:
#             suffix = 'th'
#         else:
#             suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

#         # Format: "2nd March 2026 - 9:32 PM IST"
#         formatted = dt_ist.strftime(f'%d{suffix} %B %Y - %I:%M %p IST')

#         if formatted[0] == '0':
#             formatted = formatted[1:]

#         return formatted
#     except Exception as e:
#         print(f"Error formatting timestamp: {e}")
#         return iso_timestamp

# def format_timestamp(iso_timestamp):
#     """
#     Format ISO timestamp to human-readable IST format

#     Args:
#         iso_timestamp: ISO 8601 timestamp string (UTC)

#     Returns:
#         str: Formatted timestamp in IST (e.g., "2nd March 2026 - 9:32 PM IST")
#     """
#     try:
#         # Parse the UTC timestamp
#         dt_utc = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        
#         # Convert to IST using pytz (you already imported it!)
#         utc_zone = pytz.utc
        
#         # If datetime is naive (no timezone), assume it's UTC
#         if dt_utc.tzinfo is None:
#             dt_utc = utc_zone.localize(dt_utc)
        
#         # Convert to IST
#         dt_ist = dt_utc.astimezone(ist)
        
#         # Get day with ordinal suffix
#         day = dt_ist.day
#         if 11 <= day <= 13:
#             suffix = 'th'
#         else:
#             suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

#         # Format: "2nd March 2026 - 9:32 PM IST"
#         formatted = dt_ist.strftime(f'%d{suffix} %B %Y - %I:%M %p IST')

#         # Remove leading zero from day if present
#         if formatted[0] == '0':
#             formatted = formatted[1:]

#         return formatted
#     except Exception as e:
#         print(f"Error formatting timestamp: {e}")
#         return iso_timestamp

def format_timestamp(iso_timestamp):
    """
    Format ISO timestamp to human-readable IST format
    Handles multiple timestamp formats
    """
    try:
        from dateutil import parser
        
        # Use dateutil parser - handles ANY ISO format
        dt = parser.parse(iso_timestamp)
        
        # Convert to IST
        if dt.tzinfo is None:
            # No timezone - assume UTC
            dt = pytz.utc.localize(dt)
        
        dt_ist = dt.astimezone(ist)
        
        # Format
        day = dt_ist.day
        suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        formatted = dt_ist.strftime(f'%d{suffix} %B %Y - %I:%M %p IST')
        
        if formatted[0] == '0':
            formatted = formatted[1:]
        
        return formatted
    except Exception as e:
        print(f"Error formatting timestamp: {e}")
        print(f"Timestamp value: {iso_timestamp}")
        return iso_timestamp

def format_event_message(event):
    """
    Format event data into display message

    Args:
        event: Event data from MongoDB (dict)

    Returns:
        str: Formatted message
    """
    author = event.get('author', 'Unknown')
    action = event.get('action', '')
    from_branch = event.get('from_branch')
    to_branch = event.get('to_branch', 'unknown')
    timestamp = format_timestamp(event.get('timestamp', ''))

    if action == 'PUSH':
        return f'{author} pushed to {to_branch} on {timestamp}'
    elif action == 'PULL_REQUEST':
        return f'{author} submitted a pull request from {from_branch} to {to_branch} on {timestamp}'
    elif action == 'MERGE':
        return f'{author} merged branch {from_branch} to {to_branch} on {timestamp}'
    else:
        return f'{author} performed {action} on {timestamp}'
