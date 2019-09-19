import pandas as pd
import sys

import database as pdb

db = pdb.Database(languages='RussianEnglish', types=sys.argv[1], format='latex', with_page_prefix=True)

for l in db.get('$a. $t. $i.'):
    print(r'\item{%s}' % l)
