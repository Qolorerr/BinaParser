from pprint import pprint

import requests as requests
import bs4


def download_data(url: str):
    if "bina.az" not in url:
        raise Exception()
    params = dict()
    try:
        link, _, params_str = url.partition('?')
        for param in params_str.split('&'):
            key, value = param.split('=')
            params[key] = value
    except ValueError:
        link = url
    params['page'] = 1
    while True:
        url = link + '?' + '&'.join([key + '=' + str(value) for key, value in params.items()])
        r = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0"
            }
        )
        soup = bs4.BeautifulSoup(r.text, features="html.parser")
        data = soup.find_all("div", {"class": "items-i"})
        if not data:
            break
        for page in data:
            price = page.find("div", class_="price").text.strip()
            place = page.find("div", class_="location").text.strip()
            link = "https://ru.bina.az" + page.find("a", class_="item_link")['href']
            print(price, '\t', place, '\t', link)
            # pprint(page)
        params['page'] += 1

