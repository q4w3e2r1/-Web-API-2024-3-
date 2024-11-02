from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from bs4 import BeautifulSoup
import pandas as pd

driver = webdriver.Chrome() 
driver.get("https://www.sdvor.com/moscow/category/valiki-6173")

last_height = driver.execute_script("return document.body.scrollHeight")

while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break  
    last_height = new_height


soup = BeautifulSoup(driver.page_source, "html.parser")

products = soup.find_all('sd-product-grid-item', class_='product-grid-item')

product_list = []

for product in products:
    product_code = product.find(class_='code-value').get_text().strip() if product.find(class_='code-value') else None
    product_info = product.find(class_='product-name').get_text().strip() if product.find(class_='product-name') else None
    price_element = product.find('span', class_='main').get_text().strip() if product.find('span', class_='main') else None


    product_name = product_info[0:6]
    product_description = product_info[6:]

    product_price = price_element[:-2]
    currency = price_element[-1:]

    
    # Добавление информации о товаре в список
    product_list.append({
        'code': product_code,
        'name': product_name,
        'description': product_description,
        'price': product_price,
        'currency': currency
    })


# for item in product_list:
#     print(f"Код: {item['code']}, Описание: {item['name']}, Цена: {item['price']}, Валюта: {item['currency']}")
driver.quit()


df = pd.DataFrame(product_list)
df.to_excel('products.xlsx', index=False, engine='openpyxl') 
