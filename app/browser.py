from playwright.async_api import async_playwright

async def get_browser(app):
    """Get or create a shared Playwright browser instance."""
    if not hasattr(app, "_playwright_browser"):
        app._playwright_context = await async_playwright().start()
        app._playwright_browser = await app._playwright_context.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage"],
        )
        app.logger.info("Browser instance created.")
    return app._playwright_browser


async def close_browser(app):
    """Close the shared Playwright browser instance."""
    if hasattr(app, "_playwright_browser"):
        try:
            await app._playwright_browser.close()
            await app._playwright_context.stop()
            app.logger.info("Browser instance closed.")
        except Exception as e:
            app.logger.error(f"Error closing browser: {e}")
        finally:
            del app._playwright_browser
            del app._playwright_context
