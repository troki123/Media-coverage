# article_extractor.py
import sqlite3
import requests
from newspaper import Article
from bs4 import BeautifulSoup
import time
import logging

logger = logging.getLogger(__name__)

class ArticleExtractor:
    """Extracts full content from news articles"""
    
    # Initializes a new ArticleExtractor object
    def __init__(self, timeout = 10, user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'):
        self.timeout = timeout
        self.headers = {'User-Agent': user_agent}
        
    # Extracts all the article contents using newspaper3k library
    def extract_article_content(self, url):
        """
        Extract full article content using newspaper3k
        Returns dict with title, text, summary, and metadata
        """
        try:
            # Creates na article object
            article = Article(url, timeout = self.timeout)
            
            article.download()
            article.parse()
            
            # Extracts additional metadata
            result = {
                'title': article.title,
                'content': article.text,
                'summary': article.summary,
                'authors': ', '.join(article.authors),
                'publish_date': str(article.publish_date) if article.publish_date else None,
                'top_image': article.top_image,
                'keywords': ', '.join(article.keywords),
                'extraction_success': True
            }
            
            # If the newspaper's summary is empty
            # Try to get a better summary
            if not result['summary'] and result['content']:
                result['summary'] = self._generate_fallback_summary(result['content'])
                
            logger.info(f"Successfully extracted content from {url}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {str(e)}")
            return {
                'title': None,
                'content': None,
                'summary': None,
                'authors': None,
                'publish_date': None,
                'top_image': None,
                'keywords': None,
                'extraction_success': False,
                'error': str(e)
            }
    
    # Creates a simple summary when newspaper3k fails to generate one
    def _generate_fallback_summary(self, text, max_sentences=3):
        """Generate a simple summary by taking first few sentences"""
        sentences = text.split('. ')
        summary = '. '.join(sentences[:max_sentences])
        return summary + '.' if summary else text[:500]
    
    # Multiple methods to extract contnet
    def extract_with_fallback(self, url):
        """
        Try multiple methods to extract content
        Falls back to BeautifulSoup if newspaper3k fails
        """
        # Extract with newspaper3k
        result = self.extract_article_content(url)
        
        if result['extraction_success'] and result['content']:
            return result
        
        # Fallback to BeautifulSoup
        logger.info(f"Using BeautifulSoup fallback for {url}")
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Try to find main content
            content_selectors = [
                'article', '.article-content', '.post-content', 
                '.entry-content', 'main', '.content', '#content'
            ]
            
            content_text = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content_text = ' '.join([elem.get_text(strip=True) for elem in elements])
                    break
            
            if not content_text:
                # Get all paragraphs as fallback
                paragraphs = soup.find_all('p')
                content_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            # Clean up text
            content_text = ' '.join(content_text.split())
            
            result['content'] = content_text
            result['summary'] = self._generate_fallback_summary(content_text)
            result['extraction_success'] = True
            
        except Exception as e:
            logger.error(f"Fallback extraction failed for {url}: {str(e)}")
            result['error'] = str(e)
            
        return result

# Updates mutliple database records with exctracted content
def update_database_with_content(search_id, max_articles=None):
    """
    Updates existing database entries with full article content
    """
    extractor = ArticleExtractor()
    conn = sqlite3.connect("database/app.db")
    cursor = conn.cursor()
    
    # Get articles without content or summary
    query = """
        SELECT id, link, media_name 
        FROM media_news 
        WHERE search_id = ? AND (content IS NULL OR summary IS NULL)
    """
    
    if max_articles:
        query += " LIMIT ?"
        cursor.execute(query, (search_id, max_articles))
    else:
        cursor.execute(query, (search_id,))
    
    articles = cursor.fetchall()
    
    if not articles:
        logger.info(f"No articles found needing content extraction for search_id {search_id}")
        conn.close()
        return 0
    
    logger.info(f"Extracting content for {len(articles)} articles...")
    updated_count = 0
    
    for article_id, url, title in articles:
        print(f"📰 Processing: {title[:50]}...")
        
        # Extract content
        result = extractor.extract_with_fallback(url)
        
        if result['extraction_success'] and result['content']:
            # Update database
            cursor.execute("""
                UPDATE media_news 
                SET content = ?, summary = ?
                WHERE id = ?
            """, (result['content'][:10000], result['summary'][:500], article_id))
            
            conn.commit()
            updated_count += 1
            print(f"✅ Extracted {len(result['content'])} characters")
        else:
            print(f"❌ Failed to extract content")
        
        # Be respectful - add delay between requests
        time.sleep(1)
    
    conn.close()
    return updated_count

def extract_and_save_new_article(search_id, url, title):
    """
    Extract content for a single new article and save to database
    """
    extractor = ArticleExtractor()
    result = extractor.extract_with_fallback(url)
    
    conn = sqlite3.connect("database/app.db")
    cursor = conn.cursor()
    
    if result['extraction_success'] and result['content']:
        # Check if article already exists
        cursor.execute("""
            SELECT id FROM media_news 
            WHERE search_id = ? AND link = ?
        """, (search_id, url))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute("""
                UPDATE media_news 
                SET content = ?, summary = ?, media_name = ?
                WHERE id = ?
            """, (result['content'][:10000], result['summary'][:500], title, existing[0]))
        else:
            # Insert new record with content
            cursor.execute("""
                INSERT INTO media_news (search_id, media_name, link, content, summary)
                VALUES (?, ?, ?, ?, ?)
            """, (search_id, title, url, result['content'][:10000], result['summary'][:500]))
        
        conn.commit()
        success = True
    else:
        # Insert without content
        cursor.execute("""
            INSERT INTO media_news (search_id, media_name, link)
            VALUES (?, ?, ?)
        """, (search_id, title, url))
        conn.commit()
        success = False
    
    conn.close()
    return success, result