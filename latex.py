import pandas as pd
import sys

import database as pdb

db = pdb.Database(languages=sys.argv[1], types=sys.argv[2], format='latex', with_page_prefix=True)
#db.et_al = 'et al'
#db.et_al_ru = 'и др'
#db.authors(max_authors=3)



for l in db.get('$a, $i'):
    print(r'\item{%s}' % l)
