from requests import get, HTTPError
from bs4 import BeautifulSoup
from re import compile, sub
from datetime import datetime
from urllib import request, error
from os.path import expanduser
import argparse
from multiprocessing.pool import Pool, ThreadPool

file_host = 'http://files.smashingmagazine.com/'
web_host = 'https://www.smashingmagazine.com/'

# Usage ./venv/bin/python3 wallpaper_downloader.py -y 2018 -m 9 -ext jpg -res 320x480


def get_page_with_articles(page=None):
    url = web_host + 'category/wallpapers'
    if page and page > 1:
        url += '/page/{}'.format(page)
    try:
        all_html = get(url).text
    except (ConnectionError, TimeoutError) as e:
        print(e)
        return None
    except HTTPError as e:
        print(e)
        return None
    soup = BeautifulSoup(all_html, 'html.parser')
    return soup


def get_pages_count(soup):
    count = 0
    match = soup.findAll("span")
    for m in match:
        if 'more articles' in str(m):
            try:
                count = int(clean_raw(str(m)).split(' ')[0])
            except ValueError:
                return None
    if count > 0:
        count = count // 10 + (1 if count % 10 > 0 else 0)
    return count


def get_image_list_from_article(url, resolution, extension):
    image_list = []

    try:
        all_html = get(web_host + url).text
    except (ConnectionError, TimeoutError) as e:
        print(e)
        return None
    except HTTPError as e:
        print(e)
        return None

    soup = BeautifulSoup(all_html, 'html.parser')
    match = soup.findAll("a")
    for m in match:
        if file_host in str(m.get("href")) and '{}.{}'.format(resolution, extension) in str(m.get("href")):
            image_list.append(str(m.get("href")))

    return image_list


def clean_raw(raw_html):
    return str(sub(compile('<.*?>'), '', raw_html))


def get_articles_of_provided_date(soup, year, month):
    articles = []
    match = soup.findAll("article")
    for m in match:
        date = clean_raw(str(m.find('time'))).split('—')[0]
        date = datetime.strptime(date, '%B %d, %Y ')
        if date.year == year and date.month == month:
            title = m.find('h1', {'class': 'article--post__title'})
            # for featured articles
            if not title:
                title = m.find('h2', {'class': 'tilted-featured-article__title'})
            link = title.find('a', href=True)
            if '/{}/{:02d}'.format(year, date.month) in str(link.get("href")):
                articles.append(str(link.get("href")))
    return articles


def download_images(image):
    try:
        request.urlretrieve(image, expanduser('~/') + image.split('/')[-1])
    except error.URLError:
        print('errorred: ', image)
        return None
    return image


def find_and_download(args):
    # after we found articles watch next page then return
    next_return = 0
    pages = get_pages_count(get_page_with_articles())
    results = ThreadPool(10).imap_unordered(get_page_with_articles, range(1, pages + 1))
    for r in results:
        article_list = get_articles_of_provided_date(r, args['year'], args['month'])
        for article in article_list:
            next_return = 1
            image_list = get_image_list_from_article(article, args['resolution'], args['extension'])
            if len(image_list) > 0:
                result = Pool(10).imap_unordered(download_images, image_list)
                for r in result:
                    print(r if r else '')
        if next_return and not article_list:
            return


def run():
    parser = argparse.ArgumentParser(description="Hello. Let's get some wallpapers")
    parser.add_argument("-y", "--year", type=int, required=True, help="Year of posting wallpapers (2010-2018)")
    parser.add_argument("-m", "--month", type=int, required=True, help="Month of posting wallpapers (1-12)")
    parser.add_argument("-ext", "--extension", required=True, help="Extension of wallpapers (png, jpg)")
    parser.add_argument("-res", "--resolution", required=True, help="Resolution of wallpapers (000x000)")
    args = vars(parser.parse_args())

    if args['year'] > 2018 or args['year'] < 2010:
        print('Year of posting wallpapers should be between 2010 and 2018')
        return
    if args['month'] > 12 or args['month'] < 1:
        print('Month of posting wallpapers should be between 1 and 12')
        return

    find_and_download(args)


if __name__ == '__main__':
    run()
