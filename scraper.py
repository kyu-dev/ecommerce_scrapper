from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import re

options = Options()
options.headless = True


def get_products_links(page):
    driver = webdriver.Chrome(options=options)
    driver.get(f"https://www.vandb.fr/biere?page={page}")
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
    driver.quit()  

def get_data_products(page):
    driver = webdriver.Chrome(options=options)
    driver.get(page)
    
    # Attendre que la page se charge complètement
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
    )

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    product_data = {}
    
    # Récupérer le nom du produit
    name_element = soup.select_one("h1")
    product_data['nom'] = name_element.get_text(strip=True) if name_element else "Non trouvé"
    
    # Récupérer l'image du produit
    image_element = soup.select_one("img.product-detail__image")
    if not image_element:
        image_element = soup.select_one("img.product-image")
    if not image_element:
        image_element = soup.select_one("img[src*='product']")
    if not image_element:
        image_element = soup.select_one(".product-gallery img")
    
    if image_element and 'src' in image_element.attrs:
        image_src = image_element['src']
        # Si l'URL est relative, la rendre absolue
        if image_src.startswith('/'):
            image_src = "https://www.vandb.fr" + image_src
        product_data['image'] = image_src
    else:
        product_data['image'] = "Non trouvé"
    
    # Récupérer la description
    description_element = soup.select_one(".product-detail__description, .product-description, .description")
    if not description_element:
        description_element = soup.select_one("div[class*='description']")
    product_data['description'] = description_element.get_text(strip=True) if description_element else "Non trouvé"
    
    # Récupérer le degré d'alcool
    product_data['degre_alcool'] = "Non trouvé"
    
    # 1. Chercher dans la section spécifications (classe spécifique)
    specs_section = soup.select_one(".product-custom-block.product-specification.full--yellow")
    if specs_section:
        specs_text = specs_section.get_text()
        # Chercher le degré d'alcool
        alcohol_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*[%°](?:\s*vol)?', specs_text)
        if alcohol_match:
            alcohol_value = alcohol_match.group(1)
            product_data['degre_alcool'] = f"{alcohol_value}%"
    
    # 2. Si pas trouvé, chercher dans d'autres sections techniques
    if product_data['degre_alcool'] == "Non trouvé":
        other_specs = soup.select_one(".product-technical-infos, .product-specs, .product-details, .product-info")
        if other_specs:
            all_text = other_specs.get_text()
            alcohol_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*[%°](?:\s*vol)?', all_text)
            if alcohol_match:
                alcohol_value = alcohol_match.group(1)
                product_data['degre_alcool'] = f"{alcohol_value}%"
    
    # 3. Si toujours pas trouvé, chercher dans toute la page
    if product_data['degre_alcool'] == "Non trouvé":
        all_page_text = soup.get_text()
        alcohol_matches = re.findall(r'(\d+(?:[,\.]\d+)?)\s*[%°](?:\s*vol)?', all_page_text)
        if alcohol_matches:
            # Prendre la première valeur trouvée qui semble être un degré d'alcool (entre 0 et 20)
            for match in alcohol_matches:
                try:
                    alcohol_val = float(match.replace(',', '.'))
                    if 0 <= alcohol_val <= 20: 
                        product_data['degre_alcool'] = f"{match}%"
                        break
                except ValueError:
                    continue
    
    # Récupérer la catégorie de bière
    product_data['categorie'] = "Non trouvé"
    
    # 1. Chercher dans la section spécifications (classe spécifique)
    specs_section = soup.select_one(".product-custom-block.product-specification.full--yellow")
    if specs_section:
        specs_text = specs_section.get_text().lower()
        categories = ['blonde', 'brune', 'blanche', 'rousse', 'ambrée', 'ipa', 'pils', 'stout', 'porter', 'weizen', 'berliner', 'triple', 'saison']
        for cat in categories:
            if cat in specs_text:
                product_data['categorie'] = cat.capitalize()
                break
    
    # 2. Si pas trouvé, chercher dans le fil d'Ariane
    if product_data['categorie'] == "Non trouvé":
        breadcrumb = soup.select_one(".breadcrumb, .breadcrumbs")
        if breadcrumb:
            breadcrumb_text = breadcrumb.get_text().lower()
            categories = ['blonde', 'brune', 'blanche', 'rousse', 'ambrée', 'ipa', 'pils', 'stout', 'porter', 'weizen', 'berliner', 'triple', 'saison']
            for cat in categories:
                if cat in breadcrumb_text:
                    product_data['categorie'] = cat.capitalize()
                    break
    
    # 3. Si toujours pas trouvé, chercher dans le titre du produit
    if product_data['categorie'] == "Non trouvé":
        product_name = product_data['nom'].lower()
        categories = ['blonde', 'brune', 'blanche', 'rousse', 'ambrée', 'ipa', 'pils', 'stout', 'porter', 'weizen', 'berliner', 'triple', 'saison']
        for cat in categories:
            if cat in product_name:
                product_data['categorie'] = cat.capitalize()
                break
    
    # 4. En dernier recours, chercher dans la description
    if product_data['categorie'] == "Non trouvé":
        description_text = product_data['description'].lower()
        categories = ['blonde', 'brune', 'blanche', 'rousse', 'ambrée', 'ipa', 'pils', 'stout', 'porter', 'weizen', 'berliner', 'triple', 'saison']
        for cat in categories:
            if cat in description_text:
                product_data['categorie'] = cat.capitalize()
                break
    
    
    # Récupérer la quantité
    product_data['quantite'] = "Non trouvé"
    
    # 1. Chercher dans la section spécifications (classe spécifique)
    specs_section = soup.select_one(".product-custom-block.product-specification.full--yellow")
    if specs_section:
        specs_text = specs_section.get_text()
        # Chercher la quantité
        quantity_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*(cl|ml|l)\b', specs_text, re.IGNORECASE)
        if quantity_match:
            quantity = quantity_match.group(1)
            unit = quantity_match.group(2).lower()
            product_data['quantite'] = f"{quantity} {unit}"
    
    # 2. Si pas trouvé, chercher dans le titre du produit (fallback)
    if product_data['quantite'] == "Non trouvé":
        quantity_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*(cl|ml|l)\b', product_data['nom'], re.IGNORECASE)
        if quantity_match:
            quantity = quantity_match.group(1)
            unit = quantity_match.group(2).lower()
            product_data['quantite'] = f"{quantity} {unit}"
    
    # 3. Si toujours pas trouvé, chercher dans d'autres sections techniques
    if product_data['quantite'] == "Non trouvé":
        other_specs = soup.select_one(".product-technical-infos, .product-specs, .product-details, .product-info")
        if other_specs:
            specs_text = other_specs.get_text()
            quantity_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*(cl|ml|l)\b', specs_text, re.IGNORECASE)
            if quantity_match:
                quantity = quantity_match.group(1)
                unit = quantity_match.group(2).lower()
                product_data['quantite'] = f"{quantity} {unit}"
    
    
    driver.quit()
    return product_data

def scrape_all_products(num_products=5):
    # Récupérer tous les liens des produits
    driver = webdriver.Chrome(options=options)
    driver.get(f"https://www.vandb.fr/biere?page=1")
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
    
    driver.quit()
    
    # Récupérer les données pour chaque produit
    all_products_data = []
    for i, link in enumerate(links[:num_products]):
        print(f"Récupération des données pour le produit {i+1}/{num_products}: {link}")
        try:
            product_data = get_data_products(link)
            product_data['url'] = link
            all_products_data.append(product_data)
            print(f"✅ Données récupérées: {product_data['nom']}")
        except Exception as e:
            print(f"❌ Erreur lors de la récupération de {link}: {e}")
    
    # Sauvegarder les données dans un fichier JSON
    with open('products_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_products_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 Données sauvegardées dans 'products_data.json'")
    print(f"📊 Total: {len(all_products_data)} produits récupérés")
    
    return all_products_data

# Test avec quelques produits
if __name__ == "__main__":
    scrape_all_products(5)



      
    
   