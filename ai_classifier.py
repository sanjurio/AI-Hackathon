import os
from openai import OpenAI
from models import Category
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

client = None
openai_api_key = os.getenv('OPENAI_API_KEY')

if openai_api_key:
    client = OpenAI(api_key=openai_api_key)

def classify_ticket_with_openai(description):
    if not client:
        return None
    
    categories = Category.query.all()
    if not categories:
        return None
    
    category_info = "\n".join([
        f"- {cat.name}: {cat.description} (Keywords: {cat.keywords})"
        for cat in categories
    ])
    
    try:
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
        
        for cat in categories:
            if cat.name.lower() in classified_category.lower():
                return cat
        
        return categories[0] if categories else None
    
    except Exception as e:
        print(f"OpenAI classification error: {e}")
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
    if client:
        result = classify_ticket_with_openai(description)
        if result:
            return result
    
    return classify_ticket_with_keywords(description)
