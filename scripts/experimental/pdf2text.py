#!/usr/bin/python
# pylint: disable=missing-docstring,line-too-long,invalid-name
import sys
import json
from cStringIO import StringIO
from collections import defaultdict
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams


# Usage: python scripts/experimental/protocol2json.py ~/Desktop/Pager\ Dataset/Triage\ Protocols/

def to_const(s):
    return s.strip().strip(';').strip('\n').split('\n')[0].strip('-').strip('?').upper().replace(' ', '_').replace(',', '').replace('-', '_').replace(':', '').replace(';', '').replace('.', '')


STAGES = {
    'initial_questions': set(['Initial Questions']),
    'other_protocols': set(['Other Protocols to Consider']),
    'EMR': set(['Medical History Assesment', 'Assessment', 'Assesment'])
}


def parse(fname): # pylint: disable=too-many-branches
    fp = open(fname, 'rb')
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    # Create a PDF interpreter object.
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    # Process each page contained in the document.

    for page in PDFPage.get_pages(fp):
        interpreter.process_page(page)
        data = retstr.getvalue()

    res = defaultdict(set)
    current_stage = 'title'

    for line in StringIO(data):
        print line,

def main():
    for f in sys.argv[1:]:
        parse(f)

if __name__ == "__main__":
    main()
