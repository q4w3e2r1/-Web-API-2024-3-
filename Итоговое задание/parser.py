import requests
import pandas as pd

# сама страница сайта: https://www.sdvor.com/moscow/category/valiki-6173


def get_products():
    """
    Получает информацию о продуктах из API SDVOR.
    """
    headers = {
        'accept': 'application/json, text/plain, */*', 
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',
    }

    current_page = 0  # Начинаем с первой страницы
    info = []  # Список для хранения информации о продуктах

    while True:  # Бесконечный цикл для получения всех страниц
        response = requests.get(
        f'https://api-ecomm.sdvor.com/occ/v2/sd/products/search?fields=algorithmsForAddingRelatedProducts%2CcategoryCode%2Cproducts(code%2Cbonus%2Cslug%2CdealType%2Cname%2Cunit%2Cunits(FULL)%2CunitPrices(FULL)%2CavailableInStores(FULL)%2Cbadges(DEFAULT)%2Cmultiunit%2Cprice(FULL)%2CcrossedPrice(FULL)%2CtransitPrice(FULL)%2CpersonalPrice(FULL)%2Cimages(DEFAULT)%2Cstock(FULL)%2CmarketingAttributes%2CisArchive%2Ccategories(FULL)%2CcategoryNamesForAnalytics)%2Cfacets%2Cbreadcrumbs%2Cpagination(DEFAULT)%2Csorts(DEFAULT)%2Cbanners(FULL)%2CfreeTextSearch%2CcurrentQuery%2CkeywordRedirectUrl&facets=allCategories%3Avaliki-6173&pageSize=15&currentPage={current_page}&lang=ru&curr=RUB&deviceType=desktop&baseStore=moscow',
            headers=headers,
        )
        products = (response.json())['products']  # Извлекаем список продуктов из ответа
        if len(products) == 0:  # Если продуктов нет, выходим из цикла
            break
        for product in products:  # Проходим по каждому продукту
            name, description = product['name'].split(' ', 1)  # Разделяем имя и описание продукта
            info.append((product['code'], name, description, product['price']['value']))  # Добавляем информацию о продукте в список
        current_page += 1  # Переходим к следующей странице

    return info  # Возвращаем собранную информацию о продуктах
