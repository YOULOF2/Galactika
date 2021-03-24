import pdfkit
from jinja2 import Environment, FileSystemLoader
from PyPDF2 import PdfFileMerger, PdfFileReader
import os
import requests
from random import choice
import json
# to save the results


class NewsLetterMaker:
    def __init__(self):
        self.path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
        self.config = pdfkit.configuration(wkhtmltopdf=self.path_wkhtmltopdf)
        self.env = Environment(loader=FileSystemLoader('templates/newsletter'))
        self.merger = PdfFileMerger()
        self.issue_location = "static/newsletter/pdfs/final_issue.pdf"
        self.issue_pages = ["static/newsletter/pdfs/cover_page.pdf", "page1.pdf", "page2.pdf", "page3.pdf", "page4.pdf"]

        trivia_questions = requests.get(url="https://opentdb.com/api.php?amount=5&type=boolean").json()["results"]
        with open("quotes.json") as file:
            file_data = json.load(file)["quotes"]
        self.random_quotes = []
        for i in range(6):
            random_quote = choice(file_data)
            self.random_quotes.append(random_quote)

        self.all_data = {
            "trivia": trivia_questions,
            "quotes": self.random_quotes
        }

    def make_magic(self):

        """
        This method takes the relevantint information in and automaticaly produces a pdf.
        According to self.issue_pages list, the pages are made.
        The output location can be changed by changing the self.issue_location string value.
        """
        options = {
            "page-size": "a4",
            "margin-top": "0in",
            "margin-bottom": "0in",
            "margin-right": "0in",
            "margin-left": "0in",
        }
        css_files = [
            "static/galactic blog/vendor/bootstrap/css/bootstrap.min.css",
            "static/galactic blog/css/darkmode.css",
            "static/galactic blog/css/clean-blog.min.css"
        ]

        for i in range(1, len(self.issue_pages)):
            template = self.env.get_template(f'page{i}.html')
            output_from_parsed_template = template.render(all_data=self.all_data)
            pdfkit.from_string(output_from_parsed_template, f"page{i}.pdf", configuration=self.config, options=options,
                               css=css_files)
        for file in self.issue_pages:
            self.merger.append(PdfFileReader(open(file, 'rb')), import_bookmarks=False)
        self.merger.write(self.issue_location)
        for file in self.issue_pages[1:]:
            os.remove(file)

    def delete_magic(self):
        """
        This function delets the pdf file made.
        """
        os.remove(self.issue_location)
