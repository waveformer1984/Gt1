"""
Sample Plugin for BallsDeepNit System
Demonstrates plugin architecture and provides example functionality.
"""

__version__ = "1.0.0"
__author__ = "ProtoForge Development Team"
__description__ = "Sample plugin demonstrating text processing and analysis capabilities"

import time
import json
from typing import Dict, List, Any


def analyze_text(text: str) -> Dict[str, Any]:
    """
    Analyze text and return various metrics.
    
    Args:
        text (str): Text to analyze
        
    Returns:
        Dict containing analysis results
    """
    words = text.split()
    sentences = text.split('.')
    
    return {
        "word_count": len(words),
        "sentence_count": len([s for s in sentences if s.strip()]),
        "character_count": len(text),
        "character_count_no_spaces": len(text.replace(" ", "")),
        "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
        "longest_word": max(words, key=len) if words else "",
        "analysis_timestamp": time.time()
    }


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract potential keywords from text.
    
    Args:
        text (str): Text to process
        max_keywords (int): Maximum number of keywords to return
        
    Returns:
        List of potential keywords
    """
    # Simple keyword extraction (in production, use proper NLP)
    words = text.lower().split()
    
    # Filter out common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
    
    keywords = [word.strip('.,!?;:"()[]{}') for word in words if word not in stop_words and len(word) > 3]
    
    # Count frequency
    word_freq = {}
    for word in keywords:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_keywords[:max_keywords]]


def generate_summary(text: str, max_sentences: int = 3) -> str:
    """
    Generate a simple summary of the text.
    
    Args:
        text (str): Text to summarize
        max_sentences (int): Maximum sentences in summary
        
    Returns:
        Summary string
    """
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    
    if len(sentences) <= max_sentences:
        return '. '.join(sentences) + '.'
    
    # Simple scoring based on sentence length and position
    scored_sentences = []
    for i, sentence in enumerate(sentences):
        score = len(sentence.split())  # Word count score
        if i < 2:  # Boost early sentences
            score *= 1.5
        scored_sentences.append((score, sentence))
    
    # Sort by score and take top sentences
    scored_sentences.sort(reverse=True)
    top_sentences = [sent for score, sent in scored_sentences[:max_sentences]]
    
    return '. '.join(top_sentences) + '.'


def health_check() -> Dict[str, Any]:
    """
    Plugin health check function.
    
    Returns:
        Dict with health status information
    """
    return {
        "status": "healthy",
        "plugin_name": "sample_plugin",
        "version": __version__,
        "last_check": time.time(),
        "capabilities": [
            "text_analysis",
            "keyword_extraction", 
            "text_summarization",
            "health_monitoring"
        ]
    }


def on_reload():
    """
    Called when the plugin is hot-reloaded.
    Perform any necessary cleanup or reinitialization.
    """
    print(f"Sample plugin v{__version__} reloaded successfully at {time.time()}")


def process_batch(texts: List[str]) -> List[Dict[str, Any]]:
    """
    Process multiple texts in batch.
    
    Args:
        texts (List[str]): List of texts to process
        
    Returns:
        List of analysis results
    """
    results = []
    
    for i, text in enumerate(texts):
        try:
            analysis = analyze_text(text)
            keywords = extract_keywords(text)
            summary = generate_summary(text)
            
            results.append({
                "index": i,
                "analysis": analysis,
                "keywords": keywords,
                "summary": summary,
                "success": True
            })
        except Exception as e:
            results.append({
                "index": i,
                "error": str(e),
                "success": False
            })
    
    return results


# Plugin configuration
PLUGIN_CONFIG = {
    "name": "sample_plugin",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "endpoints": {
        "analyze": "analyze_text",
        "keywords": "extract_keywords",
        "summarize": "generate_summary",
        "health": "health_check",
        "batch": "process_batch"
    },
    "required_params": {
        "analyze_text": ["text"],
        "extract_keywords": ["text"],
        "generate_summary": ["text"],
        "process_batch": ["texts"]
    }
}


if __name__ == "__main__":
    # Test the plugin functions
    test_text = """
    ProtoForge is an innovative technology platform that combines artificial intelligence, 
    hardware design, and software development. The system provides comprehensive solutions 
    for rapid prototyping and development across multiple domains including aerospace, 
    biomedical research, and entertainment applications.
    """
    
    print("=== Sample Plugin Test ===")
    print(f"Analysis: {json.dumps(analyze_text(test_text), indent=2)}")
    print(f"Keywords: {extract_keywords(test_text)}")
    print(f"Summary: {generate_summary(test_text)}")
    print(f"Health: {json.dumps(health_check(), indent=2)}")