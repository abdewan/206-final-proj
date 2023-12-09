import unittest
import sqlite3
import json
import os
import re
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
import serpapi
from scholarly import scholarly

# query = scholarly.search_author('Duderstadt, Michigan')
# scholarly.pprint(next(query))
#scrapes the url and returns the html object
def scrapeUrl(url):
    htmls = []
    for i in range(5):
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
            name = match.group(2) + ' ' + match.group(1)
            title = cells[i+3]
            #converting salaries into ints
            salary = int(cells[i+4][1:-3].replace(',',''))
            if 'Professor' in title:
                topPaid.append((name, title, salary))

    return topPaid

#adds the employee data in the top 100 list into the database 25 rows at a time.
def addToDatabase(cur, conn, top100):
    #cur.execute("DROP TABLE IF EXISTS professorPay")
    cur.execute("CREATE TABLE IF NOT EXISTS professorPay (id INTEGER PRIMARY KEY, name TEXT, title TEXT, salary INTEGER, scholar_id TEXT)")
    conn.commit()
    
    #get number of rows
    cur.execute('SELECT COUNT(*) FROM professorPay')
    result = cur.fetchone()
    print('num rows:', result[0])
    #check if empty
    if (result[0] > 0):
        cur.execute('SELECT id FROM professorPay')
        results = cur.fetchall()
        curIdx = results[-1][0]
        print('current index:', curIdx)
        for i in range(curIdx, curIdx + 25):
            cur.execute('INSERT INTO professorPay (id, name, title, salary, scholar_id) VALUES (?,?,?,?,?)', (i+1, top100[i][0], top100[i][1], top100[i][2], top100[i][3]))
    else:
        #insert for the first time
        for i in range(0, 25):
            cur.execute('INSERT INTO professorPay (id, name, title, salary, scholar_id) VALUES (?,?,?,?,?)', (i+1, top100[i][0], top100[i][1], top100[i][2], top100[i][3]))
    # id=1
    # for prof in top100:
    #     cur.execute('INSERT INTO professorPay (id, name, title, salary, scholar_id) VALUES (?,?,?,?,?)', (id, prof[0], prof[1], prof[2], prof[3]))
    #     id += 1
    # conn.commit()


#removes duplicates from the list
def removeDuplicates(top100):
    unique = []
    for prof in top100:
        if prof[0] in unique:
            top100.remove(prof)
        else:
            unique.append(prof[0])
    return top100


def saveAuthorIDs(top100):

    authorIDs = []
    counter = 0
    i=1
    for professor in top100:
        name = ''
        temp = professor[0].split(' ')
        if len(temp) > 2:
            if temp[0] == 'Jr':
                name = temp[1] + ' ' + temp[-1]
            else:
                name = temp[0] + ' ' + temp[-1]
        else:
            name = professor[0]
        query = scholarly.search_author(f'{name}, Michigan')
        i+=1
        #scholarly.pprint(query)
        try:
            result = next(query)
            print('appending', name, 'at index', len(authorIDs))
            authorIDs.append((name, professor[1], professor[2], result['scholar_id']))
        except:
            counter += 1
            print('removing', professor)
            
        
        #print(result['scholar_id'])
        #authorIDs.append((name, professor[1], professor[2], 'n/a'))
    print('removed', counter)
    return authorIDs
    


#same process as saveAuthorIDs() but different query, now saving their citations and such
def saveCitations(cur):

    citations = []

    cur.execute('SELECT scholar_id FROM professorPay')
    rows = cur.fetchall()
    i=1
    for prof in rows:
        #can only do 100 rows
        if i > 100:
            break
        id = prof[0]

        params = {
        "engine": "google_scholar_author",
        "author_id": id,
        "api_key": "48aae026c3b879c625d8a4fe9598c472f3c6a357cf8785f839e609c36d4418fd"
        }

        results = serpapi.search(params).as_dict()
        print(i)
        i+=1
        citations.append(results)

    with open('citations.json', 'w') as json_file:
        json.dump(citations, json_file)
#parses through citations.json to extract each author's number of citations, h-index, and interests
def createCitationTable(cur, conn, filename):
    f = open(os.path.abspath(os.path.join(os.path.dirname(__file__), filename)))
    file_data = f.read()
    f.close()
    data = json.loads(file_data)

    citations = []
    for author in data:
        id = author['search_parameters']['author_id']
        numCitations = author['cited_by']['table'][0]['citations']['all']
        h_index = author['cited_by']['table'][1]['h_index']['all']
        try:
            match = author['author']['interests']
            interests = match[0]['title'] + ', ' + match[1]['title'] + ', ' + match[2]['title']
        except:
            interests = 'N/A' + ', ' + 'N/A' + ', ' + 'N/A'

        citations.append((id, numCitations, h_index, interests))

    #cur.execute('DROP TABLE IF EXISTS citations')
    cur.execute('CREATE TABLE IF NOT EXISTS citations (id INTEGER PRIMARY KEY, citations INTEGER, h_index INTEGER, interests TEXT)')
    conn.commit()


    cur.execute('SELECT COUNT(*) FROM citations')
    result = cur.fetchone()
    print('num rows:', result[0])
    #check if empty
    curIdx = result[0]
    if (curIdx > 0):
        for i in range(curIdx, curIdx + 25):
            cur.execute('INSERT INTO citations (id, citations, h_index, interests) VALUES (?,?,?,?)', (i+1, citations[i][1], citations[i][2], citations[i][3]))
    else:
        #insert for the first time
        for i in range(0, 25):
            cur.execute('INSERT INTO citations (id, citations, h_index, interests) VALUES (?,?,?,?)', (i+1, citations[i][1], citations[i][2], citations[i][3]))
    conn.commit()
#finds the 5 most common words in the 'interests' section for the top 100 professors (only including the ones with interests sections)
def findCommonInterests(cur):
    counter = {}
    cur.execute('SELECT interests FROM citations WHERE interests != ?', ('N/A, N/A, N/A',))
    rows = cur.fetchall()
    for prof in rows:
        words = prof[0].split(' ')
        for word in words:
            #getting rid of the comma
            counter[word] = counter.get(word, 0) + 1
    counter = sorted(counter.items(), key=lambda x:x[1], reverse=True)
    print('The most common words in the interests section are:')
    #skipping index 0 because it was 'and'
    print('1)', counter[1])
    print('2)', counter[2])
    print('3)', counter[3])
    print('4)', counter[4])
    print('5)', counter[5])
    
        
def main():

    htmls = scrapeUrl('https://www.openthebooks.com/michigan-state-employees/?Year_S=2022&Emp_S=University%2Bof%2BMichigan%2Bat%2BAnn%2BArbor')

    profs = tableSetUp(htmls)
    profs = removeDuplicates(profs)

    cur, conn = setUpDatabase('professors.db')
    print(len(profs))
    #commenting out because we have our complete database and don't need to keep scraping the url every time, it takes a while
    #top100 = saveAuthorIDs(profs)
    #addToDatabase(cur, conn, top100)

    #authorIDs = scrapeAuthorIDs(url, top100)
    #print(authorIDs)

    #commenting out so we don't keep running the api 
    #saveCitations(cur)
    #createCitationTable(cur, conn, 'citations.json')
    
    findCommonInterests(cur)



if __name__ == "__main__":
    main()