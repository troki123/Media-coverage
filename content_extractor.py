import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse

# Optional imports with fallbacks
try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False
    print("newspaper3k not available. Install with: pip install newspaper3k")

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    print("trafilatura not available. Install with: pip install trafilatura")


def extract_with_newspaper(url, max_length=10000):
    """
    Extract article content using newspaper3k library.
    Best for news articles.
    
    Args:
        url (str): Article URL
        max_length (int): Maximum character length of content
    
    Returns:
        tuple: (content, published_date) or (None, None) if failed
    """
    if not NEWSPAPER_AVAILABLE:
        return None, None
    
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        content = article.text
        published_date = article.publish_date
        
        # Limit content length
        if content and len(content) > max_length:
            content = content[:max_length] + "..."
        
        # Convert date to string if it exists
        if published_date:
            published_date = published_date.strftime('%Y-%m-%d')
        
        return content, published_date
    
    except Exception as e:
        print(f"Newspaper extraction failed for {url}: {e}")
        return None, None


def extract_with_trafilatura(url, max_length=10000):
    """
    Extract article content using trafilatura library.
    Good for large-scale extraction.
    
    Args:
        url (str): Article URL
        max_length (int): Maximum character length of content
    
    Returns:
        tuple: (content, None) or (None, None) if failed
    """
    if not TRAFILATURA_AVAILABLE:
        return None, None
    
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            content = trafilatura.extract(downloaded)
            if content and len(content) > 100:
                if len(content) > max_length:
                    content = content[:max_length] + "..."
                return content, None
        return None, None
    
    except Exception as e:
        print(f"Trafilatura extraction failed for {url}: {e}")
        return None, None


def extract_with_beautifulsoup(url, max_length=10000):
    """
    Fallback extraction using requests and BeautifulSoup.
    
    Args:
        url (str): Article URL
        max_length (int): Maximum character length of content
    
    Returns:
        tuple: (content, None) or (None, None) if failed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        # Try to find main content area
        main_content = None
        for selector in ['article', 'main', '.article-content', '.post-content', '.entry-content', '#content']:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no specific content area found, use body
        if not main_content:
            main_content = soup.body
        
        # Get text
        text = main_content.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text if len(text) > 200 else None, None
    
    except Exception as e:
        print(f"BeautifulSoup extraction failed for {url}: {e}")
        return None, None


def extract_article_content(url, method='auto', max_length=10000):
    """
    Main function to extract article content with multiple fallback methods.
    
    Args:
        url (str): Article URL
        method (str): Extraction method - 'newspaper', 'trafilatura', 'bs4', or 'auto'
        max_length (int): Maximum character length of content
    
    Returns:
        tuple: (content, published_date) or (None, None) if extraction fails
    """
    print(f"Extracting content from: {url[:80]}...")
    
    content = None
    published_date = None
    
    # Try specified method first
    if method == 'newspaper':
        content, published_date = extract_with_newspaper(url, max_length)
        if content:
            return content, published_date
            
    elif method == 'trafilatura':
        content, published_date = extract_with_trafilatura(url, max_length)
        if content:
            return content, published_date
            
    elif method == 'bs4':
        content, published_date = extract_with_beautifulsoup(url, max_length)
        if content:
            return content, published_date
            
    elif method == 'auto':
        # Try methods in order of preference
        if NEWSPAPER_AVAILABLE:
            content, published_date = extract_with_newspaper(url, max_length)
            if content:
                return content, published_date
        
        if TRAFILATURA_AVAILABLE:
            content, published_date = extract_with_trafilatura(url, max_length)
            if content:
                return content, published_date
        
        content, published_date = extract_with_beautifulsoup(url, max_length)
        if content:
            return content, published_date
    
    print(f"❌ All extraction methods failed for: {url}")
    return None, None


def extract_multiple_articles(urls, delay=1, method='auto', max_length=10000):
    """
    Extract content from multiple articles with delay between requests.
    
    Args:
        urls (list): List of article URLs
        delay (float): Seconds to wait between requests
        method (str): Extraction method
        max_length (int): Maximum content length
    
    Returns:
        dict: Dictionary with URL as key and (content, published_date) as value
    """
    results = {}
    
    for idx, url in enumerate(urls, 1):
        print(f"Processing article {idx}/{len(urls)}")
        
        content, published_date = extract_article_content(url, method, max_length)
        results[url] = {
            'content': content,
            'published_date': published_date,
            'success': content is not None
        }
        
        if idx < len(urls):  # Don't delay after last request
            time.sleep(delay)
    
    return results


def is_valid_url(url):
    """
    Check if URL is valid.
    
    Args:
        url (str): URL to validate
    
    Returns:
        bool: True if URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def get_domain_from_url(url):
    """
    Extract domain name from URL.
    
    Args:
        url (str): Article URL
    
    Returns:
        str: Domain name or None
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return None


# Optional: Cache for extracted content to avoid re-extracting
class ContentCache:
    """Simple cache for extracted content to avoid duplicate work."""
    
    def __init__(self):
        self.cache = {}
    
    def get(self, url):
        return self.cache.get(url)
    
    def set(self, url, content, published_date):
        self.cache[url] = {'content': content, 'published_date': published_date}
    
    def clear(self):
        self.cache.clear()
    
    def size(self):
        return len(self.cache)


# Create a global cache instance
content_cache = ContentCache()


def extract_article_content_with_cache(url, method='auto', max_length=10000, use_cache=True):
    """
    Extract article content with caching to avoid re-extracting same URLs.
    
    Args:
        url (str): Article URL
        method (str): Extraction method
        max_length (int): Maximum content length
        use_cache (bool): Whether to use cache
    
    Returns:
        tuple: (content, published_date)
    """
    if use_cache:
        cached = content_cache.get(url)
        if cached:
            print(f"Using cached content for: {url[:80]}...")
            return cached['content'], cached['published_date']
    
    content, published_date = extract_article_content(url, method, max_length)
    
    if use_cache and content:
        content_cache.set(url, content, published_date)
    
    return content, published_date