from glob import glob
import sys
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.layout import LAParams
from cStringIO import StringIO
import json
from collections import defaultdict


# Usage: python scripts/experimental/protocol2json.py ~/Desktop/Pager\ Dataset/Triage\ Protocols/

def to_const(s):
    return s.strip().strip(';').strip('\n').split('\n')[0].strip('-').strip('?').upper().replace(' ', '_').replace(',', '').replace('-', '_').replace(':', '').replace(';', '').replace('.', '')


STAGES = {
    'initial_questions': set(['Initial Questions']),
    'other_protocols': set(['Other Protocols to Consider']),
    'EMR': set(['Medical History Assesment', 'Assessment', 'Assesment'])
}


def parse(fname):
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
        for stage, keywords in STAGES.items():
            for keyword in keywords:
                if keyword.lower() in line.lower():
                    current_stage = stage

        if current_stage == 'title':
            res[current_stage] = to_const(line)
            print line
            current_stage = 'representation'
        elif current_stage == 'representation':
            if '-' in line:
                res['representation'].add(to_const(line))
        elif current_stage == 'initial_questions':
            if '-' in line or '?' in line:
                res['initial_questions'].add(to_const(line))
        elif current_stage == 'other_protocols':
            res['other_protocols'].add(to_const(line))
        elif current_stage == 'EMR':
            if ('?' in line or '-' in line) and 'following' not in line:
                res['EMR'].add(to_const(line))

    data = {}
    for (k, v) in res.items():
        if k != 'title':
            data[k] = filter(lambda x: x != "", list(v)) 
        else:
            data[k] = v

    return json.dumps(data, indent=4, sort_keys=True)


for file in list(glob(sys.argv[1] + '*.pdf')):
    # try:
    data = parse(file)
    # print data
    # print data
    out = open(file + '.json', 'wb')
    out.write(data)
    # except Exception, e:
    #     print e
