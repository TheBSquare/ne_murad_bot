from bs4 import BeautifulSoup

from parser_handler.parser import Parser


with open("test.html", "r", encoding="utf-8") as f:
    data = f.read()

soup = BeautifulSoup(data, "html.parser")

orders = soup.select_one("div.datagrid-content").select_one("table").select("tr")


for order in orders[:4]:
    print(order.get("class"), order.get("data-guid"))

