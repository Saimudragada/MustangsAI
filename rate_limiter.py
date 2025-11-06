"""
Simple global rate limiting - no per-user tracking
Just tracks total queries to protect API costs
"""
import json
from pathlib import Path
from datetime import datetime

TOTAL_QUERY_LIMIT = 5000
ALERT_EMAIL = "saimudragada1@gmail.com"

def load_usage_stats():
    """Load usage statistics from file"""
    stats_file = Path("usage_stats.json")
    if stats_file.exists():
        with open(stats_file, 'r') as f:
            return json.load(f)
    return {
        'total_queries': 0,
        'alert_sent_1000': False,
        'alert_sent_5000': False
    }

def save_usage_stats(stats):
    """Save usage statistics"""
    with open("usage_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)

def check_global_limit():
    """Check if global query limit reached"""
    stats = load_usage_stats()
    
    if stats['total_queries'] >= TOTAL_QUERY_LIMIT:
        return False, "Demo limit reached. Contact saimudragada1@gmail.com for full access."
    
    return True, None

def increment_usage():
    """Increment usage counter and send alerts if needed"""
    stats = load_usage_stats()
    
    stats['total_queries'] += 1
    
    total = stats['total_queries']
    
    # Alert at 1000 queries
    if total == 1000 and not stats.get('alert_sent_1000'):
        send_alert_email(f"MustangsAI reached 1000 queries!")
        stats['alert_sent_1000'] = True
    
    # Alert at 5000 queries
    if total >= 5000 and not stats.get('alert_sent_5000'):
        send_alert_email(f"MustangsAI reached 5000 queries - demo limit!")
        stats['alert_sent_5000'] = True
    
    save_usage_stats(stats)
    
    return stats['total_queries']

def send_alert_email(message):
    """Log alert"""
    log_file = Path("alerts.log")
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now()} - {message}\n")
    print(f"ALERT: {message}")

def get_usage_display():
    """Get usage stats for display"""
    stats = load_usage_stats()
    
    return {
        'total_queries': stats['total_queries'],
        'remaining': TOTAL_QUERY_LIMIT - stats['total_queries']
    }