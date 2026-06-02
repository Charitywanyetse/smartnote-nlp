import re
import dateparser
from datetime import datetime, timedelta
from textblob import TextBlob

# Urgency keywords (High priority)
HIGH_URGENCY_KEYWORDS = [
    'urgent', 'rush', 'asap', 'emergency', 'immediately',
    'critical', 'quick', 'fast', 'express', 'priority',
    'hurry', 'last minute', 'soon as possible', 'need it now',
    'overnight', 'need this fast', 'time sensitive'
]

# Medium urgency keywords
MEDIUM_URGENCY_KEYWORDS = [
    'please', 'important', 'soon', 'quickly', 'prompt',
    'timely', 'deadline', 'need by', 'by tomorrow',
    'as soon as', 'would appreciate'
]

# Garment types to detect
GARMENT_KEYWORDS = {
    'dress': ['dress', 'gown', 'wedding dress', 'bridesmaid dress', 'cocktail dress', 'maxi dress', 'mini dress', 'sundress', 'formal dress'],
    'suit': ['suit', 'blazer', 'business suit', 'pantsuit'],
    'shirt': ['shirt', 'blouse', 'top', 't-shirt', 'button down', 'tank top', 'crop top'],
    'jacket': ['jacket', 'coat', 'blazer', 'cardigan', 'bomber', 'denim jacket'],
    'pants': ['pants', 'trousers', 'jeans', 'slacks', 'chinos', 'leggings', 'tights'],
    'skirt': ['skirt', 'mini skirt', 'midi skirt', 'maxi skirt', 'pencil skirt'],
    'romper': ['romper', 'jumpsuit', 'playsuit'],
    'sweater': ['sweater', 'pullover', 'cardigan', 'knit'],
    'shoes': ['shoes', 'boots', 'sandals', 'heels', 'flats', 'sneakers', 'wedges'],
    'accessories': ['bag', 'purse', 'clutch', 'wallet', 'belt', 'scarf', 'hat', 'jewelry']
}

# Event types (useful for context)
EVENT_KEYWORDS = {
    'wedding': ['wedding', 'bridal', 'bride', 'bridesmaid'],
    'interview': ['interview', 'job interview', 'career fair'],
    'party': ['party', 'birthday', 'anniversary', 'celebration'],
    'vacation': ['vacation', 'trip', 'travel', 'holiday', 'beach'],
    'work': ['work', 'office', 'business', 'meeting', 'conference'],
    'formal': ['gala', 'black tie', 'formal', 'ball', 'charity']
}

def detect_urgency(text):
    """Detect urgency level from customer note (improved with context)"""
    text_lower = text.lower()
    
    # Check for negations that cancel urgency
    negations = ['no ', 'not ', "don't ", "doesn't ", "isn't ", "aren't "]
    
    # For each urgency keyword, check if it's negated
    for keyword in HIGH_URGENCY_KEYWORDS:
        if keyword in text_lower:
            # Check if keyword is negated
            is_negated = False
            for neg in negations:
                # Look for negation right before the keyword
                neg_index = text_lower.find(neg)
                keyword_index = text_lower.find(keyword)
                if neg_index != -1 and keyword_index != -1:
                    if abs(neg_index + len(neg) - keyword_index) < 10:
                        is_negated = True
                        break
            
            if not is_negated:
                return 'HIGH'
    
    # Check medium urgency
    for keyword in MEDIUM_URGENCY_KEYWORDS:
        if keyword in text_lower:
            return 'MEDIUM'
    
    return 'LOW'

def extract_garments(text):
    """Extract garment types mentioned in the note"""
    text_lower = text.lower()
    found_garments = []
    
    for garment_type, keywords in GARMENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                found_garments.append(garment_type)
                break
    
    return list(set(found_garments)) if found_garments else ['not specified']

def extract_event(text):
    """Extract event type if mentioned"""
    text_lower = text.lower()
    found_events = []
    
    for event_type, keywords in EVENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                found_events.append(event_type)
                break
    
    return found_events[0] if found_events else 'general'

def extract_deadline(text):
    """Extract deadline/date from customer note"""
    text_lower = text.lower()
    
    # Check for specific date patterns
    today = datetime.now()
    
    # Tomorrow
    if 'tomorrow' in text_lower:
        target_date = today + timedelta(days=1)
        return {
            'date': target_date.strftime('%Y-%m-%d'),
            'relative_time': 'tomorrow',
            'days': 1
        }
    
    # Day names
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for i, day in enumerate(days_of_week):
        if f'by {day}' in text_lower or f'on {day}' in text_lower or f'this {day}' in text_lower:
            # Find next occurrence of that day
            current_weekday = today.weekday()  # Monday=0, Sunday=6
            target_weekday = i
            days_ahead = target_weekday - current_weekday
            if days_ahead <= 0:
                days_ahead += 7
            target_date = today + timedelta(days=days_ahead)
            return {
                'date': target_date.strftime('%Y-%m-%d'),
                'relative_time': f'this {day}',
                'days': days_ahead
            }
    
    # Try dateparser
    parsed_date = dateparser.parse(text_lower, settings={
        'PREFER_DATES_FROM': 'future',
        'RELATIVE_BASE': today
    })
    
    if parsed_date:
        days_diff = (parsed_date - today).days
        if 0 <= days_diff <= 30:  # Only return if within 30 days
            return {
                'date': parsed_date.strftime('%Y-%m-%d'),
                'relative_time': f'in {days_diff} days' if days_diff > 0 else 'today',
                'days': days_diff
            }
    
    return None

def analyze_sentiment(text):
    """Analyze sentiment of the customer note"""
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    if polarity > 0.3:
        sentiment = 'Very Positive'
    elif polarity > 0.1:
        sentiment = 'Positive'
    elif polarity > -0.1:
        sentiment = 'Neutral'
    elif polarity > -0.3:
        sentiment = 'Negative'
    else:
        sentiment = 'Very Negative'
    
    return {
        'polarity': round(polarity, 2),
        'subjectivity': round(blob.sentiment.subjectivity, 2),
        'sentiment_label': sentiment
    }

def get_action_text(urgency, days_until_deadline=None):
    """Generate action text based on analysis"""
    if urgency == 'HIGH':
        return '🔴 IMMEDIATE ACTION - Rush processing required'
    elif urgency == 'MEDIUM' and days_until_deadline is not None:
        if days_until_deadline <= 2:
            return '🟠 URGENT - Process today, deadline approaching'
        else:
            return '🟡 PRIORITY - Schedule for processing'
    elif urgency == 'MEDIUM':
        return '🟡 NORMAL PRIORITY - Process within 48 hours'
    else:
        return '🟢 STANDARD - Regular processing queue'

def get_priority_score(urgency, has_deadline, days_until_deadline=None):
    """Calculate priority score (1-10) for sorting orders"""
    score = 0
    
    if urgency == 'HIGH':
        score += 5
    elif urgency == 'MEDIUM':
        score += 3
    
    if has_deadline:
        if days_until_deadline is not None:
            if days_until_deadline <= 1:
                score += 5
            elif days_until_deadline <= 3:
                score += 4
            elif days_until_deadline <= 5:
                score += 2
            else:
                score += 1
        else:
            score += 2
    
    return min(score, 10)  # Cap at 10

def analyze_customer_note(note_text):
    """Main function: Analyze customer note and return all results"""
    if not note_text or len(note_text.strip()) == 0:
        return {'error': 'Empty note provided'}
    
    urgency = detect_urgency(note_text)
    garments = extract_garments(note_text)
    event = extract_event(note_text)
    deadline = extract_deadline(note_text)
    sentiment = analyze_sentiment(note_text)
    
    days_until = deadline['days'] if deadline else None
    action = get_action_text(urgency, days_until)
    priority_score = get_priority_score(urgency, deadline is not None, days_until)
    
    return {
        'original_note': note_text,
        'urgency': urgency,
        'garments': garments,
        'event': event,
        'deadline': deadline,
        'sentiment': sentiment,
        'action': action,
        'priority_score': priority_score,
        'summary': {
            'has_urgency': urgency != 'LOW',
            'has_deadline': deadline is not None,
            'has_garments': len(garments) > 0 and garments != ['not specified']
        }
    }

# Test the functions
if __name__ == '__main__':
    test_notes = [
        "Need this suit by Friday for job interview, please rush!",
        "URGENT!!! My daughter's birthday is tomorrow, need the dress ASAP",
        "Take your time, no rush on this shirt for everyday wear",
        "Emergency: Need these pants hemmed today for a funeral tomorrow",
        "I need this wedding dress by Saturday for my wedding! So excited!",
        "Can I get this blazer overnight? Have an important meeting Monday morning",
        "This is just a regular order, no deadline"
    ]
    
    print("🧪 TESTING NLP FUNCTIONS")
    print("=" * 60)
    
    for note in test_notes:
        print(f"\n📝 Input: {note}")
        result = analyze_customer_note(note)
        print(f"   Urgency: {result['urgency']}")
        print(f"   Garments: {', '.join(result['garments'])}")
        print(f"   Event: {result['event']}")
        if result['deadline']:
            print(f"   Deadline: {result['deadline']['date']} ({result['deadline']['relative_time']})")
        print(f"   Sentiment: {result['sentiment']['sentiment_label']}")
        print(f"   Priority Score: {result['priority_score']}/10")
        print(f"   Action: {result['action']}")
        print("-" * 40)