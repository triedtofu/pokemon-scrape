import requests
from bs4 import BeautifulSoup
from pony import orm
from datetime import datetime

db = orm.Database()
db.bind(provider='sqlite', filename='targetPokemon.db', create_db=True)

class Product(db.Entity):
  name = orm.Required(str)
  link = orm.Required(str)
  price = orm.Required(str)
  created_date = orm.Required(datetime)

db.generate_mapping(create_tables=True)

def target(session):
  url = "https://www.target.com.au/c/gifts/gift-ideas-for-kids/toys/puzzles-board-games/W1583234?brand=Pokemon&page=1&sortBy=relevance&sortOrder=descending"
  resp = session.get(url)
  soup = BeautifulSoup(resp.text, "html.parser")

  all_divs = soup.find_all('div', class_='css-1hety4e')
  all_name = []
  all_href = []
  all_price = []

  for div_tag in all_divs:
    for links in div_tag.find_all('a'):
      if links:
        href_value = links['href']
        all_href.append(href_value)
        p_tag = links.find('p')
        if p_tag:
            p_text = p_tag.get_text()
            all_name.append(p_text)

    textBox = div_tag.find('div', class_='css-fzqoy4')
    if textBox:
      price_text = textBox.find('p', class_='css-1ndntt5')
      if price_text:
        formatPrice = price_text.get_text()
        all_price.append(formatPrice)
      else:
        discount_text = textBox.find('p', class_='css-stl9iw')
        formatDiscountPrice = discount_text.get_text()
        all_price.append(formatDiscountPrice)
      
  # Extract the text from each product
  product_data = []
  for name, link, price in zip(all_name, all_href, all_price):
      product_data.append(("Target", name, link, price))

  return product_data

def main():
  session = requests.Session()
  session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
  })

  target_table = target(session)

  with orm.db_session:
    # code to create a new database
    # for item in target_table:
    #   Product(name=item[1], link=item[2], price=item[3], created_date=datetime.now())

    # code to compare with existing database

    count = 0
    for id, name, link, price in target_table:
      existing_product = Product.get(link=link)
      if existing_product:
        if existing_product.price != price:
          print(f"Price changed for {name}. Old price: {existing_product.price}, New price: {price}")
          existing_product.price = price
          existing_product.created_date = datetime.now()
          count += 1
      else:
        Product(name=name, link=link, price=price, created_date=datetime.now())
        print("New product has been added: ", name)

    if count == 0:
      print("No Prices have changed")



if __name__ == '__main__':
  main()