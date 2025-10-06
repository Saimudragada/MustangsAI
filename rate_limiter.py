"""
Enhanced rate limiting with persistent device tracking
"""
import streamlit as st
from datetime import datetime
import hashlib
import json
from pathlib import Path
import socket

# Usage limits
MAX_QUERIES_PER_DEVICE = 5
TOTAL_QUERY_LIMIT = 5000
ALERT_EMAIL = "saimudragada1@gmail.com"

def get_device_fingerprint():
    """
    Create persistent device identifier using multiple signals
    More robust than session-only tracking
    """
    # Try to get IP address from Streamlit headers
    try:
        # In deployed environment, get forwarded IP
        headers = st.context.headers if hasattr(st, 'context') else {}
        ip = headers.get('X-Forwarded-For', headers.get('X-Real-Ip', 'unknown'))
        
        # Combine with user agent for better fingerprinting
        user_agent = headers.get('User-Agent', 'unknown')
        
        # Create fingerprint from IP + user agent
        fingerprint_string = f"{ip}_{user_agent}"
        device_id = hashlib.sha256(fingerprint_string.encode()).hexdigest()
        
        return device_id
    except:
        # Fallback to session-based if headers not available
        if 'device_id' not in st.session_state:
            st.session_state.device_id = hashlib.md5(
                f"{datetime.now()}{id(st.session_state)}".encode()
            ).hexdigest()
        return st.session_state.device_id

def load_usage_stats():
    """Load usage statistics from file"""
    stats_file = Path("usage_stats.json")
    if stats_file.exists():
        with open(stats_file, 'r') as f:
            return json.load(f)
    return {
        'total_queries': 0,
        'devices': {},
        'alert_sent_1000': False,
        'alert_sent_5000': False
    }

def save_usage_stats(stats):
    """Save usage statistics"""
    with open("usage_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)

def check_device_limit():
    """Check if device has queries remaining"""
    device_id = get_device_fingerprint()
    stats = load_usage_stats()
    
    device_count = stats['devices'].get(device_id, 0)
    
    if device_count >= MAX_QUERIES_PER_DEVICE:
        return False, 0
    
    return True, MAX_QUERIES_PER_DEVICE - device_count

def check_global_limit():
    """Check if global query limit reached"""
    stats = load_usage_stats()
    
    if stats['total_queries'] >= TOTAL_QUERY_LIMIT:
        return False, "Global usage limit reached. Demo is currently unavailable."
    
    return True, None

def increment_usage():
    """Increment usage counters and send alerts if needed"""
    device_id = get_device_fingerprint()
    stats = load_usage_stats()
    
    # Increment counters
    stats['total_queries'] += 1
    stats['devices'][device_id] = stats['devices'].get(device_id, 0) + 1
    
    # Check for alerts
    total = stats['total_queries']
    
    # Alert at 1000 queries
    if total == 1000 and not stats.get('alert_sent_1000'):
        send_alert_email(f"MustangsAI reached 1000 queries! Total: {total}")
        stats['alert_sent_1000'] = True
    
    # Alert at 5000 queries
    if total == 5000 and not stats.get('alert_sent_5000'):
        send_alert_email(f"MustangsAI reached 5000 queries! Demo limit hit.")
        stats['alert_sent_5000'] = True
    
    save_usage_stats(stats)
    
    return stats['total_queries'], stats['devices'][device_id]

def send_alert_email(message):
    """Log alert - check alerts.log file manually"""
    log_file = Path("alerts.log")
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now()} - {message}\n")
    print(f"ALERT: {message}")

def get_usage_display():
    """Get usage stats for display"""
    stats = load_usage_stats()
    device_id = get_device_fingerprint()
    device_count = stats['devices'].get(device_id, 0)
    
    return {
        'total_queries': stats['total_queries'],
        'your_queries': device_count,
        'remaining': MAX_QUERIES_PER_DEVICE - device_count
    }