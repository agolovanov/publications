import pandas as pd
import sys

import database as pdb

db = pdb.Database(languages=sys.argv[1], types='Article', format='latex', with_page_prefix=True)
#db.et_al = 'et al'
#db.et_al_ru = 'и др'
#db.authors(max_authors=3)



for i,l in enumerate(db.get('$a, $i')):
    print(r'\cvitem{%d.}{%s.}' % (i + 1, l))
