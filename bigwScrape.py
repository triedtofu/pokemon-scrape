import requests
import re
from bs4 import BeautifulSoup
from pony import orm
from datetime import datetime
import pprint

db = orm.Database()
db.bind(provider='sqlite', filename='bigwPokemon.db', create_db=True)

class Product(db.Entity):
  name = orm.Required(str)
  link = orm.Required(str)
  price = orm.Required(str)
  created_date = orm.Required(datetime)

db.generate_mapping(create_tables=True)

def bigw(session, url):
  resp = session.get(url)
  soup = BeautifulSoup(resp.text, "html.parser")

  all_divs = soup.find_all('li', class_='ProductGrid_ProductTileWrapper___Agdi')
  all_name = []
  all_href = []
  all_price = []

  for div_tag in all_divs:
    for links in div_tag.findAll('a', class_='ProductTile_tileLink__UPDgb'):
      if links:
        href_value = links['href']
        all_href.append('https://www.bigw.com.au' + href_value)
        p_tag = links.find('p')
        if p_tag:
          p_text = p_tag.get_text()
          all_name.append(p_text)
        
        pricing = links.find('div', class_='PriceSection PriceSection_PriceSection__Vx1_Q')
        hiddenPricing = pricing.find('div', class_='VisuallyHidden_VisuallyHidden__VBD83')
        if hiddenPricing:
          formatPrice = hiddenPricing.get_text()
          all_price.append(formatPrice)
      
  # Extract the text from each product
  product_data = []
  for name, link, price in zip(all_name, all_href, all_price):
      product_data.append(("BigW", name, link, price))

  return product_data

def main():
  session = requests.Session()
  session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
  })

  all_product_data = []

  for page_num in range(1, 5):
    if page_num == 1:
      url = "https://www.bigw.com.au/brands/pokemon?filter%5Bcategory%5D=6815102"
    else:
      url = f"https://www.bigw.com.au/brands/pokemon?page={page_num}&filter%5Bcategory%5D=6815102"

    product_data = bigw(session, url)
    all_product_data.extend(product_data)

  with orm.db_session:

    # code to create a new database
    # for item in all_product_data:
    #   Product(name=item[1], link=item[2], price=item[3], created_date=datetime.now())

    # code to compare with existing database
    count = 0
    for id, name, link, price in all_product_data:
      existing_product = Product.get(link=link)
      if existing_product:
        # if price has changed
        if existing_product.price != price:
          print(f"Price changed for {name}. Old price: {existing_product.price}, New price: {price}")
          existing_product.price = price
          existing_product.created_date = datetime.now()
          count += 1
        # otherwise no change in price for that product
      else:
        Product(name=name, link=link, price=price, created_date=datetime.now())
        print("New product has been added: ", name)

    if count == 0:
      print("No Prices have changed")
      


if __name__ == '__main__':
  main()