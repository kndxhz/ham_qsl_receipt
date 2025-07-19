import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote


def get_zip_code(address: str):
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
    )

    # Initialize the WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # First, visit the main site to get cookies
        driver.get("https://www.youbianku.com/")
        time.sleep(2)  # Wait for JavaScript to load

        # URL-encode the address for the search URL
        encoded_address = quote(address)

        # Construct and navigate to the search URL
        search_url = (
            f"https://www.youbianku.com/SearchResults?address={encoded_address}"
        )
        driver.get(search_url)

        # Wait for the page to load completely including JavaScript
        wait = WebDriverWait(driver, 10)
        selector = "#mw-content-text > div.mw-parser-output > div > ul > div > table > tbody > tr:nth-child(3) > td > a"
        element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

        if element:
            return element.text.strip()
        else:
            print("No elements found matching the CSS selector")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        # Make sure to close the browser
        driver.quit()


if __name__ == "__main__":
    print(get_zip_code(address="黑龙江省绥化市肇东市十三道街移动小区"))
