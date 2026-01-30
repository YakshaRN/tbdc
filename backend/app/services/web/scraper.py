"""
Web scraping service to extract company information from websites.

Fetches and parses website content to extract relevant metadata
for lead qualification when no matching leads are found.
"""
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urljoin
import httpx
from bs4 import BeautifulSoup
from loguru import logger


class WebScraperService:
    """
    Service to scrape and extract company information from websites.
    
    Extracts:
    - Company name (from title, meta tags, or headings)
    - Description (from meta description or content)
    - Industry hints
    - Contact information
    - Social media links
    """
    
    def __init__(self):
        self.timeout = 15.0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    def is_valid_url(self, url: str) -> bool:
        """Check if a string is a valid URL."""
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL by adding protocol if missing."""
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    async def fetch_website_data(self, url: str) -> Dict[str, Any]:
        """
        Fetch and extract data from a website.
        
        Args:
            url: The website URL to scrape
            
        Returns:
            Dictionary containing extracted website information
        """
        url = self.normalize_url(url)
        
        if not self.is_valid_url(url):
            return {
                "success": False,
                "error": "Invalid URL format",
                "url": url,
            }
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                html_content = response.text
                final_url = str(response.url)
                
                # Parse the HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract data
                data = self._extract_metadata(soup, final_url)
                data["success"] = True
                data["url"] = final_url
                data["original_url"] = url
                
                logger.info(f"Successfully scraped website: {url}")
                return data
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout while fetching {url}")
            return {
                "success": False,
                "error": "Request timed out",
                "url": url,
            }
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error for {url}: {e.response.status_code}")
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
                "url": url,
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
            }
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from parsed HTML."""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace('www.', '')
        
        # Extract title
        title = self._get_title(soup)
        
        # Extract company name
        company_name = self._get_company_name(soup, domain)
        
        # Extract description
        description = self._get_description(soup)
        
        # Extract keywords/industry hints
        keywords = self._get_keywords(soup)
        
        # Extract contact info
        contact_info = self._extract_contact_info(soup)
        
        # Extract social links
        social_links = self._extract_social_links(soup, url)
        
        # Extract logo
        logo_url = self._get_logo(soup, url)
        
        return {
            "company_name": company_name,
            "title": title,
            "description": description,
            "domain": domain,
            "keywords": keywords,
            "email": contact_info.get("email"),
            "phone": contact_info.get("phone"),
            "address": contact_info.get("address"),
            "social_links": social_links,
            "logo_url": logo_url,
        }
    
    def _get_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        # Try og:title first
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
        # Try regular title
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        
        return None
    
    def _get_company_name(self, soup: BeautifulSoup, domain: str) -> str:
        """Extract company name from various sources."""
        # Try og:site_name
        og_site = soup.find('meta', property='og:site_name')
        if og_site and og_site.get('content'):
            return og_site['content'].strip()
        
        # Try schema.org Organization
        schema_script = soup.find('script', type='application/ld+json')
        if schema_script:
            try:
                import json
                schema_data = json.loads(schema_script.string)
                if isinstance(schema_data, dict):
                    if schema_data.get('@type') == 'Organization':
                        if schema_data.get('name'):
                            return schema_data['name']
                    elif schema_data.get('@type') == 'WebSite':
                        if schema_data.get('name'):
                            return schema_data['name']
            except:
                pass
        
        # Try h1 as company name
        h1 = soup.find('h1')
        if h1 and h1.get_text(strip=True):
            text = h1.get_text(strip=True)
            if len(text) < 100:  # Reasonable length for a company name
                return text
        
        # Fall back to domain name
        return domain.split('.')[0].title()
    
    def _get_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page description."""
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try og:description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Try first paragraph
        first_p = soup.find('p')
        if first_p:
            text = first_p.get_text(strip=True)
            if len(text) > 50:
                return text[:500] + '...' if len(text) > 500 else text
        
        return None
    
    def _get_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract keywords/industry hints."""
        keywords = []
        
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords.extend([k.strip() for k in meta_keywords['content'].split(',')])
        
        # Limit to first 10
        return keywords[:10] if keywords else []
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """Extract contact information."""
        contact = {
            "email": None,
            "phone": None,
            "address": None,
        }
        
        # Find email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_links = soup.find_all('a', href=re.compile(r'^mailto:'))
        if email_links:
            href = email_links[0].get('href', '')
            match = re.search(email_pattern, href)
            if match:
                contact["email"] = match.group()
        else:
            # Search in text
            text = soup.get_text()
            match = re.search(email_pattern, text)
            if match:
                contact["email"] = match.group()
        
        # Find phone
        phone_links = soup.find_all('a', href=re.compile(r'^tel:'))
        if phone_links:
            phone = phone_links[0].get('href', '').replace('tel:', '')
            contact["phone"] = phone
        
        return contact
    
    def _extract_social_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, str]:
        """Extract social media links."""
        social_patterns = {
            "linkedin": r'linkedin\.com',
            "twitter": r'(twitter\.com|x\.com)',
            "facebook": r'facebook\.com',
            "instagram": r'instagram\.com',
            "youtube": r'youtube\.com',
        }
        
        social_links = {}
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            for platform, pattern in social_patterns.items():
                if platform not in social_links and re.search(pattern, href, re.I):
                    social_links[platform] = href
                    break
        
        return social_links
    
    def _get_logo(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract logo URL."""
        # Try og:image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return urljoin(base_url, og_image['content'])
        
        # Try finding logo in img tags
        logo_img = soup.find('img', attrs={'class': re.compile(r'logo', re.I)})
        if logo_img and logo_img.get('src'):
            return urljoin(base_url, logo_img['src'])
        
        # Try finding by alt text
        logo_img = soup.find('img', attrs={'alt': re.compile(r'logo', re.I)})
        if logo_img and logo_img.get('src'):
            return urljoin(base_url, logo_img['src'])
        
        return None


# Global instance
website_scraper = WebScraperService()
