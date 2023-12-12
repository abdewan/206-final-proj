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

def scrapeUrl(url):
    '''
        This function scrapes the passed url and returns an html object
    '''

    htmls = []
    for i in range(5):
        params={'pg' : i}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            htmls.append(response.text)
        else:
            print("Failed to retrieve the web page.")
    return htmls

def setUpDatabase(db_name):
    '''
        given the passed database name, this function established a SQLite connection
        and returns the cursor and connection objects
    '''
    path = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(path+'/'+db_name)
    cur = conn.cursor()
    return cur, conn

def findTags(html, tag):
    '''
        Given the passed html text and desired tag, this function creates a BeautifulSoup object 
        and parses the html, returning a list of html matches for the passed tag
    '''
    soup = BeautifulSoup(html, 'html.parser')
    tags = soup.find_all(tag)
    cells = []
    for item in tags:
        value = item.text
        cells.append(value)
    return cells

def tableSetUp(htmls):
    '''
        Given a list of the html matches for the relevant tag, this function iterates over this list
        and extracts each professor's name, job title, and salary, returning a list of tuples with this data
    '''
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

def addToDatabase(cur, conn, top100):
    '''
        Given the cursor, connection, and list of tuples for each professor, this function creates our 'professorPay'
        table and adds professors into the table by 25's    
    '''
    #cur.execute("DROP TABLE IF EXISTS professorPay")
    cur.execute("CREATE TABLE IF NOT EXISTS professorPay (id INTEGER PRIMARY KEY, name TEXT, title TEXT, salary INTEGER, scholar_id TEXT)")
    conn.commit()
    
    #get number of rows
    cur.execute('SELECT COUNT(*) FROM professorPay')
    result = cur.fetchone()
    #check if empty
    if (result[0] > 0):
        cur.execute('SELECT id FROM professorPay')
        results = cur.fetchall()
        curIdx = results[-1][0]
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

def removeDuplicates(top100):
    '''
        this function takes in a list of the top paid professors and returns the same list without duplicates
    '''
    unique = []
    for prof in top100:
        if prof[0] in unique:
            top100.remove(prof)
        else:
            unique.append(prof[0])
    return top100

def saveAuthorIDs(top100):
    '''
        this function iterates througfh each professor in the passed list, extracts each name in a FirstName LastName format,
        and performs a google scholar query using the scholarly package, returning a new list with the same information as the 
        passed list, but with each professor's scholar_id in addition. it skips over all the professors for which a search was unsuccessful.
    '''
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

    print('removed', counter)
    return authorIDs
    
def saveCitations(cur):
    '''
        For each professor in the table, this function creates a google search query using the Serpapi google scholar API to access
        each professor's author profile and saving the json data for each professor to citations.json
    '''
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
        i+=1
        citations.append(results)

    with open('citations.json', 'a') as json_file:
        json.dump(citations, json_file)

def createCitationTable(cur, conn, filename):
    '''
        Parses through the passed .json file (in this case, citations.json) to access each professor's number of citations,
        h-index, and list of interests (if applicable). It then creates a citations table in our database and adds all the relevant
        information into it
    '''
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

def processData(cur):
    '''
        This function processes our data in a few different ways. It finds the 5 most common words in the interests section of the google scholar
        profiles. It also finds the professor with the most citations and highest h-index. It writes all of this information to a results.txt file
    '''
    counter = {}
    cur.execute('SELECT interests FROM citations WHERE interests != ?', ('N/A, N/A, N/A',))
    rows = cur.fetchall()
    for prof in rows:
        words = prof[0].split(' ')
        for word in words:
            #make all words lowercase
            word = word.lower()
            #getting rid of the comma
            if ',' in word:
                word = word[:-1]
            counter[word] = counter.get(word, 0) + 1
    counter = sorted(counter.items(), key=lambda x:x[1], reverse=True)

    with open('/Users/akashdewan/Downloads/SI-206/final-proj/206-final-proj/results.txt', 'w') as out_file:

        out_file.write('The most common words in the interests section are:\n')
        #skipping index 0 because it was 'and'
        out_file.write(f'1) {counter[1]}\n')
        out_file.write(f'2) {counter[2]}\n')
        out_file.write(f'3) {counter[3]}\n')
        out_file.write(f'4) {counter[4]}\n')
        out_file.write(f'5) {counter[5]}\n')

        #now find the professor with the most citations
        cur.execute('SELECT professorPay.name, MAX(citations.citations) FROM citations JOIN professorPay ON professorPay.id = citations.id')
        result = cur.fetchone()
        out_file.write(f'The most cited professor is {result[0]} with {result[1]} citations.\n')
        #find professor with highest h-index
        cur.execute('SELECT professorPay.id, professorPay.salary, professorPay.name, MAX(citations.h_index) FROM citations JOIN professorPay ON professorPay.id = citations.id')
        result = cur.fetchone()
        out_file.write(f'The professor with the highest h-index is {result[2]} with a h_index of {result[3]}.\n')
        out_file.write(f'Stephen Forrest makes an annual salary of {result[1]} which is rank {result[0]} out of our database of highly paid professors.\n')
    
        
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

    #commenting out so we don't keep running the api 
    #saveCitations(cur)
    #createCitationTable(cur, conn, 'citations.json')
    
    processData(cur)



if __name__ == "__main__":
    main()