"""
News Sentiment Analysis Module
==============================
Scrapes news from Google and analyzes sentiment for stocks and market.

Features:
- Google News scraping
- Sentiment analysis (positive/negative/neutral)
- Market news aggregation
- Stock-specific news
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import urllib.parse


class Sentiment(Enum):
    """News sentiment classification."""
    VERY_POSITIVE = "Very Positive"
    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"
    VERY_NEGATIVE = "Very Negative"


@dataclass
class NewsItem:
    """A single news item."""
    title: str
    source: str
    url: str
    published: str
    snippet: str
    sentiment: Sentiment
    sentiment_score: float  # -1 to 1
    date: Optional[datetime] = None
    keywords: List[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class NewsSentimentAnalyzer:
    """
    Scrapes and analyzes news sentiment for Indian stocks.
    """

    # Positive keywords for sentiment
    POSITIVE_KEYWORDS = [
        'surge', 'jump', 'rally', 'gain', 'rise', 'up', 'high', 'record',
        'profit', 'growth', 'bullish', 'buy', 'upgrade', 'beat', 'strong',
        'positive', 'boost', 'soar', 'advance', 'improve', 'outperform',
        'breakout', 'momentum', 'optimistic', 'recovery', 'expansion',
        'dividend', 'bonus', 'split', 'acquisition', 'partnership',
        'deal', 'contract', 'order', 'revenue', 'earnings', 'success'
    ]

    # Negative keywords for sentiment
    NEGATIVE_KEYWORDS = [
        'fall', 'drop', 'crash', 'decline', 'down', 'low', 'loss',
        'bearish', 'sell', 'downgrade', 'miss', 'weak', 'negative',
        'plunge', 'tumble', 'slump', 'concern', 'warning', 'risk',
        'debt', 'default', 'fraud', 'scandal', 'investigation',
        'layoff', 'cut', 'reduce', 'disappointing', 'struggle',
        'penalty', 'fine', 'lawsuit', 'regulatory', 'probe'
    ]

    # User agent for requests
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def get_google_news(self, query: str, num_results: int = 10) -> List[NewsItem]:
        """
        Fetch news from Google News search.

        Args:
            query: Search query (e.g., "Reliance Industries stock")
            num_results: Number of results to fetch

        Returns:
            List of NewsItem objects
        """
        news_items = []

        try:
            # Encode query
            encoded_query = urllib.parse.quote(query)

            # Google News search URL
            url = f"https://www.google.com/search?q={encoded_query}&tbm=nws&num={num_results}"

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find news articles
            articles = soup.find_all('div', class_='SoaBEf') or soup.find_all('div', {'data-hveid': True})

            for article in articles[:num_results]:
                try:
                    # Extract title
                    title_elem = article.find('div', class_='n0jPhd') or article.find('h3')
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    # Extract source
                    source_elem = article.find('div', class_='MgUUmf') or article.find('span', class_='CEMjEf')
                    source = source_elem.get_text(strip=True) if source_elem else "Unknown"

                    # Extract snippet
                    snippet_elem = article.find('div', class_='GI74Re')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    # Extract URL
                    link_elem = article.find('a', href=True)
                    url = link_elem['href'] if link_elem else ""
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]

                    # Extract time
                    time_elem = article.find('div', class_='OSrXXb') or article.find('span', class_='WG9SHc')
                    published = time_elem.get_text(strip=True) if time_elem else "Recently"

                    if title:
                        # Analyze sentiment
                        full_text = f"{title} {snippet}"
                        sentiment, score = self._analyze_sentiment(full_text)

                        # Extract keywords
                        keywords = self._extract_keywords(full_text)

                        # Parse date
                        parsed_date = self._parse_date(published)

                        news_items.append(NewsItem(
                            title=title,
                            source=source,
                            url=url,
                            published=published,
                            snippet=snippet[:200] + "..." if len(snippet) > 200 else snippet,
                            sentiment=sentiment,
                            sentiment_score=score,
                            date=parsed_date,
                            keywords=keywords
                        ))

                except Exception as e:
                    continue

        except Exception as e:
            # Return fallback data if scraping fails
            pass

        return news_items

    def get_stock_news(self, symbol: str, company_name: str = "", num_results: int = 10) -> List[NewsItem]:
        """
        Get news for a specific stock.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            company_name: Full company name (optional)
            num_results: Number of results

        Returns:
            List of NewsItem objects
        """
        # Build search query
        if company_name:
            query = f"{company_name} stock news India"
        else:
            query = f"{symbol} stock news NSE India"

        return self.get_google_news(query, num_results)

    def get_market_news(self, query: str = None, num_results: int = 15) -> List[NewsItem]:
        """
        Get general Indian stock market news.

        Args:
            query: Custom search query (optional)
            num_results: Number of results to fetch

        Returns:
            List of NewsItem objects
        """
        if query:
            return self.get_google_news(query, num_results)

        queries = [
            "Indian stock market news today",
            "Nifty 50 news today",
            "NSE BSE market news"
        ]

        all_news = []
        for q in queries:
            news = self.get_google_news(q, num_results // len(queries))
            all_news.extend(news)

        # Remove duplicates by title
        seen_titles = set()
        unique_news = []
        for item in all_news:
            if item.title not in seen_titles:
                seen_titles.add(item.title)
                unique_news.append(item)

        return unique_news[:num_results]

    def get_sector_news(self, sector: str, num_results: int = 10) -> List[NewsItem]:
        """
        Get news for a specific sector.

        Args:
            sector: Sector name (e.g., "IT", "Banking", "Pharma")

        Returns:
            List of NewsItem objects
        """
        query = f"India {sector} sector stocks news"
        return self.get_google_news(query, num_results)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        text_lower = text.lower()
        keywords = []

        # Check for positive keywords
        for word in self.POSITIVE_KEYWORDS:
            if word in text_lower:
                keywords.append(word)

        # Check for negative keywords
        for word in self.NEGATIVE_KEYWORDS:
            if word in text_lower:
                keywords.append(word)

        return keywords[:10]  # Limit to 10 keywords

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        try:
            date_str_lower = date_str.lower()

            if 'hour' in date_str_lower or 'minute' in date_str_lower:
                return datetime.now()
            elif 'day' in date_str_lower:
                days = 1
                for word in date_str_lower.split():
                    if word.isdigit():
                        days = int(word)
                        break
                return datetime.now() - timedelta(days=days)
            elif 'week' in date_str_lower:
                weeks = 1
                for word in date_str_lower.split():
                    if word.isdigit():
                        weeks = int(word)
                        break
                return datetime.now() - timedelta(weeks=weeks)
            elif 'month' in date_str_lower:
                return datetime.now() - timedelta(days=30)
            else:
                return datetime.now()
        except:
            return datetime.now()

    def _analyze_sentiment(self, text: str) -> tuple:
        """
        Analyze sentiment of text using keyword matching.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (Sentiment, score)
        """
        text_lower = text.lower()

        positive_count = sum(1 for word in self.POSITIVE_KEYWORDS if word in text_lower)
        negative_count = sum(1 for word in self.NEGATIVE_KEYWORDS if word in text_lower)

        total = positive_count + negative_count
        if total == 0:
            return Sentiment.NEUTRAL, 0.0

        # Calculate score (-1 to 1)
        score = (positive_count - negative_count) / total

        # Classify sentiment
        if score > 0.5:
            return Sentiment.VERY_POSITIVE, score
        elif score > 0.15:
            return Sentiment.POSITIVE, score
        elif score < -0.5:
            return Sentiment.VERY_NEGATIVE, score
        elif score < -0.15:
            return Sentiment.NEGATIVE, score
        else:
            return Sentiment.NEUTRAL, score

    def get_overall_sentiment(self, news_items: List[NewsItem]) -> Sentiment:
        """
        Get overall sentiment from news items (simplified return).

        Args:
            news_items: List of NewsItem objects

        Returns:
            Overall Sentiment enum value
        """
        summary = self.get_sentiment_summary(news_items)
        return summary['overall_sentiment']

    def get_sentiment_summary(self, news_items: List[NewsItem]) -> Dict[str, Any]:
        """
        Get overall sentiment summary from news items.

        Args:
            news_items: List of NewsItem objects

        Returns:
            Dictionary with sentiment summary
        """
        if not news_items:
            return {
                'overall_sentiment': Sentiment.NEUTRAL,
                'avg_score': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'total': 0
            }

        scores = [item.sentiment_score for item in news_items]
        avg_score = sum(scores) / len(scores)

        positive_count = sum(1 for item in news_items if item.sentiment in [Sentiment.POSITIVE, Sentiment.VERY_POSITIVE])
        negative_count = sum(1 for item in news_items if item.sentiment in [Sentiment.NEGATIVE, Sentiment.VERY_NEGATIVE])
        neutral_count = len(news_items) - positive_count - negative_count

        # Determine overall sentiment
        if avg_score > 0.3:
            overall = Sentiment.VERY_POSITIVE
        elif avg_score > 0.1:
            overall = Sentiment.POSITIVE
        elif avg_score < -0.3:
            overall = Sentiment.VERY_NEGATIVE
        elif avg_score < -0.1:
            overall = Sentiment.NEGATIVE
        else:
            overall = Sentiment.NEUTRAL

        return {
            'overall_sentiment': overall,
            'avg_score': avg_score,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'total': len(news_items)
        }


def get_sentiment_color(sentiment: Sentiment) -> str:
    """Get color for sentiment display."""
    colors = {
        Sentiment.VERY_POSITIVE: "#00c853",
        Sentiment.POSITIVE: "#4caf50",
        Sentiment.NEUTRAL: "#9e9e9e",
        Sentiment.NEGATIVE: "#f44336",
        Sentiment.VERY_NEGATIVE: "#b71c1c",
    }
    return colors.get(sentiment, "#9e9e9e")


def get_sentiment_emoji(sentiment: Sentiment) -> str:
    """Get emoji for sentiment display."""
    emojis = {
        Sentiment.VERY_POSITIVE: "🚀",
        Sentiment.POSITIVE: "📈",
        Sentiment.NEUTRAL: "➖",
        Sentiment.NEGATIVE: "📉",
        Sentiment.VERY_NEGATIVE: "⚠️",
    }
    return emojis.get(sentiment, "➖")


# Extended stock universe - ALL NSE stocks (major ones)
FULL_STOCK_UNIVERSE = [
    # Nifty 50
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "SBIN", "BHARTIARTL",
    "ITC", "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "TITAN", "SUNPHARMA",
    "BAJFINANCE", "WIPRO", "HCLTECH", "TATAMOTORS", "TATASTEEL", "ADANIENT", "POWERGRID",
    "NTPC", "ONGC", "ULTRACEMCO", "JSWSTEEL", "BAJAJFINSV", "TECHM", "INDUSINDBK",
    "NESTLEIND", "GRASIM", "HDFCLIFE", "DRREDDY", "COALINDIA", "SBILIFE", "CIPLA",
    "BRITANNIA", "EICHERMOT", "APOLLOHOSP", "DIVISLAB", "BPCL", "TATACONSUM",
    "HEROMOTOCO", "M&M", "ADANIPORTS", "HINDALCO", "BAJAJ-AUTO", "SHRIRAMFIN", "LTIM",

    # Nifty Next 50
    "ABB", "ADANIGREEN", "AMBUJACEM", "ATGL", "AUROPHARMA", "BANDHANBNK", "BANKBARODA",
    "BERGEPAINT", "BIOCON", "BOSCHLTD", "CANBK", "CHOLAFIN", "COLPAL", "CONCOR", "DLF",
    "DABUR", "GAIL", "GODREJCP", "HAVELLS", "ICICIPRULI", "IGL", "INDUSTOWER", "IOC",
    "IRCTC", "JINDALSTEL", "JUBLFOOD", "LUPIN", "MARICO", "MCDOWELL-N", "MOTHERSON",
    "MUTHOOTFIN", "NAUKRI", "NHPC", "NMDC", "OBEROIRLTY", "OFSS", "PAGEIND", "PAYTM",
    "PGHH", "PIDILITIND", "PNB", "POLICYBZR", "POLYCAB", "SAIL", "SBICARD", "SRF",
    "SIEMENS", "TATAPOWER", "TORNTPHARM", "TRENT", "UPL", "VBL", "VEDL", "YESBANK", "ZOMATO",

    # Nifty Midcap 50
    "ABCAPITAL", "ACC", "ASHOKLEY", "ASTRAL", "ATUL", "AUBANK", "BALKRISIND", "BEL",
    "BHEL", "CANFINHOME", "CGPOWER", "COROMANDEL", "CUMMINSIND", "DALBHARAT", "DEEPAKNTR",
    "DIXON", "ESCORTS", "EXIDEIND", "FEDERALBNK", "FSL", "GLENMARK", "GMR", "GNFC",
    "GUJGASLTD", "HAL", "HONAUT", "IDFCFIRSTB", "IIFL", "INDHOTEL", "IRFC", "ISEC",
    "JKCEMENT", "JSL", "JUBLINGREA", "KAJARIACER", "KPITTECH", "L&TFH", "LALPATHLAB",
    "LAURUSLABS", "LICHSGFIN", "LTTS", "MANAPPURAM", "MFSL", "MINDTREE", "MPHASIS",
    "MRF", "NAM-INDIA", "NATIONALUM", "NAVINFLUOR", "PERSISTENT", "PETRONET", "PFC",
    "PIIND", "PVR", "RAMCOCEM", "RECLTD", "SJVN", "SOLARINDS", "SUNTV", "SUPREMEIND",
    "SYNGENE", "TATACHEM", "TATACOMM", "TATAELXSI", "THERMAX", "TIINDIA", "TORNTPOWER",
    "TVSMOTOR", "UBL", "UNIONBANK", "VOLTAS", "WHIRLPOOL", "ZEEL",

    # Additional popular/liquid stocks
    "AARTIIND", "ADANIWILMAR", "AFFLE", "AJANTPHARM", "ALKEM", "AMARAJABAT", "APLAPOLLO",
    "ASAHIINDIA", "ASHOKA", "AVANTIFEED", "AXISBANK", "BAJAJHLDNG", "BALRAMCHIN", "BATAINDIA",
    "BAYERCROP", "BEML", "BHARATFORG", "BIRLACORPN", "BLUESTARCO", "BSOFT", "CARBORUNIV",
    "CASTROLIND", "CDSL", "CENTURYTEX", "CESC", "CHAMBLFERT", "COCHINSHIP", "COFORGE",
    "CROMPTON", "CUB", "CYIENT", "DCMSHRIRAM", "DHANUKA", "ECLERX", "EDELWEISS",
    "EMAMILTD", "ENGINERSIN", "EQUITAS", "FACT", "FINCABLES", "FINPIPE", "FLUOROCHEM",
    "FORTIS", "GARFIBRES", "GLAXO", "GOCOLORS", "GODFRYPHLP", "GRAPHITE", "GRINDWELL",
    "GSFC", "GSPL", "GUJALKALI", "HAPPSTMNDS", "HCG", "HDFC", "HFCL", "HGS", "HINDCOPPER",
    "HINDPETRO", "HINDZINC", "HUDCO", "ICICIGI", "IDBI", "IDEA", "IGPL", "IIB",
    "INDIAMART", "INTELLECT", "IPCALAB", "IRB", "ISEC", "ITDC", "ITI", "J&KBANK",
    "JBF", "JBCHEPHARM", "JKLAKSHMI", "JKPAPER", "JMFINANCIL", "JSLHISAR", "JSWENERGY",
    "JTEKTINDIA", "JUSTDIAL", "JYOTHYLAB", "KALPATPOWR", "KALYANKJIL", "KANSAINER",
    "KEI", "KEC", "KIMS", "KNRCON", "KPRMILL", "KSB", "LATENTVIEW", "LEMONTREE",
    "LINDEINDIA", "LUXIND", "MAHINDCIE", "MAHLOG", "MAHSEAMLES", "MAITHANALL", "MAPMYINDIA",
    "MARKSANS", "MASTEK", "MAXHEALTH", "MAZAGON", "MCX", "MEDANTA", "METROPOLIS",
    "MIDHANI", "MMTC", "MOIL", "MOTHERSON", "MSTCLTD", "NESCO", "NETWORK18", "NFL",
    "NH", "NLCINDIA", "NOCIL", "NSLNISP", "NTPC", "NUCLEUS", "OLECTRA", "ORIENTELEC",
    "PARAGMILK", "PATELENG", "PCBL", "PFIZER", "PHOENIXLTD", "POWERINDIA", "PRAJIND",
    "PRSMJOHNSN", "QUESS", "RADICO", "RAIN", "RAJESHEXPO", "RALLIS", "RATNAMANI",
    "RAYMOND", "RBLBANK", "RCF", "REDINGTON", "RELIGARE", "RENUKA", "RITES", "ROUTE",
    "RVNL", "SAFARI", "SANDUMA", "SANOFI", "SARDAEN", "SCHAEFFLER", "SCHNEIDER",
    "SEQUENT", "SHILPAMED", "SHREECEM", "SHREYAS", "SHYAMMETL", "SOBHA", "SONACOMS",
    "SOUTHBANK", "SPARC", "STAR", "STARCEMENT", "SUBROS", "SUMICHEM", "SUNDARMFIN",
    "SUNFLAG", "SUPRAJIT", "SURYAROSNI", "SUZLON", "SWANENERGY", "SYMPHONY", "TANLA",
    "TATAINVEST", "TATAMETALI", "TCI", "TCNSBRANDS", "TEAMLEASE", "TCIEXP", "TECHNO",
    "TEXRAIL", "TIMKEN", "TITAN", "TMB", "TORNTPOWER", "TRIDENT", "TRITURBINE",
    "TV18BRDCST", "TVTODAY", "UCOBANK", "UFLEX", "UJJIVAN", "UJJIVANSFB", "UTIAMC",
    "VAIBHAVGBL", "VARROC", "VGUARD", "VINATIORGA", "VIPIND", "VMART", "VOLTAMP",
    "VSTIND", "WELCORP", "WELSPUNIND", "WESTLIFE", "WOCKPHARMA", "XPROINDIA", "YATRA",
    "ZENSARTECH", "ZODIACJRD",
]
