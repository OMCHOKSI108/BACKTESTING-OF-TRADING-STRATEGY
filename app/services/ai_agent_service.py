import os
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging
from bs4 import BeautifulSoup
import re
import asyncio

logger = logging.getLogger(__name__)

class AIAgentService:
    """AI Agent service for automated financial market research and reporting"""

    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.search_api_key = os.getenv('GOOGLE_SEARCH_API_KEY', '')  # Optional
        self.search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID', '')  # Optional
        self.use_crawl4ai = os.getenv('USE_CRAWL4AI', 'false').lower() == 'true'  # New option

    def research_financial_markets(self, query: str, max_results: int = 5) -> Dict:
        """
        Perform automated financial market research using AI and web search

        Args:
            query: Research query (e.g., "Analyze current EURUSD trends")
            max_results: Maximum number of research results to return

        Returns:
            Dict containing research results and analysis
        """
        try:
            # Step 1: Gather web data using preferred method
            if self.use_crawl4ai:
                web_data = self._gather_web_data_crawl4ai(query)
            elif self.search_api_key:
                web_data = self._gather_web_data_google(query)
            else:
                web_data = []

            # Step 2: Generate AI analysis
            analysis = self._generate_ai_analysis(query, web_data)

            # Step 3: Structure the response
            result = {
                "success": True,
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis,
                "web_sources": web_data,
                "recommendations": self._generate_recommendations(analysis),
                "disclaimer": "This analysis is for informational purposes only and should not be considered financial advice."
            }

            return result

        except Exception as e:
            logger.error(f"Error in financial research: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "timestamp": datetime.now().isoformat()
            }

    def _gather_web_data_google(self, query: str) -> List[Dict]:
        """Gather relevant financial data using Google Custom Search API"""
        try:
            # Use Google Custom Search API if available
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.search_api_key,
                'cx': self.search_engine_id,
                'q': f"{query} financial analysis market trends",
                'num': 5,
                'dateRestrict': 'd7'  # Last 7 days
            }

            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()

            results = response.json().get('items', [])

            web_data = []
            for item in results[:5]:  # Limit to 5 results
                web_data.append({
                    "title": item.get('title', ''),
                    "url": item.get('link', ''),
                    "snippet": item.get('snippet', ''),
                    "source": item.get('displayLink', ''),
                    "method": "google_search"
                })

            return web_data

        except Exception as e:
            logger.warning(f"Google search data gathering failed: {str(e)}")
            return []

    def _gather_web_data_crawl4ai(self, query: str) -> List[Dict]:
        """Gather relevant financial data using simple web scraping (requests + BeautifulSoup)"""
        try:
            # Define financial news sources to scrape
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            for source in financial_sources[:3]:  # Limit to 3 sources for speed
                try:
                    response = requests.get(source["url"], headers=headers, timeout=10)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Extract title
                    title = soup.title.string if soup.title else source["name"]

                    # Extract headlines and content
                    headlines = []

                    # Try different selectors for headlines
                    selectors = ['h1', 'h2', 'h3', '.headline', '.title', 'a[href*="news"]']

                    for selector in selectors:
                        elements = soup.select(selector)
                        for elem in elements[:5]:  # Limit headlines per source
                            text = elem.get_text().strip()
                            if len(text) > 20 and len(text) < 200:  # Filter for substantial content
                                # Clean up text
                                text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
                                headlines.append(text)

                    # Create content snippet
                    content_snippet = " | ".join(headlines[:3]) if headlines else f"Latest financial news from {source['name']}"

                    web_data.append({
                        "title": title,
                        "url": source["url"],
                        "snippet": content_snippet,
                        "source": source["name"],
                        "method": "web_scraping",
                        "scrape_timestamp": datetime.now().isoformat()
                    })

                except Exception as e:
                    logger.warning(f"Failed to scrape {source['url']}: {str(e)}")
                    continue

            return web_data[:5]  # Return top 5 results

        except Exception as e:
            logger.warning(f"Web scraping data gathering failed: {str(e)}")
            return []

    def _generate_ai_analysis(self, query: str, web_data: List[Dict]) -> Dict:
        """Generate AI-powered financial analysis"""
        try:
            if not self.gemini_api_key:
                return self._generate_mock_analysis(query)

            # Prepare context from web data
            context_parts = []
            for item in web_data:
                method = item.get('method', 'unknown')
                source_info = f"[Source: {item['source']}]" if method == 'crawl4ai' else f"[Via: {method}]"
                context_parts.append(f"{source_info} {item['title']}\nContent: {item['snippet']}")

            context = "\n\n".join(context_parts)

            prompt = f"""
You are an expert financial analyst AI. Analyze the following query and provide comprehensive market insights.

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
"""

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048,
                }
            }

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f"{self.gemini_url}?key={self.gemini_api_key}",
                json=payload,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Extract the analysis from Gemini response
            if 'candidates' in result and result['candidates']:
                text_response = result['candidates'][0]['content']['parts'][0]['text']

                # Try to parse as JSON
                try:
                    analysis = json.loads(text_response)
                except json.JSONDecodeError:
                    # If not valid JSON, create structured response from text
                    analysis = self._parse_text_analysis(text_response)

                return analysis
            else:
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