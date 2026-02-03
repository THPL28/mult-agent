"""
🤖 RPA Web Scraper Agent - MultiAgent Platform
================================================
Advanced web scraping and automation agent with multi-instance support.
Handles real-world scenarios: e-commerce, news, social media, financial data.

Features:
- Multi-instance parallel execution
- Playwright & Selenium support
- Auto-healing with retry logic
- Smart content extraction
- Anti-bot detection handling
"""

from typing import List, Dict, Any, Optional, Callable
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import re
from urllib.parse import urljoin, urlparse
import hashlib

# Web Automation
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Data Processing
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

# Utils
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
import os

# Dashboard Integration
try:
    from app.dashboard import dashboard
except ImportError:
    dashboard = None

# Configure logger
logger.add("logs/rpa_web_scraper_{time}.log", rotation="500 MB", retention="10 days", level="INFO")


class ScraperEngine(Enum):
    """Supported scraping engines"""
    PLAYWRIGHT = "playwright"
    SELENIUM = "selenium"
    REQUESTS = "requests"


class ScenarioType(Enum):
    """Real-world automation scenarios"""
    ECOMMERCE = "ecommerce"
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    FINANCIAL = "financial"
    JOB_LISTINGS = "job_listings"
    REAL_ESTATE = "real_estate"
    CUSTOM = "custom"


@dataclass
class ScrapingTask:
    """Task definition for web scraping"""
    url: str
    scenario: ScenarioType
    engine: ScraperEngine = ScraperEngine.PLAYWRIGHT
    selectors: Dict[str, str] = field(default_factory=dict)
    wait_time: int = 5000  # milliseconds
    max_retries: int = 3
    use_proxy: bool = False
    extract_images: bool = False
    extract_links: bool = False
    pagination: bool = False
    scroll_to_bottom: bool = False
    javascript_required: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScrapingResult:
    """Result from scraping operation"""
    task_id: str
    url: str
    scenario: ScenarioType
    data: Dict[str, Any]
    images: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "success"
    error: Optional[str] = None
    execution_time: float = 0.0


class WebScraperAgent:
    """
    🌐 Advanced Web Scraping Agent
    
    Multi-instance RPA agent for automated web data extraction.
    Supports multiple engines and real-world scenarios.
    """
    
    def __init__(self, max_instances: int = 5):
        """
        Initialize the Web Scraper Agent
        
        Args:
            max_instances: Maximum number of parallel scraper instances
        """
        self.max_instances = max_instances
        self.active_instances = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        
        # Session with retry logic
        self.session = self._create_session()
        
        # Task queue
        self.task_queue = asyncio.Queue()
        self.results = []
        
        logger.info(f"🚀 Web Scraper Agent initialized with {max_instances} max instances")
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    async def execute_multi_instance(self, tasks: List[ScrapingTask]) -> List[ScrapingResult]:
        """
        Execute multiple scraping tasks in parallel
        
        Args:
            tasks: List of scraping tasks
            
        Returns:
            List of scraping results
        """
        logger.info(f"📊 Starting multi-instance execution for {len(tasks)} tasks")
        start_time = datetime.now()
        
        # Add tasks to queue
        for task in tasks:
            await self.task_queue.put(task)
        
        # Create worker instances
        workers = [
            asyncio.create_task(self._worker(f"Worker-{i}"))
            for i in range(min(self.max_instances, len(tasks)))
        ]
        
        # Wait for all tasks to complete
        await self.task_queue.join()
        
        # Cancel workers
        for worker in workers:
            worker.cancel()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Multi-instance execution completed in {execution_time:.2f}s")
        logger.info(f"📈 Success: {self.completed_tasks}, Failed: {self.failed_tasks}")
        
        return self.results
    
    async def _worker(self, name: str):
        """
        Worker assíncrono que processa tarefas da fila.
        
        Consome tarefas de `self.task_queue`, gerencia contagem de instâncias ativas
        e reporta o progresso ao logger e ao dashboard em tempo real.
        
        Args:
            name (str): Identificador único do worker (ex: Worker-1).
        """
        logger.info(f"🔧 {name} started")
        
        while True:
            try:
                task = await self.task_queue.get()
                self.active_instances += 1
                
                # Notificar dashboard sobre nova tarefa
                if dashboard:
                    await dashboard.add_task_event({
                        "type": "task_started",
                        "url": task.url,
                        "worker": name,
                        "status": "pending"
                    })
                    await dashboard.update_worker_count(self.active_instances)
                
                logger.info(f"⚙️ {name} processing: {task.url}")
                
                try:
                    result = await self._execute_single_task(task)
                    self.results.append(result)
                    self.completed_tasks += 1
                    logger.success(f"✅ {name} completed: {task.url}")
                    
                    # Notificar sucesso no dashboard
                    if dashboard:
                        await dashboard.add_task_event({
                            "type": "task_completed",
                            "url": task.url,
                            "worker": name,
                            "status": "success",
                            "execution_time": result.execution_time
                        })
                except Exception as e:
                    logger.error(f"❌ {name} failed: {task.url} - {str(e)}")
                    self.failed_tasks += 1
                    self.results.append(ScrapingResult(
                        task_id=self._generate_task_id(task.url),
                        url=task.url,
                        scenario=task.scenario,
                        data={},
                        status="failed",
                        error=str(e)
                    ))
                    
                    # Notificar falha no dashboard
                    if dashboard:
                        await dashboard.add_task_event({
                            "type": "task_failed",
                            "url": task.url,
                            "worker": name,
                            "status": "failed",
                            "error": str(e)
                        })
                finally:
                    self.active_instances -= 1
                    self.task_queue.task_done()
                    if dashboard:
                        await dashboard.update_worker_count(self.active_instances)
                    
            except asyncio.CancelledError:
                break
    
    async def _execute_single_task(self, task: ScrapingTask) -> ScrapingResult:
        """Execute a single scraping task"""
        start_time = datetime.now()
        task_id = self._generate_task_id(task.url)
        
        # Select engine based on task requirements
        if task.engine == ScraperEngine.PLAYWRIGHT:
            data = await self._scrape_with_playwright(task)
        elif task.engine == ScraperEngine.SELENIUM:
            data = await self._scrape_with_selenium(task)
        else:
            data = await self._scrape_with_requests(task)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return ScrapingResult(
            task_id=task_id,
            url=task.url,
            scenario=task.scenario,
            data=data,
            execution_time=execution_time
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _scrape_with_playwright(self, task: ScrapingTask) -> Dict[str, Any]:
        """
        Scrape with Playwright (Best for modern JS-heavy sites)
        """
        logger.info(f"🎭 Using Playwright for: {task.url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to URL
                await page.goto(task.url, wait_until="networkidle", timeout=30000)
                
                # Scroll if required
                if task.scroll_to_bottom:
                    await self._scroll_page(page)
                
                # Wait for specific elements
                if task.selectors:
                    for selector in task.selectors.values():
                        try:
                            await page.wait_for_selector(selector, timeout=task.wait_time)
                        except PlaywrightTimeout:
                            logger.warning(f"⚠️ Selector timeout: {selector}")
                
                # Extract data based on scenario
                data = await self._extract_data_by_scenario(page, task)
                
                return data
                
            finally:
                await browser.close()
    
    async def _scrape_with_selenium(self, task: ScrapingTask) -> Dict[str, Any]:
        """
        Scrape with Selenium (Compatibility mode)
        """
        logger.info(f"🔧 Using Selenium for: {task.url}")
        
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        
        try:
            driver.get(task.url)
            
            # Wait for page load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Scroll if required
            if task.scroll_to_bottom:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(2)
            
            # Get page source
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract data
            data = self._extract_data_from_soup(soup, task)
            
            return data
            
        finally:
            driver.quit()
    
    async def _scrape_with_requests(self, task: ScrapingTask) -> Dict[str, Any]:
        """
        Scrape with Requests (Fast for static content)
        """
        logger.info(f"🌐 Using Requests for: {task.url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            **task.custom_headers
        }
        
        response = self.session.get(task.url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        data = self._extract_data_from_soup(soup, task)
        
        return data
    
    async def _extract_data_by_scenario(self, page: Page, task: ScrapingTask) -> Dict[str, Any]:
        """Extract data based on scenario type"""
        
        if task.scenario == ScenarioType.ECOMMERCE:
            return await self._extract_ecommerce_data(page, task)
        elif task.scenario == ScenarioType.NEWS:
            return await self._extract_news_data(page, task)
        elif task.scenario == ScenarioType.FINANCIAL:
            return await self._extract_financial_data(page, task)
        elif task.scenario == ScenarioType.JOB_LISTINGS:
            return await self._extract_job_data(page, task)
        else:
            return await self._extract_custom_data(page, task)
    
    async def _extract_ecommerce_data(self, page: Page, task: ScrapingTask) -> Dict[str, Any]:
        """Extract e-commerce product data"""
        logger.info("🛒 Extracting e-commerce data")
        
        data = {
            "products": [],
            "categories": [],
            "total_items": 0
        }
        
        # Common e-commerce selectors
        selectors = task.selectors or {
            "product": ".product, .product-item, [data-product-id]",
            "title": "h2, h3, .product-title, .product-name",
            "price": ".price, .product-price, [class*='price']",
            "image": "img"
        }
        
        try:
            # Wait for products to load
            await page.wait_for_selector(selectors["product"], timeout=10000)
            
            # Extract product info
            products = await page.query_selector_all(selectors["product"])
            
            for product in products[:50]:  # Limit to 50 products
                try:
                    title_elem = await product.query_selector(selectors["title"])
                    price_elem = await product.query_selector(selectors["price"])
                    img_elem = await product.query_selector(selectors["image"])
                    
                    product_data = {
                        "title": await title_elem.inner_text() if title_elem else "N/A",
                        "price": await price_elem.inner_text() if price_elem else "N/A",
                        "image": await img_elem.get_attribute("src") if img_elem else "N/A"
                    }
                    
                    data["products"].append(product_data)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to extract product: {e}")
                    continue
            
            data["total_items"] = len(data["products"])
            
        except Exception as e:
            logger.error(f"❌ E-commerce extraction failed: {e}")
            raise
        
        return data
    
    async def _extract_news_data(self, page: Page, task: ScrapingTask) -> Dict[str, Any]:
        """Extract news articles"""
        logger.info("📰 Extracting news data")
        
        data = {
            "articles": [],
            "total_articles": 0
        }
        
        selectors = task.selectors or {
            "article": "article, .article, .post, [class*='article']",
            "headline": "h1, h2, .headline, .title",
            "summary": "p, .summary, .excerpt",
            "author": ".author, [class*='author']",
            "date": "time, .date, [datetime]"
        }
        
        try:
            articles = await page.query_selector_all(selectors["article"])
            
            for article in articles[:30]:  # Limit to 30 articles
                try:
                    headline_elem = await article.query_selector(selectors["headline"])
                    summary_elem = await article.query_selector(selectors["summary"])
                    author_elem = await article.query_selector(selectors["author"])
                    date_elem = await article.query_selector(selectors["date"])
                    
                    article_data = {
                        "headline": await headline_elem.inner_text() if headline_elem else "N/A",
                        "summary": await summary_elem.inner_text() if summary_elem else "N/A",
                        "author": await author_elem.inner_text() if author_elem else "N/A",
                        "date": await date_elem.get_attribute("datetime") if date_elem else "N/A"
                    }
                    
                    data["articles"].append(article_data)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to extract article: {e}")
                    continue
            
            data["total_articles"] = len(data["articles"])
            
        except Exception as e:
            logger.error(f"❌ News extraction failed: {e}")
            raise
        
        return data
    
    async def _extract_financial_data(self, page: Page, task: ScrapingTask) -> Dict[str, Any]:
        """Extract financial/stock data"""
        logger.info("💰 Extracting financial data")
        
        data = {
            "stocks": [],
            "market_summary": {}
        }
        
        selectors = task.selectors or {
            "stock": "[data-symbol], .stock-row, tr",
            "symbol": ".symbol, [data-symbol]",
            "price": ".price, [data-field='regularMarketPrice']",
            "change": ".change, [data-field='regularMarketChange']"
        }
        
        try:
            stocks = await page.query_selector_all(selectors["stock"])
            
            for stock in stocks[:100]:  # Limit to 100 stocks
                try:
                    symbol_elem = await stock.query_selector(selectors["symbol"])
                    price_elem = await stock.query_selector(selectors["price"])
                    change_elem = await stock.query_selector(selectors["change"])
                    
                    stock_data = {
                        "symbol": await symbol_elem.inner_text() if symbol_elem else "N/A",
                        "price": await price_elem.inner_text() if price_elem else "N/A",
                        "change": await change_elem.inner_text() if change_elem else "N/A"
                    }
                    
                    data["stocks"].append(stock_data)
                except Exception as e:
                    continue
            
        except Exception as e:
            logger.error(f"❌ Financial extraction failed: {e}")
            raise
        
        return data
    
    async def _extract_job_data(self, page: Page, task: ScrapingTask) -> Dict[str, Any]:
        """Extract job listings"""
        logger.info("💼 Extracting job listings")
        
        data = {
            "jobs": [],
            "total_jobs": 0
        }
        
        selectors = task.selectors or {
            "job": ".job, .job-card, [data-job-id]",
            "title": "h2, h3, .job-title",
            "company": ".company, .company-name",
            "location": ".location, .job-location",
            "salary": ".salary, [class*='salary']"
        }
        
        try:
            jobs = await page.query_selector_all(selectors["job"])
            
            for job in jobs[:50]:
                try:
                    title_elem = await job.query_selector(selectors["title"])
                    company_elem = await job.query_selector(selectors["company"])
                    location_elem = await job.query_selector(selectors["location"])
                    salary_elem = await job.query_selector(selectors["salary"])
                    
                    job_data = {
                        "title": await title_elem.inner_text() if title_elem else "N/A",
                        "company": await company_elem.inner_text() if company_elem else "N/A",
                        "location": await location_elem.inner_text() if location_elem else "N/A",
                        "salary": await salary_elem.inner_text() if salary_elem else "N/A"
                    }
                    
                    data["jobs"].append(job_data)
                except Exception as e:
                    continue
            
            data["total_jobs"] = len(data["jobs"])
            
        except Exception as e:
            logger.error(f"❌ Job extraction failed: {e}")
            raise
        
        return data
    
    async def _extract_custom_data(self, page: Page, task: ScrapingTask) -> Dict[str, Any]:
        """Extract custom data using provided selectors"""
        logger.info("🔧 Extracting custom data")
        
        data = {}
        
        if not task.selectors:
            # Get all text content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            data = {
                "title": soup.title.string if soup.title else "N/A",
                "text_content": soup.get_text()[:5000],  # First 5000 chars
                "links": [a.get('href') for a in soup.find_all('a', href=True)][:50]
            }
        else:
            # Use custom selectors
            for key, selector in task.selectors.items():
                try:
                    elements = await page.query_selector_all(selector)
                    values = []
                    for elem in elements[:20]:  # Limit to 20 per selector
                        text = await elem.inner_text()
                        values.append(text)
                    data[key] = values
                except Exception as e:
                    logger.warning(f"⚠️ Failed to extract {key}: {e}")
                    data[key] = []
        
        return data
    
    def _extract_data_from_soup(self, soup: BeautifulSoup, task: ScrapingTask) -> Dict[str, Any]:
        """Extract data from BeautifulSoup object"""
        data = {
            "title": soup.title.string if soup.title else "N/A",
            "text_content": soup.get_text()[:5000],
            "meta_description": ""
        }
        
        # Extract meta description
        meta = soup.find('meta', attrs={'name': 'description'})
        if meta:
            data["meta_description"] = meta.get('content', '')
        
        # Extract custom selectors
        if task.selectors:
            for key, selector in task.selectors.items():
                elements = soup.select(selector)
                data[key] = [elem.get_text(strip=True) for elem in elements[:20]]
        
        # Extract links if requested
        if task.extract_links:
            links = soup.find_all('a', href=True)
            data["links"] = [urljoin(task.url, link['href']) for link in links[:100]]
        
        # Extract images if requested
        if task.extract_images:
            images = soup.find_all('img', src=True)
            data["images"] = [urljoin(task.url, img['src']) for img in images[:50]]
        
        return data
    
    async def _scroll_page(self, page: Page):
        """Scroll page to bottom to load dynamic content"""
        logger.info("📜 Scrolling page to load content")
        
        previous_height = await page.evaluate("document.body.scrollHeight")
        
        for _ in range(5):  # Max 5 scrolls
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == previous_height:
                break
            previous_height = new_height
    
    def _generate_task_id(self, url: str) -> str:
        """Generate unique task ID"""
        return hashlib.md5(f"{url}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    def export_results_to_json(self, filename: str = "scraping_results.json"):
        """Export results to JSON file"""
        output = []
        for result in self.results:
            output.append({
                "task_id": result.task_id,
                "url": result.url,
                "scenario": result.scenario.value,
                "data": result.data,
                "status": result.status,
                "error": result.error,
                "execution_time": result.execution_time,
                "timestamp": result.timestamp.isoformat()
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.success(f"📁 Results exported to {filename}")
    
    def export_results_to_csv(self, filename: str = "scraping_results.csv"):
        """Export results to CSV file"""
        flattened_data = []
        
        for result in self.results:
            base_data = {
                "task_id": result.task_id,
                "url": result.url,
                "scenario": result.scenario.value,
                "status": result.status,
                "error": result.error,
                "execution_time": result.execution_time,
                "timestamp": result.timestamp.isoformat()
            }
            
            # Flatten nested data
            if isinstance(result.data, dict):
                for key, value in result.data.items():
                    if isinstance(value, (list, dict)):
                        base_data[key] = str(value)
                    else:
                        base_data[key] = value
            
            flattened_data.append(base_data)
        
        df = pd.DataFrame(flattened_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        
        logger.success(f"📊 Results exported to {filename}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Agent health check"""
        return {
            "agent": "WebScraperAgent",
            "status": "healthy",
            "active_instances": self.active_instances,
            "max_instances": self.max_instances,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_results": len(self.results)
        }


# ============================================================
# REAL-WORLD SCENARIO DEMOS
# ============================================================

async def demo_ecommerce_scraping():
    """Demo: Scrape e-commerce product listings"""
    logger.info("🛒 Demo: E-commerce Scraping")
    
    agent = WebScraperAgent(max_instances=3)
    
    tasks = [
        ScrapingTask(
            url="https://www.amazon.com/s?k=laptop",
            scenario=ScenarioType.ECOMMERCE,
            engine=ScraperEngine.PLAYWRIGHT,
            scroll_to_bottom=True,
            selectors={
                "product": "[data-component-type='s-search-result']",
                "title": "h2 span",
                "price": ".a-price-whole",
                "rating": ".a-icon-star-small"
            }
        ),
        ScrapingTask(
            url="https://www.ebay.com/sch/i.html?_nkw=smartphone",
            scenario=ScenarioType.ECOMMERCE,
            engine=ScraperEngine.PLAYWRIGHT
        )
    ]
    
    results = await agent.execute_multi_instance(tasks)
    agent.export_results_to_json("ecommerce_results.json")
    
    return results


async def demo_news_scraping():
    """Demo: Scrape news headlines"""
    logger.info("📰 Demo: News Scraping")
    
    agent = WebScraperAgent(max_instances=4)
    
    tasks = [
        ScrapingTask(
            url="https://news.ycombinator.com/",
            scenario=ScenarioType.NEWS,
            engine=ScraperEngine.REQUESTS,
            selectors={
                "article": ".athing",
                "headline": ".titleline > a",
                "score": ".score"
            }
        ),
        ScrapingTask(
            url="https://www.reddit.com/r/technology/",
            scenario=ScenarioType.NEWS,
            engine=ScraperEngine.PLAYWRIGHT
        ),
        ScrapingTask(
            url="https://techcrunch.com/",
            scenario=ScenarioType.NEWS,
            engine=ScraperEngine.PLAYWRIGHT
        )
    ]
    
    results = await agent.execute_multi_instance(tasks)
    agent.export_results_to_csv("news_results.csv")
    
    return results


async def demo_job_scraping():
    """Demo: Scrape job listings"""
    logger.info("💼 Demo: Job Listings Scraping")
    
    agent = WebScraperAgent(max_instances=2)
    
    tasks = [
        ScrapingTask(
            url="https://www.linkedin.com/jobs/search/?keywords=python%20developer",
            scenario=ScenarioType.JOB_LISTINGS,
            engine=ScraperEngine.PLAYWRIGHT,
            scroll_to_bottom=True
        ),
        ScrapingTask(
            url="https://www.indeed.com/jobs?q=data+scientist",
            scenario=ScenarioType.JOB_LISTINGS,
            engine=ScraperEngine.PLAYWRIGHT
        )
    ]
    
    results = await agent.execute_multi_instance(tasks)
    agent.export_results_to_json("jobs_results.json")
    
    return results


async def demo_financial_scraping():
    """Demo: Scrape financial data"""
    logger.info("💰 Demo: Financial Data Scraping")
    
    agent = WebScraperAgent(max_instances=2)
    
    tasks = [
        ScrapingTask(
            url="https://finance.yahoo.com/most-active",
            scenario=ScenarioType.FINANCIAL,
            engine=ScraperEngine.PLAYWRIGHT,
            scroll_to_bottom=True
        )
    ]
    
    results = await agent.execute_multi_instance(tasks)
    agent.export_results_to_json("financial_results.json")
    
    return results


# ============================================================
# MAIN EXECUTION
# ============================================================

async def main():
    """Main execution - Run all real-world scenarios"""
    logger.info("=" * 60)
    logger.info("🤖 RPA Web Scraper Agent - MultiAgent Platform")
    logger.info("=" * 60)
    
    # Run demos
    demos = [
        ("E-Commerce", demo_ecommerce_scraping),
        ("News", demo_news_scraping),
        ("Job Listings", demo_job_scraping),
        ("Financial Data", demo_financial_scraping)
    ]
    
    for name, demo_func in demos:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"🚀 Running: {name} Scraping Demo")
        logger.info(f"{'=' * 60}\n")
        
        try:
            results = await demo_func()
            logger.success(f"✅ {name} Demo completed: {len(results)} results")
        except Exception as e:
            logger.error(f"❌ {name} Demo failed: {str(e)}")
    
    logger.info(f"\n{'=' * 60}")
    logger.info("🎉 All scraping demos completed!")
    logger.info(f"{'=' * 60}")


# Agent instance for external use
agent = WebScraperAgent(max_instances=5)


if __name__ == "__main__":
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Run main
    asyncio.run(main())
