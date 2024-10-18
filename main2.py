import json
import re
import asyncio
import time
import random

import aiohttp
import requests
from bs4 import BeautifulSoup

headers = {
    "user-agent":
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "accept":
        "application/json,text/plain,*/*"
}


all_products_list = []
num = 1


async def gather_data():
    url = "https://online.metro-cc.ru/category/chaj-kofe-kakao/chay?in_stock=1"
    async with aiohttp.ClientSession() as session:
        response = await session.get(url=url, headers=headers)
        soup = BeautifulSoup(await response.text(), "lxml")

        # Поиск пагинатора для того, чтобы узнать, сколько страниц с товарами есть в выбранной категории
        pages_count = int(soup.find("ul", class_="catalog-paginate").find_all("li")[-2].find("a").string)

        tasks = []

        for page in range(1, pages_count + 1):
            task = asyncio.create_task(get_page_data(session, page))
            tasks.append(task)

        await asyncio.gather(*tasks)


async def get_page_data(session, page):
    _url = "https://online.metro-cc.ru/category/chaj-kofe-kakao/chay?in_stock=1"
    url = f"{_url}&page={page}"  # Ссылка на страницу №page

    async with session.get(url=url, headers=headers) as response:
        response_text = await response.text()
        soup = BeautifulSoup(response_text, "lxml")

        # Список всех продуктов на странице
        all_products = soup.find("div", class_="subcategory-or-type__products").find_all("div", class_="product-card")

        for product in all_products:
            id_product = product.get("id")
            try:
                url_product = "https://online.metro-cc.ru" + product.find("a", class_="product-card-photo__link").get("href")
                req = requests.get(url_product, headers=headers)

                soup = BeautifulSoup(req.text, "lxml")
                brand_product = soup.find("div", class_="product-attributes").find("span",
                                                                                   string=re.compile("Бренд")).find_parent(
                    "li", "product-attributes__list-item").find("a").string.strip()

            except Exception:
                brand_product = "Нет бренда"
                url_product = "Нет ссылки на продукт"

            try:
                name_product = product.find("span", class_="product-card-name__text").string.strip()
            except Exception:
                name_product = "Нет наименования"

            try:
                price_actual = product.find("div", class_="product-unit-prices__actual-wrapper").find("span",
                                                                                                   class_="product-price__sum-rubles").string
            except Exception:
                price_actual = "Нет актуальной цены"

            try:
                price_old = product.find("div", class_="product-unit-prices__old-wrapper").find("span",
                                                                                             class_="product-price__sum-rubles").string
            except Exception:
                price_old = "Нет старой цены"

            all_products_list.append(
                {
                    "id": id_product,
                    "Наименование": name_product,
                    "Ссылка": url_product,
                    "Бренд": brand_product,
                    "Актуальная цена": price_actual,
                    "Старая цена": price_old
                }
            )

            global num
            # print(f"{num} {id_product} {name_product} {brand_product} {price_actual}Р {price_old}Р")
            num += 1
        print(f"обработана страница #{page}")


def main():
    url = "https://online.metro-cc.ru/category/chaj-kofe-kakao/chay?in_stock=1"  # Ссылка на категорию с параметром "В наличии"
    asyncio.run(gather_data())
    with open("data2.json", "a") as file:
        json.dump(all_products_list, file, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()
