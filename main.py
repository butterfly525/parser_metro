import json
import random
import re
import time
import requests
from bs4 import BeautifulSoup


def get_data(url, storeId):
    headers = {
        "user-agent":
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "accept":
            "*/*,application/json"
    }
    cookies = {'metroStoreId': storeId}
    #Поиск пагинатора, для того, чтобы узнать, сколько страниц с товарами есть в выбранной категории

    req = requests.get(url, headers=headers, cookies=cookies)

    soup = BeautifulSoup(req.text, "lxml")
    #Нахождение предпоследнего li  (в последнем лежит иконка для переключения страницы)
    pages_count = int(soup.find("ul", class_="catalog-paginate").find_all("li")[-2].find("a").string)
    print(pages_count)
    all_products_list = []
    num = 1
    #Перебор всех страниц категории
    for i in range(1, pages_count + 1):
        url_tmp = f"{url}&page={i}"  # Ссылка на i-ую страницу
        print(url_tmp)
        req = requests.get(url_tmp, headers=headers, cookies=cookies)
        soup = BeautifulSoup(req.text, "lxml")

        #Список всех продуктов на странице
        all_products = soup.find("div", class_="subcategory-or-type__products").find_all("div", class_="product-card")

        for product in all_products:
            id_product = product.get("id")
            try:
                url_product = "https://online.metro-cc.ru" + product.find("a", class_="product-card-photo__link").get(
                    "href")
                req = requests.get(url_product, headers=headers, cookies=cookies)
                soup = BeautifulSoup(req.text, "lxml")
                brand_product = soup.find("div", class_="product-attributes").find("span",
                                                                                   string=re.compile(
                                                                                       "Бренд")).find_parent("li",
                                                                                                             "product-attributes__list-item").find(
                    "a").string.strip()

            except Exception:
                brand_product = "Бренд не указан"
                url_product = "url не указан"
            try:
                name_product = product.find("span", class_="product-card-name__text").string.strip()
            except Exception:
                name_product = "Имя не указано"
            try:
                price_actual = product.find("div", class_="product-unit-prices__actual-wrapper").find("span",
                                                                                                      class_="product-price__sum-rubles").string
            except Exception:
                price_actual = "Актуальная цена не указана"
            try:
                price_old = product.find("div", class_="product-unit-prices__old-wrapper").find("span",
                                                                                                class_="product-price__sum-rubles").string
            except Exception:
                price_old = "Старая цена не указана"
            all_products_list.append(
                {
                    "№": num,
                    "id": id_product,
                    "Наименование": name_product,
                    "Ссылка": url_product,
                    "Бренд": brand_product,
                    "Актуальная цена": price_actual,
                    "Старая цена": price_old
                }
            )

            print(f"{num} {id_product} {name_product} {brand_product} {price_actual}Р {price_old}Р")
            num += 1
        # time.sleep(random.randrange(2, 4))
    with open(f"data_storeId_{storeId}.json", "a") as file:
        json.dump(all_products_list, file, indent=4, ensure_ascii=False)


def main():
    url = "https://online.metro-cc.ru/category/chaj-kofe-kakao/chay?in_stock=1"  # Ссылка на категорию с параметром "В наличии"
    get_data(url, "10")  # магазин в Москве
    get_data(url, "15")  # магазин в Питере


if __name__ == '__main__':
    main()
