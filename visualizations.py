from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import pandas as pd
import os
import sqlite3





def load_employees_data(db):
    """
    This function accepts the filename of the database as a parameter, and returns a nested dictionary. Each outer 
    key of the dictionary is the name of each person in the database, and each inner key is a dictionary, where the 
    key:value pairs should be the job title, salary, number of citations, h index for the person.
    """

    conn = sqlite3.connect(db)
    cur = conn.cursor()

    nested_dict = {}

    query = """
            SELECT professorPay.name, professorPay.title, professorPay.salary, citations.citations, citations.h_index
            FROM professorPay 
            INNER JOIN citations ON professorPay.id = citations.id 
            """
    cur.execute(query)

    for row in cur.fetchall():
        nested_dict[row[0]] = {
            'title': row[1],
            'salary': row[2],
            'num_citations': row[3],
            'h_index': row[4]
        }

    conn.close()
    return nested_dict
pass


def highest_paid(dictionary):
    """
    This function accepts a dictionary from the function load_employees_data and creates a viualization.
    The visualization is a histogram with salary range on the x-axis with the number of people with that 
    salary on the y-axis
    """
    salaries = [person['salary'] for person in dictionary.values()]
    
    plt.hist(salaries, bins=10, edgecolor='black')
    plt.xlabel('Salary Range')
    plt.ylabel('Number of Employees')
    plt.title('Histogram of Employee Salaries')

    plt.show()

def highest_paid_vs_citations(dictionary):
    """
    This function accepts a dictionary from the function load_employees_data and creates a viualization.
    The visualization is a scatter plot that shows the number of citations in the x-axis and the person's
    corresponding salary in the y-axis
    """
    citations = [person['num_citations'] for person in dictionary.values()]
    salaries = [person['salary'] for person in dictionary.values()]

    plt.scatter(citations, salaries)

    plt.xlabel('Number of Citations')
    plt.ylabel('Salary')
    plt.title('Salary vs. Number of Citations')

    plt.show()

def highest_paid_vs_h_index(dictionary):
    """
    This function accepts a dictionary from the function load_employees_data and creates a viualization.
    The visualization is a scatter plot that shows the h_index in the x-axis and the person's coressponding
    salary in the y-axis
    """
    h_index = [person['h_index'] for person in dictionary.values()]
    salaries = [person['salary'] for person in dictionary.values()]

    plt.scatter(h_index, salaries)

    plt.xlabel('H-Index')
    plt.ylabel('Salary')
    plt.title('Salary vs. H-Index')

    plt.show()

def professor_vs_interest(db):
    """
    This function accepts the filename of the database as a parameter and creates a string of words 
    from the interest column of the citations table. Then, use wordcloud and matplot to create a
    word map coresponding to the frequency of the words used.
    """
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('SELECT interests FROM citations WHERE interests != ?', ('N/A, N/A, N/A',))



    comment_words = ''

    rows = cur.fetchall()
    for prof in rows:
        words = prof[0].split(' ')
        for word in words:
            #make all words lowercase
            word = word.lower()
            #getting rid of the comma
            if ',' in word:
                word = word[:-1]
            comment_words += word + ' '

    wordcloud = WordCloud(width = 800, height = 800,
                background_color ='white',
                min_font_size = 10).generate(comment_words)

    plt.figure(figsize = (8, 8), facecolor = None)
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.tight_layout(pad = 0)
 
    plt.show()


def main():

    file = 'professors.db'
    source_dir = os.path.dirname(__file__)
    full_path = os.path.join(source_dir, file)

    data = load_employees_data(full_path)
    highest_paid(data)
    highest_paid_vs_citations(data)
    highest_paid_vs_h_index(data)
    professor_vs_interest(full_path)


if __name__ == "__main__":
    main()