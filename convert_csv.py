import pandas as pd
import re
import os

if __name__ == '__main__':
    db = pd.read_csv('citations.csv', dtype='str')

    def format_author(s):
        surname, initials = [x.strip() for x in s.split(',')]
        initials = [s + '.' for s in re.findall('(Yu|[A-ZА-Я])', initials)]
        return surname + ', ' + ' '.join(initials)

    def format_authors(s: str):
        return '; '.join([format_author(x.strip()) for x in s.split(';')[:-1]])

    db['Authors'] = db['Authors'].map(format_authors)
    db.rename(columns={'Year': 'Date', 'Publication': 'Journal'}, inplace=True)
    db['Pages'] = db['Pages'].map(lambda s: s.replace('–', '-'))
    db.loc[db['Volume'].isnull(), 'Type'] = 'Proceeding'
    db.loc[db['Volume'].isnull(), 'Conference'] = db['Journal']
    db.loc[db['Volume'].isnull(), 'Journal'] = None
    db.loc[db['Volume'].notnull(), 'Type'] = 'Article'
    db = db[['Authors', 'Title', 'Type', 'Journal', 'Conference', 'Volume', 'Number', 'Pages', 'Date', 'Publisher']]

    db.sort_values(by='Date').to_json('citations.json', 'records', force_ascii=False)
    os.system("jq 'del(.[][] | nulls)' citations.json")
    os.system("rm citations.json")