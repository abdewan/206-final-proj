import unittest
import sqlite3
import json
import os
import re
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
import serpapi



#scrapes the url and returns the html object
def scrapeUrl(url):
    htmls = []
    for i in range(4):
        params={'pg' : i}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            htmls.append(response.text)
        else:
            print("Failed to retrieve the web page.")
    return htmls

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
def tableSetUp(htmls):
    topPaid = []
    for html in htmls:
        cells = findTags(html, "td")
        #looping through the section of list once the employees start (at index 6), breaking into tuples to append to my list
        for i in range(0, len(cells)-6, 6):
            name = cells[i+2]
            #reordering the names to be first middle last 
            match = re.search('(\w+)\s(\D+)', name)
            name = match.group(1) + ' ' + match.group(2)
            title = cells[i+3]
            #converting salaries into ints
            salary = int(cells[i+4][1:-3].replace(',',''))
            if 'Professor' in title:
                topPaid.append((name, title, salary))

    return topPaid

#adds the employee data in the top 100 list into the database
def addToDatabase(cur, conn, top100):
    cur.execute("DROP TABLE IF EXISTS professorPay")
    cur.execute("CREATE TABLE IF NOT EXISTS professorPay (id INTEGER PRIMARY KEY, name TEXT, title TEXT, salary INTEGER)")
    conn.commit()

    id = 1
    for employee in top100:                                                                                                                                                                                
        cur.execute('INSERT INTO professorPay (id, name, title, salary) VALUES (?,?,?,?)', (id, employee[0], employee[1], employee[2]))
        id += 1
    conn.commit()

#we are using this to use each professor's name to access their authorID which can then be used with the profiles API
#because we only get a limited number of searches with this API, we are storing the search results for 100 professors in an authorIDs.json file
#adding the pass keyword to the top of this function now that we have the saved .json file so we don't use up more free searches
def saveAuthorIDs(top100):
    pass

    authorIDs = []
    for professor in top100:
        name = professor[1]

        params = {
        "engine": "google_scholar_profiles",
        "mauthors": name,
        "api_key": "cb4afefcf1639be4471e44507bafaeb29e7035b1ae95037c8f65603ab631ea08"
        }

        results = serpapi.search(params).as_dict()
        authorIDs.append(results)

        with open('authorIDs.json', 'w') as json_file:
            json.dump(authorIDs, json_file)

def createScholarTable(cur, conn, top100):
    pass

    
        
def main():

    htmls = scrapeUrl('https://www.openthebooks.com/michigan-state-employees/?Year_S=2022&Emp_S=University%2Bof%2BMichigan%2Bat%2BAnn%2BArbor')

    top100 = tableSetUp(htmls)
    top100 = top100[:100]

    cur, conn = setUpDatabase('professors.db')
    addToDatabase(cur, conn, top100)

    saveAuthorIDs(top100)

    # cur2, conn2 = setUpDatabase('googleScholars')
    # createScholarTable(cur2, conn2, top100)
    



if __name__ == "__main__":
    main()