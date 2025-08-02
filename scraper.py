from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

options = Options()
options.headless = True

driver = webdriver.Chrome(options=options)
driver.get("https://www.vandb.fr/biere?page=1")

try:
    # Attendre jusqu'à 10 secondes que les éléments soient présents
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.product-list-item__content"))
    )

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    links = []
    for product in soup.select("a.product-list-item__content[href]"):
        href = product['href']
        full_url = "https://www.vandb.fr" + href
        links.append(full_url)

    print(links)

finally:
    driver.quit()