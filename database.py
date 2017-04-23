import pandas as pd

class Database():
    types = ['Article', 'Proceeding', 'Abstract', 'BookArticle']
    languages = ['English', 'English*', 'Russian', 'Russian*']

    et_al = 'et al.'
    et_al_ru = 'и др.'

    def __init__(self, file='database.json', journals_file='journals.json', languages='English', types=None,
                 format=None, with_page_prefix=False):
        self.journals_db = pd.read_json(journals_file).set_index('Journal')

        if types is None:
            types = Database.types
        elif not isinstance(types, list):
            types = [types]

        if languages == 'English':
            languages = ['English', 'English*']
        elif languages == 'Russian':
            languages = ['Russian', 'Russian*']
        elif languages == 'RussianEnglish':
            languages = ['English', 'Russian*', 'Russian']
        elif languages == 'All':
            languages = Database.languages

        self.db0 = pd.read_json(file, dtype={'Volume': 'str', 'Number': 'str'})
        self.check()
        self.db0.drop(self.db0[~self.db0['Language'].isin(languages)].index, inplace=True)
        self.db0.drop(self.db0[~self.db0['Type'].isin(types)].index, inplace=True)
        self.db0.sort_values(by='Date', inplace=True)
        self.db0 = self.db0.reset_index(drop=True)

        self.format = format
        self.with_page_prefix = with_page_prefix

        self.initials_sep = ' '
        self.one_initial_sep = ' '
        self.many_initials_sep = ' '
        self.pages_sep = '-'
        self.pages_prefix_ru = 'стр. '
        self.pages_prefix = 'p. '
        self.pages_prefix_mult = 'pp. '

        if format == 'latex':
            self.initials_sep = '\,'
            self.one_initial_sep = '~'
            self.pages_sep = '--'
            self.pages_prefix_ru = 'стр.~'
            self.pages_prefix = 'p.~'
            self.pages_prefix_mult = 'pp.~'
        elif format == 'unicode':
            self.pages_sep = '–'

        self.db = self.db0.copy()
        self.format_db()

    def check(self):
        for _, el in self.db0.iterrows():
            if el['Type'] not in Database.types:
                raise Exception("The type [%s] of entry [%s] is invalid" % (el['Type'], el['Title']))
            if el['Language'] not in Database.languages:
                raise Exception("The language [%s] of entry [%s] is invalid" % (el['Language'], el['Title']))
            if not pd.isnull(el['Journal']) and el['Journal'] not in self.journals_db.index:
                raise Exception("Journal [%s] is absent in journals" % (el['Journal']))
            for s in el:
                if isinstance(s, str) and s.strip() != s:
                    print('Extra whitespace in %s' % s)

    def format_db(self):
        self.db['Journal Short'] = self.db0['Journal'].map(lambda x:
                                                           self.journals_db['Short'][x] if pd.notnull(x) else None)
        self.impact_factor()
        self.db['Year'] = self.db0['Date'].dt.year
        self.authors()
        self.pages()
        self.page_numbers()

        if self.format == 'latex':
            self.journal_info(r'\textit{$j} \textbf{$v}, $p ($yy)')
        else:
            self.journal_info(r'$j $v, $p ($yy)')

    def authors(self, max_authors=None, initials_sep=None, initials_in_front=True, one_initial_sep=None,
                many_initials_sep=None, use_and=False):
        if initials_sep is None:
            initials_sep = self.initials_sep
        if one_initial_sep is None:
            one_initial_sep = self.one_initial_sep
        if many_initials_sep is None:
            many_initials_sep = self.many_initials_sep

        def format_author(s):
            surname, initials = [x.strip() for x in s.split(',')]
            initials = initials.split(' ')
            n = len(initials)
            initials = initials_sep.join(initials)
            if initials_in_front:
                a = (initials, surname)
            else:
                a = (surname, initials)
            if n > 1:
                return many_initials_sep.join(a)
            else:
                return one_initial_sep.join(a)

        def format_authors(s, language=None):
            is_en = language.startswith('English')

            authors = [format_author(x.strip()) for x in s.split(';')]
            use_et_al = False
            if max_authors is not None and len(authors) > max_authors + 1:
                authors = authors[:max_authors]
                use_et_al = True

            if use_et_al:
                return ', '.join(authors) + ' ' + (self.et_al if is_en else self.et_al_ru)
            else:
                if use_and:
                    and_str = ' and ' if is_en else ' и '
                    and_str_alt = ', and ' if is_en else ' и '
                    if len(authors) == 2:
                        return and_str.join(authors)
                    elif len(authors) > 2:
                        return ', '.join(authors[:-1]) + and_str_alt + authors[-1]
                    else:
                        return authors[0]
                else:
                    return ', '.join(authors)

        self.db['Authors'] = self.db0.apply(lambda row: format_authors(row['Authors'], row['Language']), axis=1)

    def journal_info(self, s: str, skip_none=True):
        replacement_dict = {'$J': 'Journal',
                            '$j': 'Journal Short',
                            '$v': 'Volume',
                            '$n': 'Number',
                            '$p': 'Pages',
                            '$yy': 'Year'}
        self.db['Info'] = self.get(s, skip_none, replacement_dict)

    def impact_factor(self, s: str=None):
        def calc_if(journal):
            if pd.isnull(journal) or journal not in self.journals_db.index:
                return None

            el = self.journals_db.loc[journal]

            if s is not None:
                return el[s]
            index = sorted([x for x in el.dropna().index if x.startswith('IF')])

            if len(index) > 0:
                return el[index[-1]]
            else:
                return None

        self.db['IF'] = self.db['Journal'].map(calc_if)

    def pages(self, sep=None, use_prefix=None):
        if sep is None:
            sep = self.pages_sep
        if use_prefix is None:
            use_prefix = self.with_page_prefix

        def transform_page(s, language):
            is_en = language.startswith("English")

            if pd.isnull(s):
                return None

            arr = s.split('-')
            if len(arr) == 2:
                prefix = ''
                if arr[0] == arr[1]:
                    if use_prefix:
                        prefix = self.pages_prefix if is_en else self.pages_prefix_ru
                    return prefix + arr[0]
                else:
                    if use_prefix:
                        prefix = self.pages_prefix_mult if is_en else self.pages_prefix_ru
                    return prefix + sep.join(arr)
            else:
                return s

        self.db['Pages'] = self.db0.apply(lambda row: transform_page(row['Pages'], row['Language']), axis=1)

    def page_numbers(self):
        def calc_page_number(s):
            if pd.isnull(s):
                return None

            arr = s.split('-')
            if len(arr) == 2:
                return str(int(arr[1]) - int(arr[0]) + 1)
            else:
                return None

        self.db.loc[self.db['Page Number'].isnull(), 'Page Number'] = self.db0['Pages'].map(calc_page_number)


    def get(self, s, skip_none = True, replacement_dict=None):
        if isinstance(s, dict):
            return pd.DataFrame({k: self.get(v, skip_none=skip_none, replacement_dict=replacement_dict)
                                 for k, v in s.items()})

        if replacement_dict is None:
            replacement_dict = {'$a': 'Authors',
                                '$t': 'Title',
                                '$i': 'Info',
                                '$DOI': 'DOI',
                                '$URL': 'URL',
                                '$IF': 'IF',
                                '$pn': 'Page Number'
                                }

        arr = pd.Series(index=self.db.index)
        for index, el in self.db.iterrows():
            ans = s
            for k, v in replacement_dict.items():
                if k not in ans:
                    continue
                value = el[v]
                if pd.isnull(value):
                    value = ''
                    if skip_none:
                        ans = None
                        break
                ans = ans.replace(k, str(value))
            arr[index] = ans
        return arr

    def print(self, s: str, skip_none = True):
        for line in self.get(s, skip_none):
            print(line)
