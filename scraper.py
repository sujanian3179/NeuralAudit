"""
State-Aware Scraper Module
Captures (Image_URL, Color_Label) pairs by interacting with e-commerce product pages
"""
import time
from typing import List, Tuple, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementNotInteractableException
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from logger import logger
from config import (
    SELENIUM_HEADLESS,
    SELENIUM_WAIT_TIMEOUT,
    SELENIUM_IMPLICIT_WAIT,
    SCREENSHOT_ON_ERROR
)


class ProductScraper:
    """
    Scrapes product pages with dynamic color swatches using Selenium.
    Mimics user interaction to capture image-color pairs.
    """
    
    def __init__(self):
        """Initialize the Selenium WebDriver"""
        self.driver = None
        self.wait = None
        self._init_driver()
    
    def _init_driver(self):
        """Initialize Chrome WebDriver with configured options"""
        try:
            options = webdriver.ChromeOptions()
            if SELENIUM_HEADLESS:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(SELENIUM_IMPLICIT_WAIT)
            self.wait = WebDriverWait(self.driver, SELENIUM_WAIT_TIMEOUT)
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def _take_screenshot(self, filename: str = "error_screenshot.png"):
        """Take screenshot for debugging"""
        if SCREENSHOT_ON_ERROR:
            try:
                screenshot_path = f"./screenshots/{filename}"
                os.makedirs("./screenshots", exist_ok=True)
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Screenshot saved: {screenshot_path}")
            except Exception as e:
                logger.warning(f"Failed to save screenshot: {e}")
    
    def scrape_product(self, product_url: str) -> List[Tuple[str, str]]:
        """
        Scrape all variant pairs from a product page.
        
        Args:
            product_url: URL of the e-commerce product page
        
        Returns:
            List of tuples: [(image_url, color_label), ...]
        
        Raises:
            Exception: If scraping fails
        """
        variant_pairs = []
        
        try:
            logger.info(f"Loading product page: {product_url}")
            self.driver.get(product_url)
            time.sleep(2)  # Wait for page to fully load
            
            # Find all color swatch elements
            color_swatches = self._find_color_swatches()
            
            if not color_swatches:
                logger.warning(f"No color swatches found on {product_url}")
                return variant_pairs
            
            logger.info(f"Found {len(color_swatches)} color variants")
            
            # Iterate through each color swatch
            for idx, swatch in enumerate(color_swatches):
                try:
                    # Re-find swatches to avoid stale elements
                    color_swatches = self._find_color_swatches()
                    if idx >= len(color_swatches):
                        break
                    
                    swatch = color_swatches[idx]
                    
                    # Click the swatch
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", swatch)
                    time.sleep(0.5)
                    self._safe_click(swatch)
                    time.sleep(1.5)  # Wait for DOM to update
                    
                    # Get the image URL and color label
                    image_url = self._get_product_image()
                    color_label = self._get_color_label(swatch)
                    
                    if image_url and color_label:
                        variant_pairs.append((image_url, color_label))
                        logger.info(f"Captured variant {idx + 1}: {color_label}")
                    
                except (StaleElementReferenceException, ElementNotInteractableException) as e:
                    logger.warning(f"Error processing swatch {idx}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error processing swatch {idx}: {e}")
                    self._take_screenshot(f"error_swatch_{idx}.png")
                    continue
            
            logger.info(f"Successfully scraped {len(variant_pairs)} variants from {product_url}")
            return variant_pairs
        
        except TimeoutException:
            logger.error(f"Timeout loading product page: {product_url}")
            self._take_screenshot("timeout.png")
            raise
        except Exception as e:
            logger.error(f"Error scraping product {product_url}: {e}")
            self._take_screenshot("scrape_error.png")
            raise
    
    def _find_color_swatches(self) -> List:
        """
        Find all color swatch elements on the page.
        This uses common e-commerce selectors.
        
        Returns:
            List of WebElements representing color swatches
        """
        selectors = [
            "div[data-color-swatch]",
            "button[data-color]",
            "li[data-color-option]",
            ".color-swatch",
            ".swatch-color",
            "[role='button'][aria-label*='color' i]",
            ".product-variant-swatch",
            "div.swatch",
        ]
        
        for selector in selectors:
            try:
                swatches = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if swatches:
                    logger.info(f"Found color swatches using selector: {selector}")
                    return swatches
            except NoSuchElementException:
                continue
        
        logger.warning("Could not find color swatches with common selectors")
        return []
    
    def _safe_click(self, element):
        """Safely click an element with fallback to JS click"""
        try:
            element.click()
        except ElementNotInteractableException:
            self.driver.execute_script("arguments[0].click();", element)
    
    def _get_product_image(self) -> Optional[str]:
        """
        Get the src URL of the main product image.
        
        Returns:
            Image URL or None
        """
        selectors = [
            "img.product-image",
            "img[alt*='product' i]",
            ".product-main-image img",
            ".main-image img",
            "img.main-product-image",
            ".product-photo img",
            "img[role='img']",
        ]
        
        for selector in selectors:
            try:
                img_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                src = img_element.get_attribute("src")
                if src:
                    return src
            except NoSuchElementException:
                continue
        
        logger.warning("Could not find product image")
        return None
    
    def _get_color_label(self, swatch_element) -> Optional[str]:
        """
        Extract the color label from a swatch element.
        
        Args:
            swatch_element: WebElement of the color swatch
        
        Returns:
            Color label string or None
        """
        # Try to get from aria-label
        aria_label = swatch_element.get_attribute("aria-label")
        if aria_label:
            return aria_label.strip()
        
        # Try to get from title attribute
        title = swatch_element.get_attribute("title")
        if title:
            return title.strip()
        
        # Try to get from data-color attribute
        data_color = swatch_element.get_attribute("data-color")
        if data_color:
            return data_color.strip()
        
        # Try to get text content
        try:
            text = swatch_element.text.strip()
            if text:
                return text
        except:
            pass
        
        logger.warning("Could not extract color label from swatch")
        return None
    
    def close(self):
        """Close the WebDriver"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
        except Exception as e:
            logger.error(f"Error closing WebDriver: {e}")


def scrape_batch(product_urls: List[str]) -> dict:
    """
    Scrape multiple product URLs.
    
    Args:
        product_urls: List of product URLs to scrape
    
    Returns:
        Dictionary with results: {url: [(image_url, color_label), ...], ...}
    """
    scraper = ProductScraper()
    results = {}
    
    try:
        for url in product_urls:
            try:
                pairs = scraper.scrape_product(url)
                results[url] = pairs
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                results[url] = []
    
    finally:
        scraper.close()
    
    return results


if __name__ == "__main__":
    import os
    # Example usage
    test_urls = [
        "https://www.amazon.in/Insulated-Bottle-Stainless-Warranty-Military/dp/B0CLXVWX25/ref=sr_1_2_sspa?crid=2FUZWK8JY2VVM&dib=eyJ2IjoiMSJ9.kJ-6FlyjSF51uVJd4pRr7FZEOxfVzPnMgR8HmQhLVproQv5nODT__lh2ZmlwcDaqi6cYiYN1Mu90sWERFZnI3lsDVfhViHtR-kIW_bV3S8ivCoxgOEu3NC0P60LooV9uEsMRU_cGPF-psnt0CQmbRWhrdL3xOK3DqDC1b7_-T9RxHAxkANGX7EhXbCgq9r0Wg2OBpmOJWrXo4ikcJEPpL0Ul2NikBvzLy8IVkqkG6qQcJOYiFSD05HjdCunxsQ8G9raotHxEgfhULZPGBKNeHdhSHZb-6hDQGG4KPRbbIXA._v_DQH3vFyRE5UvL_165HiGqexBVc-AuLen6YQ7Irm0&dib_tag=se&keywords=water%2Bbottle%2B1%2Bltr&qid=1777112909&sprefix=water%2Bbottle%2Caps%2C428&sr=8-2-spons&aref=1r3IfYuycp&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1"
    ]
    
    results = scrape_batch(test_urls)
    for url, pairs in results.items():
        print(f"\n{url}:")
        for img_url, color in pairs:
            print(f"  - {color}: {img_url}")
