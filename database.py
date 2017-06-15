import pandas as _pd


class Database:
    TYPES = ['Article', 'Proceeding', 'Abstract', 'BookArticle', 'Preprint', 'Patent']
    LANGUAGES = ['English', 'English*', 'Russian', 'Russian*']

    et_al = 'et al.'
    et_al_ru = 'и др.'
    initials_sep = ' '
    one_initial_sep = ' '
    many_initials_sep = ' '
    pages_sep = '-'
    pages_prefix_ru = 'стр. '
    pages_prefix = 'p. '
    pages_prefix_mult = 'pp. '
    proceedings_prefix = 'Proceedings of'
    proceedings_prefix_ru = 'Материалы'
    lquote = '"'
    rquote = '"'
    lquote_ru = '"'
    rquote_ru = '"'

    def __init__(self, file='database.json', journals_file='journals.json', languages='English', types=None,
                 format=None, with_page_prefix=False):
        self.journals_db = _pd.read_json(journals_file).set_index('Journal')

        if types is None:
            types = Database.TYPES
        elif not isinstance(types, list):
            types = [types]
            for t in types:
                if t not in Database.TYPES:
                    raise ValueError(f'Type [{t}] is not available, possible types are: {", ".join(Database.TYPES)}')

        if languages == 'English':
            languages = ['English', 'English*']
        elif languages == 'Russian':
            languages = ['Russian', 'Russian*']
        elif languages == 'RussianEnglish':
            languages = ['English', 'Russian*', 'Russian']
        elif languages == 'All':
            languages = Database.LANGUAGES

        self.db0 = _pd.read_json(file, dtype={'Volume': 'str', 'Number': 'str'})
        self.check()
        self.db0.drop(self.db0[~self.db0['Language'].isin(languages)].index, inplace=True)
        self.db0.drop(self.db0[~self.db0['Type'].isin(types)].index, inplace=True)
        self.db0.sort_values(by='Date', inplace=True)
        self.db0 = self.db0.reset_index(drop=True)

        self.format = format
        self.with_page_prefix = with_page_prefix

        if format == 'latex':
            self.initials_sep = '\,'
            self.one_initial_sep = '~'
            self.pages_sep = '--'
            self.pages_prefix_ru = 'стр.~'
            self.pages_prefix = 'p.~'
            self.pages_prefix_mult = 'pp.~'
            self.lquote = "``"
            self.rquote = "''"
            self.lquote_ru = "<<"
            self.rquote_ru = ">>"
        elif format == 'html':
            self.initials_sep = '&nbsp;'
            self.one_initial_sep = '&nbsp;'
            self.pages_sep = '&ndash;'
            self.pages_prefix_ru = 'стр.&nbsp;'
            self.pages_prefix = 'p.&nbsp;'
            self.pages_prefix_mult = 'pp.&nbsp;'
            self.lquote = "&ldquo;"
            self.rquote = "&rdquo;"
            self.lquote_ru = "&laquo;"
            self.rquote_ru = "&raquo;"
        elif format == 'unicode':
            self.pages_sep = '–'
            self.lquote = "“"
            self.rquote = "”"
            self.lquote_ru = "«"
            self.rquote_ru = "»"

        self.db = self.db0.copy()
        self.format_db()

    def check(self):
        for _, el in self.db0.iterrows():
            if el['Type'] not in Database.TYPES:
                raise Exception("The type [%s] of entry [%s] is invalid" % (el['Type'], el['Title']))
            if el['Language'] not in Database.LANGUAGES:
                raise Exception("The language [%s] of entry [%s] is invalid" % (el['Language'], el['Title']))
            if not _pd.isnull(el['Journal']) and el['Journal'] not in self.journals_db.index:
                raise Exception("Journal [%s] is absent in journals" % (el['Journal']))
            for s in el:
                if isinstance(s, str) and s.strip() != s:
                    print('Extra whitespace in %s' % s)

    def format_db(self):
        self.db['Journal Short'] = self.db0['Journal'].map(lambda x:
                                                           self.journals_db['Short'][x] if _pd.notnull(x) else None)
        self.impact_factor()
        self.db['Year'] = self.db0['Date'].dt.year
        self.authors()
        self.pages()
        self.page_numbers()
        self.conference_materials()

        if self.format == 'latex':
            self.conference_info(r'\textit{$C}, $l ($yy)')
        elif self.format == 'html':
            self.conference_info(r'<i>$C</i>, $l ($yy)')
        else:
            self.conference_info(r'$C, $l ($yy)')

        if self.format == 'latex':
            self.conference_info(r'\textit{$C}, $p, $l ($yy)')
        elif self.format == 'html':
            self.conference_info(r'<i>$C</i>, $p, $l ($yy)')
        else:
            self.conference_info(r'$C, $p, $l ($yy)')

        if self.format == 'latex':
            self.journal_info(r'\textit{$j} \textbf{$v}, $p ($yy)')
        elif self.format == 'html':
            self.journal_info(r'<i>$j</i> <b>$v</b>, $p ($yy)')
        else:
            self.journal_info(r'$j $v, $p ($yy)')

    def authors(self, max_authors=None, initials_sep=None, initials_in_front=True, one_initial_sep=None,
                many_initials_sep=None, use_and=False):
        if len(self.db) == 0:
            return

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
        tmp = self.get(s, skip_none, replacement_dict)
        self.db.loc[tmp.notnull(), 'Info'] = tmp

    def conference_info(self, s: str, skip_none=True):
        """
        Formats the conference proceedings/abstract information into the `Info` column using the template.
        
        :param s: 
         Allowed options are:
         $C --- conference materials name
         $p --- pages in the materials
         $l --- location of the conference
         $yy --- year of the conference
        :param skip_none: 
         Doesn't replace the information of the conferences which cannot be correctly formatted.
        """
        replacement_dict = {'$C': 'Conference Materials',
                            '$l': 'Location',
                            '$p': 'Pages',
                            '$yy': 'Year'}
        tmp = self.get(s, skip_none, replacement_dict)
        self.db.loc[tmp.notnull(), 'Info'] = tmp

    def conference_materials(self, use_prefix=True, long_name=True):
        """
        Formats conference materials into a `Conference Materials` column.
        :param use_prefix: where to use a prefix like "Proceedings of ..."
        :param long_name: whether to use long or short names of the conference
        """
        if len(self.db) == 0:
            self.db['Conference Materials'] = None
            return

        def format_materials(row):
            is_en = row['Language'].startswith('English')
            lquote = self.lquote if is_en else self.lquote_ru
            rquote = self.rquote if is_en else self.rquote_ru
            prefix = self.proceedings_prefix if is_en else self.proceedings_prefix_ru
            long = row['Conference']
            short = row['Conference Short']
            title = row['Conference Title']
            if _pd.notnull(title):
                if _pd.notnull(long):
                    full_long = title + ' ' + lquote + long + rquote
                else:
                    full_long = title
            elif _pd.notnull(long):
                full_long = long
            else:
                full_long = None

            if long_name:
                name = full_long if _pd.notnull(full_long) else short
            else:
                name = short if _pd.notnull(short) else full_long

            if use_prefix and _pd.notnull(name):
                name = prefix + ' ' + name
            return name

        self.db['Conference Materials'] = self.db.apply(format_materials, axis=1)

    def impact_factor(self, s: str=None):
        def calc_if(journal):
            if _pd.isnull(journal) or journal not in self.journals_db.index:
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
        if len(self.db) == 0:
            self.db['Pages'] = None
            return

        if sep is None:
            sep = self.pages_sep
        if use_prefix is None:
            use_prefix = self.with_page_prefix

        def transform_page(s, language):
            is_en = language.startswith("English")

            if _pd.isnull(s):
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
            if _pd.isnull(s):
                return None

            arr = s.split('-')
            if len(arr) == 2:
                return str(int(arr[1]) - int(arr[0]) + 1)
            else:
                return None

        self.db.loc[self.db['Page Number'].isnull(), 'Page Number'] = self.db0['Pages'].map(calc_page_number)

    def get(self, s, skip_none=True, replacement_dict=None):
        if isinstance(s, dict):
            return _pd.DataFrame({k: self.get(v, skip_none=skip_none, replacement_dict=replacement_dict)
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

        arr = _pd.Series(index=self.db.index)
        for index, el in self.db.iterrows():
            ans = s
            for k, v in replacement_dict.items():
                if k not in ans:
                    continue
                value = el[v]
                if _pd.isnull(value):
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

    def filter_years(self, min_year=None, max_year=None):
        if min_year is not None:
            self.db.drop(self.db[self.db['Year'] < min_year].index, inplace=True)
        if max_year is not None:
            self.db.drop(self.db[self.db['Year'] < max_year].index, inplace=True)
        return self

    def __len__(self):
        return len(self.db)