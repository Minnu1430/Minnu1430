"""
NLP Engine - AI Extraction and Classification
"""

import re
import logging
import json
import spacy
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class NLPEngine:
    """Handle NLP-based extraction and classification of classified ads"""
    
    # Category keywords for classification
    CATEGORY_KEYWORDS = {
        'Real Estate': ['property', 'flat', 'apartment', 'house', 'plot', 'rent', 'sale', 'residential', 'commercial', 'office'],
        'Automobiles': ['car', 'vehicle', 'bike', 'motorcycle', 'scooter', 'truck', 'auto', 'drive', 'engine'],
        'Furniture': ['sofa', 'table', 'chair', 'bed', 'cabinet', 'desk', 'furniture', 'wooden'],
        'Electronics': ['mobile', 'phone', 'laptop', 'computer', 'tv', 'camera', 'electronic', 'gadget', 'appliance'],
        'Services': ['service', 'repair', 'cleaning', 'painting', 'plumbing', 'electrician', 'tutor', 'trainer'],
        'Jobs': ['job', 'hiring', 'employment', 'vacancy', 'position', 'requirement', 'career', 'recruit'],
        'Education': ['tuition', 'coaching', 'course', 'training', 'coaching center', 'classes', 'education'],
        'Health': ['medical', 'clinic', 'doctor', 'hospital', 'health', 'wellness', 'yoga', 'fitness'],
        'Events': ['event', 'catering', 'decoration', 'organizer', 'wedding', 'party', 'ceremony'],
        'Miscellaneous': ['wanted', 'buy', 'sell', 'exchange', 'lost', 'found', 'free'],
    }
    
    # Hyderabad areas/locations
    HYDERABAD_AREAS = {
        'Hyderabad', 'Telangana', 'GHMC',
        'Secunderabad', 'Banjara Hills', 'Jubilee Hills', 'Madhapur', 'Hitech City',
        'Begumpet', 'Kachiguda', 'Charminar', 'Hussain Sagar', 'Lakdikapool',
        'Kondapur', 'Gachibowli', 'Manikonda', 'Narsingi', 'Tellapur',
        'Kukatpally', 'Miyapur', 'Vasanthnagar', 'Jeedimetla', 'Suraram',
        'Shamshabad', 'Tandur', 'Choutuppal', 'Yacharam', 'Pedakakimidi',
        'Ameerpet', 'Himayatnagar', 'Rajbagh', 'Chaderghat', 'Shantinagar',
        'Malakpet', 'Tolichowki', 'Golconda', 'Fort', 'Falaknuma',
        'Habsiguda', 'Vikarabad', 'Tandoor', 'Medchal', 'Malkajgiri'
    }
    
    def __init__(self):
        try:
            self.nlp = spacy.load('en_core_web_sm')
            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """
        Extract contact information from text
        
        Args:
            text: Text to extract contact info from
        
        Returns:
            dict with phone and email
        """
        contact_info = {
            'phone_numbers': [],
            'emails': []
        }
        
        # Phone number patterns (Indian format)
        phone_patterns = [
            r'\b\d{10}\b',  # 10-digit
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # XXX-XXX-XXXX
            r'\+91[-.\s]?\d{10}\b',  # +91 format
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            contact_info['phone_numbers'].extend(phones)
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        contact_info['emails'].extend(emails)
        
        # Remove duplicates
        contact_info['phone_numbers'] = list(set(contact_info['phone_numbers']))
        contact_info['emails'] = list(set(contact_info['emails']))
        
        return contact_info
    
    def extract_location(self, text: str) -> str:
        """
        Extract location from text (Hyderabad specific)
        
        Args:
            text: Text to extract location from
        
        Returns:
            Location string or 'Unknown'
        """
        text_lower = text.lower()
        
        # Check for known areas
        for area in self.HYDERABAD_AREAS:
            if area.lower() in text_lower:
                return area
        
        # Try to extract named entities if spaCy is available
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ == 'GPE':  # Geopolitical entity
                    return ent.text
        
        return None
    
    def extract_date(self, text: str) -> str:
        """
        Extract date information from text
        
        Args:
            text: Text to extract date from
        
        Returns:
            Date string or None
        """
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # DD-MM-YYYY or MM-DD-YYYY
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',  # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        return None
    
    def classify_category(self, text: str, title: str = "") -> Tuple[str, float]:
        """
        Classify ad into category
        
        Args:
            text: Full text of the ad
            title: Title of the ad
        
        Returns:
            Tuple of (category, confidence_score)
        """
        combined_text = f"{title} {text}".lower()
        scores = {}
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # Weight title matches higher
                if keyword in title.lower():
                    score += 3
                if keyword in combined_text:
                    score += 1
            scores[category] = score
        
        if max(scores.values()) == 0:
            return 'Miscellaneous', 0.0
        
        best_category = max(scores, key=scores.get)
        confidence = min(scores[best_category] / 10, 1.0)
        
        return best_category, round(confidence, 2)
    
    def extract_title(self, text: str, max_length: int = 100) -> str:
        """
        Extract or generate title from text
        
        Args:
            text: Full ad text
            max_length: Maximum title length
        
        Returns:
            Title string
        """
        lines = text.split('\n')
        
        # Try first non-empty line as title
        for line in lines:
            cleaned = line.strip()
            if cleaned and len(cleaned) > 10 and len(cleaned) < max_length:
                return cleaned
        
        # Generate title from first few words
        words = text.split()[:15]
        title = ' '.join(words)
        
        if len(title) > max_length:
            title = title[:max_length] + '...'
        
        return title
    
    def extract_description(self, text: str, lines_to_skip: int = 1) -> str:
        """
        Extract description, skipping title line
        
        Args:
            text: Full ad text
            lines_to_skip: Number of lines to skip from beginning
        
        Returns:
            Description text
        """
        lines = text.split('\n')[lines_to_skip:]
        description = '\n'.join([line.strip() for line in lines if line.strip()])
        
        # Limit to reasonable length
        if len(description) > 5000:
            description = description[:5000] + '...'
        
        return description
    
    def detect_language(self, text: str) -> str:
        """
        Detect primary language of text
        
        Returns:
            'English', 'Telugu', or 'Mixed'
        """
        # Simple heuristic based on character ranges
        telugu_chars = re.findall(r'[\u0C00-\u0C7F]', text)
        english_chars = re.findall(r'[a-zA-Z]', text)
        
        total_chars = len(telugu_chars) + len(english_chars)
        if total_chars == 0:
            return 'Unknown'
        
        telugu_ratio = len(telugu_chars) / total_chars
        
        if telugu_ratio > 0.7:
            return 'Telugu'
        elif telugu_ratio > 0.3:
            return 'Mixed'
        else:
            return 'English'
    
    def remove_duplicates(self, texts: List[str]) -> List[str]:
        """
        Remove near-duplicate texts
        
        Args:
            texts: List of text strings
        
        Returns:
            List of unique texts
        """
        unique = []
        seen = set()
        
        for text in texts:
            # Normalize text
            normalized = re.sub(r'\s+', ' ', text.lower().strip())
            
            # Check similarity with existing entries
            is_duplicate = False
            for seen_text in seen:
                # Simple Levenshtein-like check
                if self._text_similarity(normalized, seen_text) > 0.9:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(text)
                seen.add(normalized)
        
        return unique
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity score 0-1"""
        if text1 == text2:
            return 1.0
        
        len1, len2 = len(text1), len(text2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Simple character overlap calculation
        common = sum(1 for i, c in enumerate(text1) if i < len2 and text2[i] == c)
        return common / max(len1, len2)
    
    def extract_all(self, text: str, title: str = None) -> Dict:
        """
        Extract all relevant information from ad text
        
        Args:
            text: Full ad text
            title: Optional title (if not in text)
        
        Returns:
            dict with all extracted information
        """
        if not title:
            title = self.extract_title(text)
        
        description = self.extract_description(text)
        category, confidence = self.classify_category(text, title)
        location = self.extract_location(text)
        date = self.extract_date(text)
        contact_info = self.extract_contact_info(text)
        language = self.detect_language(text)
        
        return {
            'title': title,
            'description': description,
            'category': category,
            'category_confidence': confidence,
            'location': location,
            'date': date,
            'contact_info': contact_info,
            'language': language,
            'raw_text': text,
        }


# Initialize NLP Engine
nlp_engine = NLPEngine()
