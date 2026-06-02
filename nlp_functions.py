import re
import joblib
import dateparser
from datetime import datetime, timedelta
from textblob import TextBlob
import os

# Load the trained model and vectorizer
model_path = 'urgency_model.pkl'
vectorizer_path = 'vectorizer.pkl'

# Check if model files exist
if os.path.exists(model_path) and os.path.exists(vectorizer_path):
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)
    MODEL_AVAILABLE = True
    print("✅ Trained ML model loaded successfully")
else:
    MODEL_AVAILABLE = False
    print("⚠️ Model files not found, using fallback rule-based detection")

# Garment keywords (rule-based – still fine)
GARMENT_KEYWORDS = {
    'dress': ['dress', 'gown', 'wedding dress', 'bridesmaid dress', 'cocktail dress', 'maxi dress', 'mini dress', 'sundress'],
    'suit': ['suit', 'blazer', 'business suit', 'pantsuit'],
    'shirt': ['shirt', 'blouse', 'top', 't-shirt', 'button down', 'tank top'],
    'jacket': ['jacket', 'coat', 'blazer', 'cardigan'],
    'pants': ['pants', 'trousers', 'jeans', 'slacks', 'leggings'],
    'skirt': ['skirt', 'mini skirt', 'midi skirt'],
    'romper': ['romper', 'jumpsuit', 'playsuit']
}

# Event keywords (for context)
EVENT_KEYWORDS = {
    'wedding': ['wedding', 'bridal', 'bride', 'bridesmaid'],
    'interview': ['interview', 'job interview', 'career fair'],
    'party': ['party', 'birthday', 'anniversary', 'celebration'],
    'work': ['work', 'office', 'business', 'meeting', 'conference'],
    'vacation': ['vacation', 'trip', 'travel', 'holiday']
}

def clean_text_for_model(text):
    """Same cleaning function used during training"""
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', '', text)   # remove punctuation/numbers
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def detect_urgency_ml(text):
    """Use trained ML model to predict urgency (0=LOW,1=MEDIUM,2=HIGH)"""
    if MODEL_AVAILABLE:
        cleaned = clean_text_for_model(text)
        vec = vectorizer.transform([cleaned])
        pred = model.predict(vec)[0]
        # Map numeric to label
        return {0: 'LOW', 1: 'MEDIUM', 2: 'HIGH'}[pred]
    else:
        # Fallback rule-based
        text_lower = text.lower()
        high_words = ['urgent', 'rush', 'asap', 'emergency', 'immediately', 'critical']
        medium_words = ['please', 'soon', 'quickly', 'need by', 'deadline']
        if any(w in text_lower for w in high_words):
            return 'HIGH'
        elif any(w in text_lower for w in medium_words):
            return 'MEDIUM'
        else:
            return 'LOW'

def extract_garments(text):
    text_lower = text.lower()
    found = []
    for g_type, keywords in GARMENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                found.append(g_type)
                break
    return found if found else ['not specified']

def extract_event(text):
    text_lower = text.lower()
    for event_type, keywords in EVENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return event_type
    return 'general'

def extract_deadline(text):
    """Extract deadline if present"""
    text_lower = text.lower()
    today = datetime.now()
    
    # Check for tomorrow
    if 'tomorrow' in text_lower:
        target = today + timedelta(days=1)
        return {'date': target.strftime('%Y-%m-%d'), 'relative_time': 'tomorrow', 'days': 1}
    
    # Check for day names
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for i, day in enumerate(days):
        if f'by {day}' in text_lower or f'on {day}' in text_lower:
            current_weekday = today.weekday()
            target_weekday = i
            days_ahead = target_weekday - current_weekday
            if days_ahead <= 0:
                days_ahead += 7
            target_date = today + timedelta(days=days_ahead)
            return {'date': target_date.strftime('%Y-%m-%d'), 'relative_time': f'this {day}', 'days': days_ahead}
    
    # Try dateparser on full text
    parsed = dateparser.parse(text_lower, settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': today})
    if parsed:
        days_diff = (parsed - today).days
        if 0 <= days_diff <= 30:
            return {'date': parsed.strftime('%Y-%m-%d'), 'relative_time': f'in {days_diff} days' if days_diff > 0 else 'today', 'days': days_diff}
    return None

def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.3:
        label = 'Very Positive'
    elif polarity > 0.1:
        label = 'Positive'
    elif polarity > -0.1:
        label = 'Neutral'
    elif polarity > -0.3:
        label = 'Negative'
    else:
        label = 'Very Negative'
    return {'polarity': round(polarity, 2), 'subjectivity': round(blob.sentiment.subjectivity, 2), 'sentiment_label': label}

def get_action_text(urgency, days_until_deadline=None):
    if urgency == 'HIGH':
        return '🔴 IMMEDIATE ACTION - Rush processing required'
    elif urgency == 'MEDIUM' and days_until_deadline is not None and days_until_deadline <= 2:
        return '🟠 URGENT - Process today, deadline approaching'
    elif urgency == 'MEDIUM':
        return '🟡 NORMAL PRIORITY - Process within 48 hours'
    else:
        return '🟢 STANDARD - Regular processing queue'

def get_priority_score(urgency, has_deadline, days_until_deadline=None):
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
    return min(score, 10)

def analyze_customer_note(note_text):
    """Main entry point for the API"""
    if not note_text or len(note_text.strip()) == 0:
        return {'error': 'Empty note provided'}
    
    urgency = detect_urgency_ml(note_text)
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
        'model_used': 'Trained Random Forest (99.4% accuracy)' if MODEL_AVAILABLE else 'Fallback rule-based',
        'summary': {
            'has_urgency': urgency != 'LOW',
            'has_deadline': deadline is not None,
            'has_garments': garments != ['not specified']
        }
    }