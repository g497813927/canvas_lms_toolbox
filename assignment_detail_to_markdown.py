"""
Author:      Techzjc
Description: this script converts the assignment details obtained from the Canvas LMS API into markdown.
"""
import time
from bs4 import BeautifulSoup
import requests
import json
import markdownify

"""
Configuration Section
"""
# Canvas LMS URL, usually the domain part of the address you use to access Canvas
BASE_URL = ''

# Canvas LMS API access token,
# can obtain by logining to your canvas site and click
# 'Account' -> 'Settings' -> 'New Access Token'
ACCESS_TOKEN = ''


course_payload = {
    'enrollment_state': 'active',
}

assignment_payload = {
    'include[]': 'all_dates',
}

header = {
    'Authorization': 'Bearer ' + ACCESS_TOKEN
}

COURSE_LIST_URL = BASE_URL + '/api/v1/courses'
ASSIGNMENT_URL = COURSE_LIST_URL + '/{}/assignments'

"""
Course Selection Section
"""
response = requests.get(COURSE_LIST_URL, params=course_payload, headers=header)

json.loads(response.text)

print('Available courses:')

for course in json.loads(response.text):
    if "name" in course:
        print(course['id'], '\t-\t', course['name'])
    elif "access_restricted_by_date" in course:
        if course['access_restricted_by_date']:
            print(course['id'], '\t-\t', 'NOT AVAILABLE')
    else:
        print(course['id'], '\t-\t', 'UNKNOWN')

course_id = None
course_name = None
while course_id is None:
    selection = input('Enter course ID: ')
    if selection.isdigit():
        for course in json.loads(response.text):
            if course['id'] == int(selection):
                if "access_restricted_by_date" in course:
                    if course['access_restricted_by_date']:
                        print('Course is not available.')
                        break
                course_id = course['id']
                course_name = course['name']
                break
        if course_id is None:
            print('Course not found or you do not have access to this course.')
            course_id = int(selection)
    else:
        print('Invalid course ID.')

print('You selected: ', course_id, ' - ', course_name)

"""
Assignment Selection Section
"""
ASSIGNMENT_URL = ASSIGNMENT_URL.format(str(course_id))
response = requests.get(ASSIGNMENT_URL, params=assignment_payload, headers=header)
assignments = json.loads(response.text)
# list the assignment id, names and due dates
for assignment in assignments:
    if assignment['due_at'] is not None:
        due_time = time.strptime(
                      assignment['due_at'], "%Y-%m-%dT%H:%M:%SZ"
                  )
        # Set the timezone to the local timezone
        # Check if the timezone is having daylight saving time
        if time.daylight:
            due_time = time.localtime(time.mktime(due_time) - time.altzone)
        else:
            due_time = time.localtime(time.mktime(due_time) - time.timezone)
        print(assignment['id'], '\t-\t', assignment['name'], '\t\t\tDue at:\t',
              time.strftime(
                  "%Y-%m-%d %H:%M:%S",
                  due_time
              ) + ' ' + time.tzname[time.localtime().tm_isdst])
    else:
        print(assignment['id'], '\t-\t', assignment['name'], '\t\t\tDue at:\t', 'NOT AVAILABLE')


assignment_id = None
assignment_name = None
while assignment_id is None:
    selection = input('Enter assignment ID: ')
    if selection.isdigit():
        for assignment in assignments:
            if assignment['id'] == int(selection):
                assignment_id = assignment['id']
                assignment_name = assignment['name']
                break
        if assignment_id is None:
            print('Assignment not found or you do not have access to this assignment.')
            assignment_id = int(selection)
    else:
        print('Invalid assignment ID.')

print('You selected: ', assignment_id, ' - ', assignment_name)

"""
Assignment Details Section
"""
# get the assignment details
for assignment in assignments:
    if assignment['id'] == assignment_id:
        assignment_details = assignment
        break

"""
Assignment Details to Markdown Section
"""
# change the equation image to the latex code
soup = BeautifulSoup(assignment_details['description'], 'html.parser')
add_access_token = False
add_access_token_question_answered = False
for img in soup.find_all('img'):
    # Check if the alt contains the equation
    if 'data-equation-content' in img.attrs:
        # Get the equation
        equation = img['data-equation-content']
        # Remove the new line characters from the equation
        equation = equation.replace('\n', '')
        img['src'] = 'latex equation'
        del img['title']
        img['alt'] = equation  # put the equation to the alt, make sure it can be replaced
    elif img['src'].startswith(BASE_URL):
        # Prompt the user to ask if they want to add the access token to the image to ensure the image can be displayed
        if not add_access_token and not add_access_token_question_answered:
            add_access_token = input('Do you want to add the access token '
                                     'to the image to ensure the image can be displayed? [y/n] '
                                     ).lower()
            if add_access_token == 'y':
                add_access_token = True
                add_access_token_question_answered = True
            else:
                add_access_token = False
                add_access_token_question_answered = True
        if add_access_token:
            if '?' in img['src']:
                img['src'] += '&access_token=' + ACCESS_TOKEN
            else:
                img['src'] += '?access_token=' + ACCESS_TOKEN

# convert the html to markdown
markdown = markdownify.markdownify(str(soup))

# Create an array of the markdown lines
markdown_lines = markdown.splitlines()

# change the equation image to the latex code
for i in range(len(markdown_lines)):
    # Check if the line contains the equation
    if markdown_lines[i].find('(latex equation)') > -1:
        markdown_lines[i] = markdown_lines[i].replace('](latex equation)', '$')
        markdown_lines[i] = markdown_lines[i].replace('![', '$')

# convert the array to a string
result = ''
for line in markdown_lines:
    if line != '' and not line.startswith('---'):
        result += line
    elif line.startswith('---'):
        result += '\n' + line
    else:
        result += '\n'

# Prompt the user to ask if they want to save the markdown file
save_file = input('Do you want to save the markdown file? (y/n): ').lower()
if save_file == 'y':
    # Check if the file exists
    file_save = False  # Flag to check if the user wants to save the file
    try:
        with open(assignment_name + '.md', 'r') as f:
            overwrite_file = input('The file {}.md already exists. Do you want to overwrite the file? (y/n): '
                                   .format(assignment_name)).lower()
            if overwrite_file == 'y':
                file_save = True
    except FileNotFoundError:
        file_save = True

    if file_save:
        file = open(assignment_name + '.md', 'w')
        file.write(result)
        file.close()
        print('The markdown file is saved.')

# Prompt the user to ask if they want to print the markdown
print_markdown = input('Do you want to print the markdown? (y/n): ').lower()
if print_markdown == 'y':
    print(result)
