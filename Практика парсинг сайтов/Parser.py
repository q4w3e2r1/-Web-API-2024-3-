import requests
import pandas as pd

# сама страница сайта: https://www.sdvor.com/moscow/category/valiki-6173

# Заголовки для HTTP-запроса
headers = {
    'accept': 'application/json, text/plain, */*',  # Указываем, что принимаем JSON и текстовые данные
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0',  # Указываем User-Agent для имитации браузера
}

current_page = 0  # Начинаем с первой страницы
info = []  # Список для хранения информации о продуктах

while True:  # Бесконечный цикл для получения всех страниц
    # Формируем URL для запроса с текущей страницей
    url = f'https://api-ecomm.sdvor.com/occ/v2/sd/products/search?fields=algorithmsForAddingRelatedProducts%2CcategoryCode%2Cproducts(code%2Cbonus%2Cslug%2CdealType%2Cname%2Cunit%2Cunits(FULL)%2CunitPrices(FULL)%2CavailableInStores(FULL)%2Cbadges(DEFAULT)%2Cmultiunit%2Cprice(FULL)%2CcrossedPrice(FULL)%2CtransitPrice(FULL)%2CpersonalPrice(FULL)%2Cimages(DEFAULT)%2Cstock(FULL)%2CmarketingAttributes%2CisArchive%2Ccategories(FULL)%2CcategoryNamesForAnalytics)%2Cfacets%2Cbreadcrumbs%2Cpagination(DEFAULT)%2Csorts(DEFAULT)%2Cbanners(FULL)%2CfreeTextSearch%2CcurrentQuery%2CkeywordRedirectUrl&facets=allCategories%3Avaliki-6173&pageSize=15&currentPage={current_page}&lang=ru&curr=RUB&deviceType=desktop&baseStore=moscow'

    # Отправляем GET-запрос к API
    response = requests.get(
        url,
        headers=headers,
    )
    # Извлекаем список продуктов из ответа
    products = (response.json())['products']
    
    # Если продуктов нет, выходим из цикла
    if len(products) == 0:
        break

    # Проходим по каждому продукту и извлекаем нужные данные
    for product in products:
        name, description = product['name'].split(' ', 1)  # Разделяем имя и описание продукта
        # Добавляем информацию о продукте в список
        info.append((product['code'], name, description, product['price']['value']))
    
    current_page += 1  # Переходим к следующей странице

# Создаем DataFrame из собранной информации
df = pd.DataFrame(info, columns=['Код', 'Название', 'Описание', 'Цена'])

# Сохраняем DataFrame в Excel файл
df.to_excel('products_info.xlsx', index=False)

# Выводим сообщение об успешном сохранении данных
print("Данные успешно сохранены в файл products_info.xlsx")
