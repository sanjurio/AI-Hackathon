import os
import logging
from openai import OpenAI
from models import Category
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = None
openai_api_key = os.getenv('OPENAI_API_KEY')

if openai_api_key:
    client = OpenAI(api_key=openai_api_key)
    logger.info("✓ OpenAI client initialized successfully with API key")
else:
    logger.warning("✗ No OPENAI_API_KEY found - will use keyword/TF-IDF fallback only")

def classify_ticket_with_openai(description):
    if not client:
        logger.warning("OpenAI client not initialized - skipping AI classification")
        return None
    
    categories = Category.query.all()
    if not categories:
        logger.warning("No categories found in database")
        return None
    
    category_info = "\n".join([
        f"- {cat.name}: {cat.description} (Keywords: {cat.keywords})"
        for cat in categories
    ])
    
    try:
        logger.info(f"🤖 CALLING OpenAI GPT-3.5-turbo for ticket classification...")
        logger.info(f"   Ticket description: '{description[:100]}...'")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a ticket classification assistant. Based on the ticket description, classify it into one of the available categories. Respond with ONLY the category name, nothing else."
                },
                {
                    "role": "user",
                    "content": f"Available categories:\n{category_info}\n\nTicket description: {description}\n\nWhich category does this ticket belong to?"
                }
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        classified_category = response.choices[0].message.content.strip()
        logger.info(f"✅ OpenAI response: '{classified_category}'")
        
        for cat in categories:
            if cat.name.lower() in classified_category.lower():
                logger.info(f"✅ AI CLASSIFIED as: {cat.name} (using OpenAI GPT-3.5-turbo)")
                return cat
        
        logger.warning(f"OpenAI returned '{classified_category}' but no matching category found")
        return categories[0] if categories else None
    
    except Exception as e:
        logger.error(f"❌ OpenAI classification error: {e}")
        logger.info("Will fallback to keyword-based classification")
        return None

def classify_ticket_with_keywords(description):
    categories = Category.query.all()
    if not categories:
        return None
    
    description_lower = description.lower()
    best_match = None
    max_matches = 0
    
    for category in categories:
        if category.keywords:
            keywords = [kw.strip().lower() for kw in category.keywords.split(',')]
            matches = sum(1 for keyword in keywords if keyword in description_lower)
            
            if matches > max_matches:
                max_matches = matches
                best_match = category
    
    if best_match and max_matches > 0:
        return best_match
    
    if categories:
        category_texts = []
        for cat in categories:
            text = f"{cat.name} {cat.description} {cat.keywords or ''}"
            category_texts.append(text)
        
        try:
            vectorizer = TfidfVectorizer(stop_words='english')
            all_texts = category_texts + [description]
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
            best_idx = similarities.argmax()
            
            if similarities[best_idx] > 0.1:
                return categories[best_idx]
        except:
            pass
    
    return categories[0] if categories else None

def classify_ticket(description):
    logger.info("="*60)
    logger.info("TICKET CLASSIFICATION STARTED")
    logger.info("="*60)
    
    if client:
        logger.info("Attempting AI classification with OpenAI...")
        result = classify_ticket_with_openai(description)
        if result:
            logger.info(f"✅ USING AI CLASSIFICATION: {result.name}")
            logger.info("="*60)
            return result, True
        else:
            logger.warning("OpenAI classification failed, falling back to keyword matching")
    else:
        logger.warning("No OpenAI client available, using keyword fallback")
    
    logger.info("Using keyword-based classification...")
    result = classify_ticket_with_keywords(description)
    if result:
        logger.info(f"📝 USING KEYWORD CLASSIFICATION: {result.name}")
    else:
        logger.warning("⚠️  No classification result")
    logger.info("="*60)
    return result, False
