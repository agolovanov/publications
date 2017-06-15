import database as pdb
import sys

types = ('BookArticle', 'Article', 'Proceeding', 'Abstract', 'Preprint', 'Patent')
codes = ('К', 'С', 'Тр.', 'Т', 'П', 'И')
headlines = ('Статьи в книгах',
             'Статьи в реферируемых журналах',
             'Публикации в трудах конференций',
             'Тезисы и абстракты',
             'Препринты',
             'Патенты на изобретения')

year = int(sys.argv[1])

db = pdb.Database(languages='RussianEnglish', format='html')

print('<meta http-equiv="Content-Type" content="text/html; charset=utf-8">')

print(f'Общее к-во печ. работ: {len(db)}<br>')
print('<br>')

overall = 0

for c, t in zip(codes, types):
    db = pdb.Database(languages='RussianEnglish', types=t, format='html').filter_years(min_year=year, max_year=year)
    count = len(db)
    overall += count
    print(f'{c}: {count}<br>')

print(f'О: {overall}<br>')

for h, t in zip(headlines, types):
    print('<br>')
    print(f'<h3>{h}</h3>')
    items = pdb.Database(languages='RussianEnglish', types=t, format='html', with_page_prefix=True).get('$a. $t. $i.')
    if len(items) == 0:
        print('&mdash;<br>')
    for i in range(len(items)):
        print(f'{i+1}. {items[i]}<br>')