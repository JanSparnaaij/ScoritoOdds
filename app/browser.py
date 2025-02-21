from playwright.async_api import async_playwright
import glob
import os

async def get_browser(app):
    """Get or create a shared Playwright browser instance."""
    if not hasattr(app, "_playwright"):
        try:
            # Find chrome executable
            chrome_paths = glob.glob("/ms-playwright/chromium-*/chrome-linux/chrome")
            if not chrome_paths:
                app.logger.error("Chrome executable not found!")
                raise FileNotFoundError("Chrome executable not found in /ms-playwright")
            
            chrome_path = chrome_paths[0]
            app.logger.info(f"Using Chrome at: {chrome_path}")
            
            # Start Playwright
            app._playwright = await async_playwright().start()
            app._browser = await app._playwright.chromium.launch(
                headless=True,
                executable_path=chrome_path,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )
            app.logger.info("Browser instance created successfully")
        except Exception as e:
            app.logger.error(f"Error creating browser: {str(e)}")
            if hasattr(app, "_playwright"):
                await app._playwright.stop()
                del app._playwright
            raise
    return app._browser


async def close_browser(app):
    """Close the shared Playwright browser instance."""
    if hasattr(app, "_browser"):
        try:
            await app._browser.close()
            app.logger.info("Browser closed")
        except Exception as e:
            app.logger.error(f"Error closing browser: {e}")
        finally:
            del app._browser

    if hasattr(app, "_playwright"):
        try:
            await app._playwright.stop()
            app.logger.info("Playwright stopped")
        except Exception as e:
            app.logger.error(f"Error stopping playwright: {e}")
        finally:
            del app._playwright
