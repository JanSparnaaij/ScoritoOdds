# playwright_deps.sh
#!/bin/bash
echo "Installing Playwright dependencies..."
npx playwright install chromium firefox webkit
