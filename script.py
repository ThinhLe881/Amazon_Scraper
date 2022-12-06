import argparse
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import pandas as pd

def getData(url):
    req = Request(url)
    req.add_header('user-agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20')
    client = urlopen(req)
    res = client.read()
    client.close()
    soup = BeautifulSoup(res, "html.parser")
    return soup

def extractInfo(soup):
    deals = []
    products = soup.find_all('div', {'data-component-type': 's-search-result'})
    for item in products:
        title = item.find('a', {'class': 'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'})
        name = title.text.strip()
        link = 'https://www.amazon.ca' + title['href']
        try:
            price = item.find_all('span', {'class': 'a-offscreen'})
            sale_price = float(price[0].text.replace('$','').replace(',','').strip())
            old_price = float(price[1].text.replace('$','').replace(',','').strip())
        except:
            try:
                old_price = float(item.find('span', {'class': 'a-offscreen'}).text.replace('$','').replace(',','').strip())
                sale_price = old_price
            except:
                old_price = -1
                sale_price = -1
        try:
            reviews = item.find('span', {'class': 'a-size-base s-underline-text'}).text.replace(',','').strip('()')
            stars = float(item.find('span', {'class': 'a-icon-alt'}).text.strip()[0:3])
        except:
            reviews = 0
            stars = 0
        deal = {
            'name': name,
            'link': link,
            'sale_price': sale_price,
            'old_price': old_price,
            'reviews': reviews,
            'stars': stars   
            }
        deals.append(deal)
    return deals

def getNextPage(soup):
    try:
        url = 'https://www.amazon.ca' + soup.find('a', {'class': 's-pagination-item s-pagination-next s-pagination-button s-pagination-separator'})['href']
        return url
    except:
        return

def main():
    parser = argparse.ArgumentParser(description='Amazon Scraper')
    parser.add_argument('search_term', metavar='search_term', type=str, help='The item(s) to be searched for. Use + for spaces')
    args = parser.parse_args()

    search_term = args.search_term
    url = f'https://www.amazon.ca/s?k={search_term}'

    print('Scraping products...')
    while True:
        data = getData(url)
        deals = extractInfo(data)
        url = getNextPage(data)
        if not url:
            print('Scraping done.')
            break
    
    df = pd.DataFrame(deals)
    df['percent_off'] = ((df['old_price'] - df['sale_price']) / df['old_price']) * 100
    df['percent_off'] = df['percent_off'].astype(int)
    df = df.sort_values(by=['percent_off'], ascending=False)
    df.to_csv(search_term + '.csv', index=False)
    df = df.drop_duplicates(subset=['name'], keep='first')
    print('Finish.')
    print(df.head())

if __name__ == '__main__':
    main()