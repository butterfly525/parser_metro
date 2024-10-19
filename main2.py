import json
import re
import asyncio
import time
import random
import logging

import aiohttp
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "accept": "application/json,text/plain,*/*"
}

# Список User-Agents для ротации
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/573.1.1 (KHTML, like Gecko) Version/12.1.2 Safari/573.1.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/94.0.4606.55 Mobile/16A366 Safari/604.1"
]

all_products_list = []
num = 1


async def gather_data():
    url = "https://online.metro-cc.ru/category/chaj-kofe-kakao/chay?in_stock=1"

    # Переключение User-Agent для каждого запроса
    headers["User-Agent"] = random.choice(user_agents)

    async with aiohttp.ClientSession() as session:
        response = await session.get(url=url, headers=headers)
        soup = BeautifulSoup(await response.text(), "lxml")

        pages_count = int(soup.find("ul", class_="catalog-paginate").find_all("li")[-2].find("a").string)

        tasks = []

        for page in range(1, pages_count + 1):
            task = asyncio.create_task(get_page_data(session, page))
            tasks.append(task)
            time.sleep(random.uniform(2, 4))  # Случайная задержка между 2 и 4 секундами
        await asyncio.gather(*tasks)


async def get_page_data(session, page):
    _url = "https://online.metro-cc.ru/category/chaj-kofe-kakao/chay?in_stock=1"
    url = f"{_url}&page={page}"

    # Переключение User-Agent для каждого запроса
    headers["User-Agent"] = random.choice(user_agents)

    async with session.get(url=url, headers=headers) as response:
        response.raise_for_status()  # Поднимаем исключение для плохих статус-кодов
        response_text = await response.text()

        soup = BeautifulSoup(response_text, "lxml")
        all_products = soup.find("div", class_="subcategory-or-type__products").find_all("div", class_="product-card")

        for product in all_products:
            id_product = product.get("id")
            try:
                url_product = "https://online.metro-cc.ru" + product.find("a", class_="product-card-photo__link").get(
                    "href")
                req = requests.get(url_product, headers={"User-Agent": random.choice(user_agents)})

                soup = BeautifulSoup(req.text, "lxml")
                brand_product = soup.find("div", class_="product-attributes").find("span",
                                                                                   string=re.compile(
                                                                                       "Бренд")).find_parent(
                    "li", "product-attributes__list-item").find("a").string.strip()

            except Exception as e:
                logging.error(f"Ошибка при получении деталей продукта: {str(e)}")
                brand_product = "Нет бренда"
                url_product = "Нет ссылки на продукт"

            try:
                name_product = product.find("span", class_="product-card-name__text").string.strip()
            except Exception as e:
                logging.error(f"Ошибка получения названия продукта: {str(e)}")
                name_product = "Нет наименования"

            try:
                price_actual = product.find("div", class_="product-unit-prices__actual-wrapper").find("span",
                                                                                                      class_="product-price__sum-rubles").string
            except Exception as e:
                logging.error(f"Ошибка получения актуальной цены: {str(e)}")
                price_actual = "Нет актуальной цены"

            try:
                price_old = product.find("div", class_="product-unit-prices__old-wrapper").find("span",
                                                                                                class_="product-price__sum-rubles").string
            except Exception as e:
                logging.error(f"Ошибка получения старой цены: {str(e)}")
                price_old = "Нет старой цены"

            all_products_list.append({
                "id": id_product,
                "Наименование": name_product,
                "Ссылка": url_product,
                "Бренд": brand_product,
                "Актуальная цена": price_actual,
                "Старая цена": price_old
            })

            global num
            logging.info(
                f"Обработан продукт {num}: {id_product} {name_product} {brand_product} {price_actual}R {price_old}R")
            num += 1

        time.sleep(random.uniform(2, 4))  # Случайная задержка после обработки каждой страницы


def main():
    url = "https://online.metro-cc.ru/category/chaj-kofe-kakao/chay?in_stock=1"
    asyncio.run(gather_data())
    with open("data2.json", "a", encoding="utf-8") as file:
        json.dump(all_products_list, file, indent=4, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()
