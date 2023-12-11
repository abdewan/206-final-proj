import matplotlib.pyplot as plt
import os
import sqlite3
import unittest


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

def professor_vs_interest():
    """
    This function accepts the filename of the database as a parameter and creates a dictionary. Each key
    is the name of the professor and each value is the 5 most common words in the 'interest' section for
    the professors. It then creates a 
    """
    pass


def main():

    file = 'professors.db'
    source_dir = os.path.dirname(__file__)
    full_path = os.path.join(source_dir, file)

    data = load_employees_data(full_path)
    highest_paid(data)
    highest_paid_vs_citations(data)
    



if __name__ == "__main__":
    main()