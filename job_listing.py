""" classes for job listings as they are found through scrape operations """
from datetime import datetime

class JobListing:
    def __init__(self, _id, _url, _company, _title, _details, _location):
        """ the id is the key that will be used as docx file name, as well as dataframe key """
        self.id = _id
        self.url = _url
        self.company = _company
        self.title = _title
        self.details = _details
        self.location = _location
        self.text = ""      
    
    def append_text_line(self, _text):
        self.text += _text

    def __str__(self):
        returnstring = f'{self.id} \n'
        returnstring += f'{self.title} \n'
        returnstring += f'{self.url} \n'
        returnstring += f'{self.company} \n'
        returnstring += f'{self.location} \n'
        for detail in self.details:
            returnstring += f'{detail[0]} : {detail[1]} \n'
        returnstring += f'{self.text} \n'
        return returnstring

