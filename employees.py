import unittest
import sqlite3
import json
import os
import re
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests

# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options

# options = Options()
# options.headless = True

#scrapes the website using the passed in soup object, returning a list with all instances of the passed tag
def findTags(html, tag):
    soup = BeautifulSoup(html, 'html.parser')
    tags = soup.find_all(tag)
    cells = []
    for item in tags:
        value = item.text
        cells.append(value)
    return cells

#Sets up the table of top 100 highest paid employees and returns a list of tuples
def tableSetUp(html, additional):
    cells = findTags(html, "tr")
    topPaid = []
    #looping through the section of list once the employees start (at index 6), breaking into tuples to append to my list
    for i in range(6, len(cells) - 2):
        values = cells[i].split('\n')
        #converting salaries into ints
        values[4] = int(values[4][2:-3].replace(',', ''))
        #(name, title, department, salary)
        topPaid.append((values[1], values[2], values[3], values[4]))

    url = 'https://www.umsalary.info/index.php?FName=Luanne&LName=Ewald&Year=0'
    #searching for each additional employee in the top 100 on the website and extracting their information to add to our database
    for person in additional:
        name = person.split(' ')
        params = {'FName': name[0], 'LName': name[1], 'Year': 0}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            html2 = response.text
        else:
            print("Failed to retrieve the web page.")

        cells2 = findTags(html2, "td")
        cells2[13] = int(cells2[13][2:-3].replace(',', ''))
        topPaid.append((cells2[10], cells2[11], cells2[12], cells2[13]))
        
def main():
    url = 'https://www.umsalary.info/numbers.php'

    # browser = webdriver.Chrome(options=options)
    response = requests.get(url)

    if response.status_code == 200:
        html = response.text
    else:
        print("Failed to retrieve the web page.")

    #need to add the 75 other employees to this list
    additional = ['Luanne Ewald']

    top100 = tableSetUp(html, additional)
    



if __name__ == "__main__":
    main()