import os
import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
import logging
from bs4 import BeautifulSoup
import bleach
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class AIAgentService:
    """AI Agent service for automated financial market research and reporting with enhanced security"""

    # Input validation patterns
    QUERY_PATTERN = re.compile(r'^[a-zA-Z0-9\s\.,!?\-\(\)\[\]\'\"]+$', re.MULTILINE)
    MAX_QUERY_LENGTH = 1000
    MAX_RESULTS = 10
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1

    # Allowed domains for web scraping
    ALLOWED_DOMAINS = {
        'investing.com',
        'forexlive.com',
        'fxstreet.com',
        'bloomberg.com',
        'reuters.com',
        'cnbc.com',
        'marketwatch.com'
    }

    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.search_api_key = os.getenv('GOOGLE_SEARCH_API_KEY', '')
        self.search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID', '')
        self.use_crawl4ai = os.getenv('USE_CRAWL4AI', 'false').lower() == 'true'

        # Validate API keys
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY not set - AI analysis will be limited")

    def _sanitize_input(self, text: str, max_length: int = MAX_QUERY_LENGTH) -> str:
        """Sanitize and validate input text"""
        if not isinstance(text, str):
            raise ValueError("Input must be a string")

        # Remove null bytes and control characters
        text = text.replace('\x00', '').replace('\r', '').replace('\n', ' ')

        # Limit length
        text = text[:max_length]

        # Basic sanitization - remove potentially dangerous characters
        text = bleach.clean(text, tags=[], attributes={}, strip=True)

        # Validate against pattern
        if not self.QUERY_PATTERN.match(text):
            raise ValueError("Input contains invalid characters")

        return text.strip()

    def _validate_url(self, url: str) -> bool:
        """Validate URL for security"""
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ['http', 'https'] and
                parsed.netloc and
                any(domain in parsed.netloc for domain in self.ALLOWED_DOMAINS)
            )
        except:
            return False

    def research_financial_markets(self, query: str, max_results: int = 5) -> Dict:
        """
        Perform automated financial market research using AI and web search with security validation

        Args:
            query: Research query (e.g., "Analyze current EURUSD trends")
            max_results: Maximum number of research results to return

        Returns:
            Dict containing research results and analysis
        """
        try:
            # Validate and sanitize inputs
            sanitized_query = self._sanitize_input(query)
            max_results = min(max(max_results, 1), self.MAX_RESULTS)

            logger.info(f"Processing AI research query: {sanitized_query[:50]}...")

            # Step 1: Gather web data using preferred method
            web_data = []
            if self.use_crawl4ai:
                web_data = self._gather_web_data_secure(sanitized_query, max_results)
            elif self.search_api_key:
                web_data = self._gather_web_data_google_secure(sanitized_query, max_results)

            # Step 2: Generate AI analysis with rate limiting
            analysis = self._generate_ai_analysis_secure(sanitized_query, web_data)

            # Step 3: Structure the response
            result = {
                "success": True,
                "query": sanitized_query,
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis,
                "web_sources": web_data,
                "recommendations": self._generate_recommendations(analysis),
                "disclaimer": "This analysis is for informational purposes only and should not be considered financial advice."
            }

            logger.info(f"AI research completed successfully for query: {sanitized_query[:30]}...")
            return result

        except ValueError as e:
            logger.warning(f"Input validation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Invalid input: {str(e)}",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in financial research: {str(e)}")
            return {
                "success": False,
                "error": "Research service temporarily unavailable",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }

    def _gather_web_data_google_secure(self, query: str, max_results: int) -> List[Dict]:
        """Gather relevant financial data using Google Custom Search API with security"""
        try:
            # Validate query
            if not query or len(query) > 200:
                return []

            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.search_api_key,
                'cx': self.search_engine_id,
                'q': f"{query} financial analysis market trends -site:pinterest.com -site:facebook.com",
                'num': min(max_results, 5),
                'dateRestrict': 'd7',  # Last 7 days
                'safe': 'active'  # Safe search
            }

            # Rate limiting
            time.sleep(self.RETRY_DELAY)

            response = requests.get(
                search_url,
                params=params,
                timeout=self.REQUEST_TIMEOUT,
                headers={'User-Agent': 'Financial-Analysis-Bot/1.0'}
            )
            response.raise_for_status()

            results = response.json().get('items', [])

            web_data = []
            for item in results[:max_results]:
                title = item.get('title', '')[:100]  # Limit title length
                url = item.get('link', '')
                snippet = item.get('snippet', '')[:300]  # Limit snippet length

                # Validate URL
                if self._validate_url(url):
                    web_data.append({
                        "title": bleach.clean(title, tags=[], strip=True),
                        "url": url,
                        "snippet": bleach.clean(snippet, tags=[], strip=True),
                        "source": item.get('displayLink', ''),
                        "method": "google_search"
                    })

            return web_data

        except requests.exceptions.RequestException as e:
            logger.warning(f"Google search failed: {str(e)}")
            return []
        except Exception as e:
            logger.warning(f"Google search error: {str(e)}")
            return []

    def _gather_web_data_secure(self, query: str, max_results: int) -> List[Dict]:
        """Gather relevant financial data using secure web scraping"""
        try:
            # Define trusted financial news sources
            financial_sources = [
                {
                    "url": "https://www.investing.com/news/forex-news",
                    "name": "Investing.com"
                },
                {
                    "url": "https://www.forexlive.com/",
                    "name": "ForexLive"
                },
                {
                    "url": "https://www.fxstreet.com/",
                    "name": "FXStreet"
                }
            ]

            web_data = []
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            for source in financial_sources[:min(max_results, 3)]:  # Limit sources
                if not self._validate_url(source["url"]):
                    continue

                try:
                    # Rate limiting between requests
                    time.sleep(self.RETRY_DELAY)

                    response = requests.get(
                        source["url"],
                        headers=headers,
                        timeout=self.REQUEST_TIMEOUT,
                        verify=True  # SSL verification
                    )
                    response.raise_for_status()

                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Extract title safely
                    title_elem = soup.find('title')
                    title = title_elem.get_text().strip()[:100] if title_elem else source["name"]

                    # Extract headlines safely - only from specific tags
                    headlines = []
                    allowed_tags = ['h1', 'h2', 'h3', 'a']

                    for tag in allowed_tags:
                        elements = soup.find_all(tag, limit=10)  # Limit elements
                        for elem in elements:
                            text = elem.get_text().strip()
                            # Filter for substantial financial content
                            if (len(text) > 15 and len(text) < 150 and
                                any(keyword in text.lower() for keyword in
                                    ['forex', 'currency', 'market', 'trading', 'price', 'analysis'])):
                                # Clean the text
                                text = bleach.clean(text, tags=[], strip=True)
                                headlines.append(text)

                    # Create content snippet
                    content_snippet = " | ".join(headlines[:3]) if headlines else f"Latest financial news from {source['name']}"

                    web_data.append({
                        "title": title,
                        "url": source["url"],
                        "snippet": content_snippet[:500],  # Limit length
                        "source": source["name"],
                        "method": "web_scraping",
                        "scrape_timestamp": datetime.now().isoformat()
                    })

                except requests.exceptions.RequestException as e:
                    logger.warning(f"Failed to scrape {source['url']}: {str(e)}")
                    continue
                except Exception as e:
                    logger.warning(f"Scraping error for {source['url']}: {str(e)}")
                    continue

            return web_data[:max_results]

        except Exception as e:
            logger.warning(f"Web scraping failed: {str(e)}")
            return []

    def _generate_ai_analysis_secure(self, query: str, web_data: List[Dict]) -> Dict:
        """Generate AI-powered financial analysis with security measures"""
        try:
            if not self.gemini_api_key:
                return self._generate_mock_analysis(query)

            # Prepare context from web data with length limits
            context_parts = []
            for item in web_data[:3]:  # Limit to 3 sources for context
                method = item.get('method', 'unknown')
                source_info = f"[Source: {item['source']}]" if method == 'web_scraping' else f"[Via: {method}]"

                # Sanitize content
                title = bleach.clean(item.get('title', ''), tags=[], strip=True)[:100]
                snippet = bleach.clean(item.get('snippet', ''), tags=[], strip=True)[:300]

                context_parts.append(f"{source_info} {title}\nContent: {snippet}")

            context = "\n\n".join(context_parts)

            # Create secure prompt with input validation
            prompt = f"""You are an expert financial analyst AI. Analyze the following query and provide comprehensive market insights.

Query: {query}

Additional Context from Recent Financial News:
{context}

Please provide a detailed analysis including:
1. Current market conditions and trends
2. Key factors influencing the market
3. Technical analysis insights
4. Risk assessment
5. Future outlook and recommendations

Format your response as a JSON object with the following structure:
{{
    "market_overview": "Brief overview of current market conditions",
    "key_factors": ["List of key influencing factors"],
    "technical_analysis": "Technical analysis insights",
    "risk_assessment": "Risk assessment and potential challenges",
    "outlook": "Future market outlook",
    "confidence_level": "High/Medium/Low confidence in the analysis"
}}

Important: Only respond with valid JSON. Do not include any other text or explanations."""

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.3,  # Lower temperature for more consistent responses
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048,
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }

            headers = {
                'Content-Type': 'application/json'
            }

            # Retry logic with exponential backoff
            for attempt in range(self.MAX_RETRIES):
                try:
                    response = requests.post(
                        f"{self.gemini_url}?key={self.gemini_api_key}",
                        json=payload,
                        headers=headers,
                        timeout=self.REQUEST_TIMEOUT
                    )

                    response.raise_for_status()
                    result = response.json()

                    # Extract the analysis from Gemini response
                    if 'candidates' in result and result['candidates']:
                        text_response = result['candidates'][0]['content']['parts'][0]['text']

                        # Try to parse as JSON with validation
                        try:
                            analysis = json.loads(text_response.strip())

                            # Validate required fields
                            required_fields = ['market_overview', 'key_factors', 'technical_analysis',
                                             'risk_assessment', 'outlook', 'confidence_level']

                            if all(field in analysis for field in required_fields):
                                # Sanitize the response
                                for key, value in analysis.items():
                                    if isinstance(value, str):
                                        analysis[key] = bleach.clean(value, tags=[], strip=True)[:1000]
                                    elif isinstance(value, list):
                                        analysis[key] = [bleach.clean(str(item), tags=[], strip=True)[:200]
                                                       for item in value[:5]]  # Limit list items

                                return analysis
                            else:
                                logger.warning("AI response missing required fields")
                                return self._generate_mock_analysis(query)

                        except json.JSONDecodeError:
                            logger.warning("AI response not valid JSON")
                            return self._generate_mock_analysis(query)
                    else:
                        logger.warning("No candidates in AI response")
                        return self._generate_mock_analysis(query)

                except requests.exceptions.Timeout:
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        logger.error("AI request timed out after retries")
                        return self._generate_mock_analysis(query)

                except requests.exceptions.RequestException as e:
                    logger.error(f"AI request failed: {str(e)}")
                    return self._generate_mock_analysis(query)

            return self._generate_mock_analysis(query)

        except Exception as e:
            logger.error(f"AI analysis generation failed: {str(e)}")
            return self._generate_mock_analysis(query)

    def _parse_text_analysis(self, text: str) -> Dict:
        """Parse text analysis into structured format"""
        # Simple parsing logic - in production, use more sophisticated NLP
        return {
            "market_overview": "Analysis generated from AI model",
            "key_factors": ["Market trends", "Economic indicators", "Technical signals"],
            "technical_analysis": text[:500] + "..." if len(text) > 500 else text,
            "risk_assessment": "Please consult with financial advisor",
            "outlook": "Market conditions are dynamic",
            "confidence_level": "Medium"
        }

    def _generate_mock_analysis(self, query: str) -> Dict:
        """Generate mock analysis when AI API is not available"""
        return {
            "market_overview": f"Analysis for query: {query}",
            "key_factors": [
                "Economic indicators",
                "Market sentiment",
                "Technical signals",
                "Global events"
            ],
            "technical_analysis": "Technical analysis requires current market data and AI processing capabilities.",
            "risk_assessment": "Market risks include volatility, economic uncertainty, and geopolitical factors.",
            "outlook": "Market outlook depends on various economic and technical factors.",
            "confidence_level": "Low (Demo Mode)"
        }

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []

        confidence = analysis.get('confidence_level', 'Low')

        if confidence == 'High':
            recommendations.extend([
                "Consider implementing risk management strategies",
                "Monitor key technical indicators regularly",
                "Stay informed about market news and economic data"
            ])
        elif confidence == 'Medium':
            recommendations.extend([
                "Diversify investment portfolio",
                "Consult with financial advisor",
                "Monitor market conditions closely"
            ])
        else:
            recommendations.extend([
                "This is educational information only",
                "Consult professional financial advisors",
                "Conduct thorough personal research"
            ])

        return recommendations

    def get_research_history(self) -> List[Dict]:
        """Get history of research queries (mock implementation)"""
        # In production, this would query a database
        return [
            {
                "query": "EURUSD trend analysis",
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
        ]