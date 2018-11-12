import pandas as pd
import sys

import database as pdb

db = pdb.Database(languages=sys.argv[1], types='Article', format='unicode', with_page_prefix=True)
db.et_al = 'et al'
db.et_al_ru = 'и др'
#db.authors(max_authors=3)
table = db.get({'Paper': '$a. $t. $i', 'URL': 'URL: $URL', 'DOI': 'DOI: $DOI', 'IF': 'IF: $IF'})

for _, row in table.iterrows():
    print(row['Paper'])
    url = row['URL']
    if url:
        print(url)
    doi = row['DOI']
    if pd.notnull(doi):
        print(doi)
    if pd.notnull(row['IF']):
        print(row['IF'])
    print()
