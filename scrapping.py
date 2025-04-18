from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service


# --- Setup Chrome Options ---
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Run in background
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("--headless=new")

# Updated ChromeDriver init
service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)

# --- Set up ChromeDriver ---
driver = webdriver.Chrome(options=chrome_options)

# --- URL for scraping ---
BASE_URL = "https://www.myntra.com/men-shoes"

# --- Store all product data here ---
all_products = []

# --- Loop through first 5 pages ---
for page in range(1, 6):
    print(f"Scraping page {page}...")
    url = f"{BASE_URL}?p={page}"
    driver.get(url)
    # driver.save_screenshot(f"debug_page_{page}.png")

    # Wait for products to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "product-product"))
    )

    # Get all product containers
    products = driver.find_elements(By.CLASS_NAME, "product-base")

    for product in products:
        try:
            # Get product link
            link_tag = product.find_element(By.TAG_NAME, "a")
            product_link = link_tag.get_attribute("href")
            # driver.execute_script("window.open('');")  # Open new tab
            # driver.switch_to.window(driver.window_handles[1])
            driver.get(product_link)
            # time.sleep(2)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h1[@class='pdp-title']")))

            # --- Extract details ---
            product_id = product_link.split("/")[-2]
            name = driver.find_element(By.XPATH, "//h1[@class='pdp-title']").text
            brand = driver.find_element(By.XPATH, "//h1[@class='pdp-title']/following-sibling::h1").text
            try:
                price = driver.find_element(By.XPATH, "//span[contains(@class, 'pdp-price')]").text
                price = ''.join(filter(str.isdigit, price))
            except:
                price = "N/A"
            try:
                image_url = driver.find_element(By.XPATH, "(//img[contains(@src, 'assets.myntassets.com')])[1]").get_attribute("src")
            except:
                image_url = "N/A"
            print("Page source saved for debugging image:", product_link)
            with open("debug_image.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)

            # Try to extract description, rating, and stock status
            try:
                description = driver.find_element(By.XPATH, "//div[@class='index-rowInfo']").text
            except:
                try:
                    description = driver.find_element(By.XPATH, "//div[@class='pdp-productDescriptorsContainer']").text
                except:
                    description = "N/A"

            try:
                raw_rating = driver.find_element(By.XPATH, "//div[contains(@class,'index-overallRating')]").text
                rating = raw_rating.replace("\n", " | ")
            except:
                rating = "N/A"

            try:
                stock_button = driver.find_element(By.XPATH, "//div[contains(text(),'ADD TO BAG')]")
                stock_status = "In Stock"
            except:
                stock_status = "Out of Stock or Unavailable"

            print(f"Parsed: {name} | {brand} | ₹{price} | {rating} | {stock_status}")

            # --- Save the product data ---
            all_products.append({
                "product_id": product_id,
                "name": name,
                "brand": brand,
                "price": price,
                "image_url": image_url,
                "description": description,
                "rating": rating,
                "stock_status": stock_status,
                "category": "Men Shoes",
                "product_link": product_link
            })

            # driver.close()  # Close the tab
            # driver.switch_to.window(driver.window_handles[0])  # Back to main page

            driver.back()
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "product-base")))

        except Exception as e:
            print("Error:", e)
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            continue

# --- Save to CSV ---
driver.quit()
df = pd.DataFrame(all_products)
df.to_csv("myntra_men_shoes_detailed.csv", index=False)
print("Scraping complete! Data saved to myntra_men_shoes_detailed.csv")