from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import sqlite3
import ssl
import re

site_map_list = ['https://deliveroo.fr/fr/sitemap'];

#Ignore SSL Certification Errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

conn = sqlite3.connect('restaurantsdb.sqlite')
cur = conn.cursor()

# Create Pays, Ville, Restaurant tables
cur.executescript('''
DROP TABLE IF EXISTS Country;
DROP TABLE IF EXISTS City;
DROP TABLE IF EXISTS Restaurant;


CREATE TABLE Country (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name    TEXT UNIQUE

);

CREATE TABLE City (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    country_id INTERGER,
    name    TEXT UNIQUE
);

CREATE TABLE Restaurant (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    city_id  INTEGER,
    name  TEXT UNIQUE,
    rating INTEGER
);

''')

for countries in site_map_list:
    req = Request(countries, headers={'User-Agent': 'Mozilla/5.0'})
    webpage = urlopen(req).read()

    soup = BeautifulSoup(webpage, 'html.parser')

    country = soup.h2.string

    #TO-DO, Function to dynamically change URL depending on country

    #Insert value into Country table
    cur.execute('''INSERT OR IGNORE INTO Country (name) VALUES ( ? )''', ( country, ) )
    cur.execute('SELECT id FROM Country WHERE name = ? ', (country, ))
    country_id = cur.fetchone()[0]

    for city in soup.find_all("h3", class_="mbottom30"):
        #Insert value into City table
        cur.execute('''INSERT OR IGNORE INTO City (name, country_id) VALUES ( ?, ? )''', ( city.string, country_id) )


        for link in soup.find_all('a',href=re.compile("/fr/restaurants"))[:1]:
            restaurants = "https://deliveroo.fr" + link.get('href')


            req = Request(restaurants, headers={'User-Agent': 'Mozilla/5.0'})
            webpage = urlopen(req).read()

            soup = BeautifulSoup(webpage, 'html.parser')

            for names in soup.find_all("p", text=re.compile("^[^0-9]"),class_="ccl-19882374e640f487 ccl-417df52a76832172 ccl-a5fb02a1085896d3 ccl-dd90031787517421 ccl-9d0a5327c911d0f3"):
                name = names.string
                print(name)

                cur.execute('SELECT id FROM City WHERE name = ? ', (city.string, ))
                city_id = cur.fetchone()[0]
                cur.execute('''INSERT OR IGNORE INTO Restaurant (name, city_id)
                    VALUES ( ?, ? )''', ( name, city_id ) )

            counter = 2

            for ratings in soup.find_all("span",text=re.compile("(?=^((?!km).)*$)(?=^((?!livraison).)*$)(?=[0-9]+.[0-9]+\s)"),class_= "ccl-19882374e640f487 ccl-417df52a76832172"):
                rating = str(ratings.string).split(' ')[0]
                cur.execute('UPDATE Restaurant SET rating = ? WHERE id= ? ', (rating, counter) )
                counter += 1




conn.commit()
