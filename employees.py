import unittest
import sqlite3
import json
import os
import re
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
from serpapi import GoogleSearch

params = {
  "engine": "google_scholar_profiles",
  "mauthors": "Mark Schlissel",
  "api_key": "cb4afefcf1639be4471e44507bafaeb29e7035b1ae95037c8f65603ab631ea08"
}

search = GoogleSearch(params)
results = search.get_dict()
print(results)

#scrapes the url and returns the html object
def scrapeUrl(url):
    response = requests.get(url)
    if response.status_code == 200:
        html = response.text
    else:
        print("Failed to retrieve the web page.")
    return html

#creates a database with the passed name
def setUpDatabase(db_name):
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn


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

    return topPaid

#adds the employee data in the top 100 list into the database
def addToDatabase(cur, conn, top100):
    cur.execute("DROP TABLE IF EXISTS employees")
    cur.execute("CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT, title TEXT, salary INTEGER)")
    conn.commit()
    id = 1
    for employee in top100:                                                                                                                                                                                      
        cur.execute('INSERT INTO employees (id, name, department, title, salary) VALUES (?,?,?,?,?)', (id, employee[0], employee[1], employee[2], employee[3]))
        id += 1
    conn.commit()

# def getScholarIDs(top100):
#     allProfiles = []
#     for person in top100:
#         params = {
#             "engine": "google_scholar_profiles",
#             "mauthors": person[1],
#             "api_key": "cb4afefcf1639be4471e44507bafaeb29e7035b1ae95037c8f65603ab631ea08"
#         }

#         search = google_search(params)
#         results = search.get_dict()
#         profiles = results["profiles"]
#         allProfiles.append(profiles)

def createScholarTable(cur, conn, top100):
    pass

    
        
def main():

    html = scrapeUrl('https://www.umsalary.info/numbers.php')

    #need to add the 75 other employees to this list
    additional = ['Luanne Ewald']

    top100 = tableSetUp(html, additional)

    cur, conn = setUpDatabase('employeePay')
    addToDatabase(cur, conn, top100)

    #getScholarIDs(top100)

    # cur2, conn2 = setUpDatabase('googleScholars')
    # createScholarTable(cur2, conn2, top100)
    



if __name__ == "__main__":
    main()