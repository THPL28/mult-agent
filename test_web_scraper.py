"""
🚀 Quick Test - Web Scraper Agent
Simple execution test with safe URLs
"""

import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.agents.rpa.web_scraper import (
    WebScraperAgent,
    ScrapingTask,
    ScenarioType,
    ScraperEngine
)
from loguru import logger


async def quick_test():
    """Quick test with safe, fast URLs"""
    
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║           🤖 RPA WEB SCRAPER - QUICK TEST 🤖            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    logger.info("🚀 Initializing Web Scraper Agent...")
    
    # Create agent with 5 parallel instances
    agent = WebScraperAgent(max_instances=5)
    
    # Define quick test tasks (safe, fast URLs)
    tasks = [
        # Test Site 1: Quotes to Scrape
        ScrapingTask(
            url="https://quotes.toscrape.com/",
            scenario=ScenarioType.CUSTOM,
            engine=ScraperEngine.REQUESTS,
            selectors={
                "quote": ".quote",
                "text": ".text",
                "author": ".author",
                "tags": ".tag"
            }
        ),
        
        # Test Site 2: Books to Scrape
        ScrapingTask(
            url="https://books.toscrape.com/",
            scenario=ScenarioType.ECOMMERCE,
            engine=ScraperEngine.REQUESTS,
            selectors={
                "product": ".product_pod",
                "title": "h3 a",
                "price": ".price_color",
                "rating": ".star-rating"
            }
        ),
        
        # Test Site 3: HackerNews (Fast)
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
        
        # Test Site 4: Example.com (Simple)
        ScrapingTask(
            url="https://example.com/",
            scenario=ScenarioType.CUSTOM,
            engine=ScraperEngine.REQUESTS
        ),
        
        # Test Site 5: Wikipedia Main Page
        ScrapingTask(
            url="https://en.wikipedia.org/wiki/Main_Page",
            scenario=ScenarioType.CUSTOM,
            engine=ScraperEngine.REQUESTS,
            selectors={
                "featured": "#mp-tfa"
            }
        )
    ]
    
    logger.info(f"📊 Executing {len(tasks)} scraping tasks in parallel...")
    
    # Execute all tasks
    results = await agent.execute_multi_instance(tasks)
    
    # Export results
    logger.info("💾 Exporting results...")
    agent.export_results_to_json("test_results.json")
    agent.export_results_to_csv("test_results.csv")
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    health = await agent.health_check()
    print(f"\n✅ Completed: {health['completed_tasks']}")
    print(f"❌ Failed: {health['failed_tasks']}")
    print(f"📈 Total Results: {health['total_results']}")
    
    print("\n" + "=" * 60)
    print("🎯 DETAILED RESULTS")
    print("=" * 60)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.url}")
        print(f"   ├─ Status: {result.status}")
        print(f"   ├─ Scenario: {result.scenario.value}")
        print(f"   ├─ Execution Time: {result.execution_time:.2f}s")
        print(f"   └─ Data Keys: {list(result.data.keys())}")
        
        # Show sample data
        for key, value in result.data.items():
            if isinstance(value, list) and len(value) > 0:
                sample = str(value[0])[:80]
                print(f"      └─ {key}: {sample}...")
                break
            elif isinstance(value, str) and len(value) > 0:
                sample = value[:80]
                print(f"      └─ {key}: {sample}...")
                break
    
    print("\n" + "=" * 60)
    print("📁 FILES CREATED")
    print("=" * 60)
    print("  ✓ test_results.json")
    print("  ✓ test_results.csv")
    print("  ✓ logs/rpa_web_scraper_*.log")
    print("=" * 60)
    
    logger.success("\n✅ Quick test completed successfully!")


if __name__ == "__main__":
    try:
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        
        # Run test
        asyncio.run(quick_test())
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
