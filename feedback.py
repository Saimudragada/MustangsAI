"""
Feedback tracking system
"""
import json
from pathlib import Path
from datetime import datetime

FEEDBACK_FILE = Path("feedback.json")

def load_feedback():
    """Load feedback data"""
    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, 'r') as f:
            return json.load(f)
    return {'responses': []}

def save_feedback(data):
    """Save feedback data"""
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_feedback(question, answer, rating, comment=""):
    """
    Add feedback for a response
    rating: 'positive' or 'negative'
    """
    data = load_feedback()
    
    feedback_entry = {
        'timestamp': datetime.now().isoformat(),
        'question': question,
        'answer': answer[:200],  # Truncate for storage
        'rating': rating,
        'comment': comment
    }
    
    data['responses'].append(feedback_entry)
    save_feedback(data)

def get_feedback_stats():
    """Get feedback statistics"""
    data = load_feedback()
    responses = data['responses']
    
    if not responses:
        return {
            'total': 0,
            'positive': 0,
            'negative': 0,
            'satisfaction_rate': 0
        }
    
    positive = sum(1 for r in responses if r['rating'] == 'positive')
    negative = sum(1 for r in responses if r['rating'] == 'negative')
    
    return {
        'total': len(responses),
        'positive': positive,
        'negative': negative,
        'satisfaction_rate': round((positive / len(responses)) * 100, 1) if responses else 0
    }