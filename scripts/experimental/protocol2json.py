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
            data[k] = [_ for _ in v if _]
        else:
            data[k] = v

    return json.dumps(data, indent=4, sort_keys=True)

def main():
    for f in sys.argv[1:]:
        # try:
        data = parse(f)
        # print data
        # print data
        out = open(f + '.json', 'wb')
        out.write(data)
        # except Exception, e:
        #     print e

if __name__ == "__main__":
    main()
