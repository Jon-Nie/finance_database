import requests
from bs4 import BeautifulSoup
from finance_database import Database
import re
from finance_database.utils import headers

db = Database()
con = db.connection
cur = db.cursor

countries = {}
country_url = "https://en.wikipedia.org/wiki/List_of_circulating_currencies"
html = requests.get(url=country_url, headers=headers).text
soup = BeautifulSoup(html, "lxml")
table = soup.find("table")
for row in table.find_all("tr")[1:]:
    cells = row.find_all("td")
    if len(cells) == 6:
        country_name = cells[0].find("a").get("title")
        country_name = "Ireland" if country_name == "Republic of Ireland" else country_name
        flag_url = "https:" + cells[0].find("img").get("src")
        flag_url_50 = re.sub("[0-9]+px", "50px", flag_url)
        flag_url_100 = re.sub("[0-9]+px", "100px", flag_url)
        flag_url_200 = re.sub("[0-9]+px", "200px", flag_url)
        flag_bytes_50 = requests.get(url=flag_url_50, headers=headers).content
        flag_bytes_100 = requests.get(url=flag_url_100, headers=headers).content
        flag_bytes_200 = requests.get(url=flag_url_200, headers=headers).content
        i = 1
    else:
        i = 0
    currency_name = cells[i].text.split("[")[0].strip()
    currency_name = cells[i].find("a")
    if currency_name is None:
        continue
    currency_name = currency_name.get("title")
    currency_abbr = cells[i+2].text.split("[")[0].strip()
    currency_abbr = None if currency_abbr == "(none)" else currency_abbr

    cur.execute(
        """
        INSERT OR IGNORE INTO currencies (name, abbr)
        VALUES (?, ?)
        """,
        (currency_name, currency_abbr)
    )

    currency_id = cur.execute("SELECT id FROM currencies WHERE name = ?", (currency_name,)).fetchone()[0]

    cur.execute(
        """
        INSERT OR IGNORE INTO countries (name, flag_small, flag_medium, flag_large)
        VALUES (?, ?, ?, ?)
        """,
        (country_name, flag_bytes_50, flag_bytes_100, flag_bytes_200)
    )
    print(country_name)
    country_id = cur.execute("SELECT id FROM countries WHERE name = ?", (country_name,)).fetchone()[0]

    cur.execute(
        """
        INSERT OR IGNORE INTO country_currency_match (country_id, currency_id)
        VALUES (?, ?)
        """,
        (country_id, currency_id)
    )

cur.execute(
    """
    INSERT OR IGNORE INTO countries (name)
    VALUES (?)
    """,
    ("Europe",)
)

europe_id = cur.execute("SELECT id FROM countries WHERE name = ?", ("Europe",)).fetchone()[0]
eur_id = cur.execute("SELECT id FROM currencies WHERE name = ?", ("Euro",)).fetchone()[0]
cur.execute("INSERT OR IGNORE INTO country_currency_match VALUES (?, ?)", (europe_id, eur_id))

cur.execute(
    """
    INSERT OR IGNORE INTO countries (name)
    VALUES (?)
    """,
    (None,)
)

cur.execute(
    """
    INSERT OR IGNORE INTO countries (name)
    VALUES (?)
    """,
    ("Global",)
)

con.commit()

exchange_url = "https://help.yahoo.com/kb/exchanges-data-providers-yahoo-finance-sln2310.html"
html = requests.get(url=exchange_url, headers=headers).text
soup = BeautifulSoup(html, "lxml")
table = soup.find("table")

for row in table.find_all("tr")[1:]:
    cells = row.find_all("td")
    country_name = cells[0].text.strip()
    if country_name == "United States of America":
        country_name = "United States"
    exchange_name = cells[1].text.replace("*", "").strip()
    suffix = cells[2].text.strip()
    suffix = "" if suffix == "N/A" else suffix

    country_id = cur.execute("SELECT id FROM countries WHERE name = ?", (country_name,)).fetchone()[0]
    cur.execute(
        """
        INSERT OR IGNORE INTO exchanges (name, country_id, yahoo_suffix)
        VALUES (?, ?, ?)
        """,
        (exchange_name, country_id, suffix)
    )

con.commit()
con.close()