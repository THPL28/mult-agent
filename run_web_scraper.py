"""
🚀 Web Scraper Agent Runner
Execute the RPA Web Scraper with real-world scenarios
"""

import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.agents.rpa.web_scraper import (
    WebScraperAgent,
    ScrapingTask,
    ScenarioType,
    ScraperEngine,
    demo_ecommerce_scraping,
    demo_news_scraping,
    demo_job_scraping,
    demo_financial_scraping
)
from loguru import logger


async def run_custom_scenario():
    """Run a custom scraping scenario"""
    logger.info("🎯 Running Custom Scraping Scenario")
    
    agent = WebScraperAgent(max_instances=10)  # 10 parallel instances
    
    # Real-world scraping tasks
    tasks = [
        # Tech News
        ScrapingTask(
            url="https://news.ycombinator.com/",
            scenario=ScenarioType.NEWS,
            engine=ScraperEngine.REQUESTS,
            selectors={
                "article": ".athing",
                "headline": ".titleline > a",
                "score": ".score",
                "comments": "a:contains('comments')"
            }
        ),
        
        # GitHub Trending
        ScrapingTask(
            url="https://github.com/trending",
            scenario=ScenarioType.CUSTOM,
            engine=ScraperEngine.PLAYWRIGHT,
            selectors={
                "repo": "article.Box-row",
                "title": "h2 a",
                "description": "p",
                "stars": "span.d-inline-block.float-sm-right"
            }
        ),
        
        # Product Hunt
        ScrapingTask(
            url="https://www.producthunt.com/",
            scenario=ScenarioType.CUSTOM,
            engine=ScraperEngine.PLAYWRIGHT,
            scroll_to_bottom=True,
            selectors={
                "product": "[data-test='post-item']",
                "name": "h3",
                "description": "p"
            }
        ),
        
        # Stack Overflow Jobs
        ScrapingTask(
            url="https://stackoverflow.com/jobs",
            scenario=ScenarioType.JOB_LISTINGS,
            engine=ScraperEngine.PLAYWRIGHT
        ),
        
        # Medium Articles
        ScrapingTask(
            url="https://medium.com/tag/artificial-intelligence",
            scenario=ScenarioType.NEWS,
            engine=ScraperEngine.PLAYWRIGHT,
            scroll_to_bottom=True
        ),
        
        # Dev.to Articles
        ScrapingTask(
            url="https://dev.to/",
            scenario=ScenarioType.NEWS,
            engine=ScraperEngine.PLAYWRIGHT,
            selectors={
                "article": ".crayons-story",
                "title": "h2, h3",
                "author": ".crayons-story__secondary"
            }
        ),
        
        # Reddit Python
        ScrapingTask(
            url="https://www.reddit.com/r/Python/",
            scenario=ScenarioType.NEWS,
            engine=ScraperEngine.PLAYWRIGHT
        ),
        
        # Quotes to Scrape (Testing)
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
        
        # Books to Scrape (Testing)
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
        
        # Wikipedia Featured Article
        ScrapingTask(
            url="https://en.wikipedia.org/wiki/Main_Page",
            scenario=ScenarioType.CUSTOM,
            engine=ScraperEngine.REQUESTS,
            selectors={
                "featured": "#mp-tfa",
                "news": "#mp-itn"
            }
        )
    ]
    
    # Execute all tasks in parallel
    results = await agent.execute_multi_instance(tasks)
    
    # Export results
    agent.export_results_to_json("web_scraper_results.json")
    agent.export_results_to_csv("web_scraper_results.csv")
    
    # Display summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 SCRAPING SUMMARY")
    logger.info("=" * 60)
    
    health = await agent.health_check()
    logger.info(f"✅ Completed Tasks: {health['completed_tasks']}")
    logger.info(f"❌ Failed Tasks: {health['failed_tasks']}")
    logger.info(f"📈 Total Results: {health['total_results']}")
    
    # Show sample results
    logger.info("\n" + "=" * 60)
    logger.info("🎯 SAMPLE RESULTS")
    logger.info("=" * 60)
    
    for i, result in enumerate(results[:3], 1):
        logger.info(f"\n{i}. {result.url}")
        logger.info(f"   Status: {result.status}")
        logger.info(f"   Scenario: {result.scenario.value}")
        logger.info(f"   Execution Time: {result.execution_time:.2f}s")
        logger.info(f"   Data Keys: {list(result.data.keys())}")
        
        # Show first item if available
        for key, value in result.data.items():
            if isinstance(value, list) and len(value) > 0:
                logger.info(f"   {key} (sample): {str(value[0])[:100]}...")
                break
    
    logger.info("\n" + "=" * 60)
    logger.info("📁 Results saved to:")
    logger.info("   - web_scraper_results.json")
    logger.info("   - web_scraper_results.csv")
    logger.info("=" * 60)
    
    return results


async def main():
    """Main execution"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║           🤖 RPA WEB SCRAPER AGENT 🤖                   ║
    ║                                                          ║
    ║     Multi-Instance Intelligent Web Automation           ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    
    Scenarios Available:
    ════════════════════════════════════════════════════════════
    
    1. 🛒 E-Commerce Scraping
       - Amazon, eBay product listings
       - Price monitoring, product data
    
    2. 📰 News Scraping
       - HackerNews, Reddit, TechCrunch
       - Headlines, articles, trending topics
    
    3. 💼 Job Listings
       - LinkedIn, Indeed, Stack Overflow
       - Remote jobs, tech positions
    
    4. 💰 Financial Data
       - Yahoo Finance, stock data
       - Market trends, crypto prices
    
    5. 🎯 Custom Scenario
       - GitHub trending, Product Hunt
       - Wikipedia, Dev.to, Medium
       - 10 parallel real-world tasks
    
    ════════════════════════════════════════════════════════════
    """)
    
    print("Select a scenario to run:")
    print("1. E-Commerce Scraping")
    print("2. News Scraping")
    print("3. Job Listings")
    print("4. Financial Data")
    print("5. Custom Multi-Instance (10 tasks)")
    print("6. Run ALL Scenarios")
    print()
    
    choice = input("Enter choice (1-6) or press Enter for option 5: ").strip() or "5"
    
    try:
        if choice == "1":
            await demo_ecommerce_scraping()
        elif choice == "2":
            await demo_news_scraping()
        elif choice == "3":
            await demo_job_scraping()
        elif choice == "4":
            await demo_financial_scraping()
        elif choice == "5":
            await run_custom_scenario()
        elif choice == "6":
            logger.info("🚀 Running ALL Scenarios...")
            await demo_ecommerce_scraping()
            await demo_news_scraping()
            await demo_job_scraping()
            await demo_financial_scraping()
            await run_custom_scenario()
        else:
            logger.error("Invalid choice. Running custom scenario by default.")
            await run_custom_scenario()
        
        logger.success("\n✅ Web Scraper Agent execution completed successfully!")
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Execution interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    # Run
    asyncio.run(main())
