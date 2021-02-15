#!/usr/bin/env python3

import os
import sys
import subprocess
import shutil
import re
import pprint as pp
from datetime import date
from datetime import time
from datetime import datetime

# TODO: combined template strings

npr_template_top = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NPR</title>
<link rel="stylesheet" href="main.css" />
</head>
<body>
"""

template_bot = """</body>
</html>"""

def month_num_to_name(month_num):
    if month_num == 1: return 'January'
    if month_num == 2: return 'February'
    if month_num == 3: return 'March'
    if month_num == 4: return 'April'
    if month_num == 5: return 'May'
    if month_num == 6: return 'June'
    if month_num == 7: return 'July'
    if month_num == 8: return 'August'
    if month_num == 9: return 'September'
    if month_num == 10: return 'October'
    if month_num == 11: return 'November'
    if month_num == 12: return 'December'

def month_name_to_num(month):
    month = month.lower()
    if month.startswith('jan'): return 1
    if month.startswith('feb'): return 2
    if month.startswith('mar'): return 3
    if month.startswith('apr'): return 4
    if month.startswith('may'): return 5
    if month.startswith('jun'): return 6
    if month.startswith('jul'): return 7
    if month.startswith('aug'): return 8
    if month.startswith('sep'): return 9
    if month.startswith('oct'): return 10
    if month.startswith('nov'): return 11
    if month.startswith('dec'): return 12

def wget_set(articles, skip_if_exists=True):

    html_files = [f for f in os.listdir() if f.endswith(".html")]

    ps = list()
    for article in articles:
        filename = article['filename']
        if not filename in html_files:
            sys.stderr.write('spawning...\n')
            p = subprocess.Popen(['wget', '-O', filename, article['url']])
            ps.append(p)
        else:
            sys.stderr.write('%s found, not calling wget...\n' % filename)

    for p in ps:
        sys.stderr.write('waiting...\n')
        p.communicate()
        p.wait()

def npr_get_articles(do_wget = True):

    if do_wget:
        subprocess.run(['wget', '-O', 'tmp.html', 'https://text.npr.org/'])

        new_articles = list()

        with open('tmp.html', 'r') as fh:
            lines = fh.readlines()

        for line in lines:
            m = re.search(r'topic-title.*href="/(?P<href>\d+)">(?P<title>[^<]+)<', line)
            if m:
                href = m.groupdict()['href']
                filename = href + '.html'
                url = 'https://text.npr.org/' + href
                title = '' + m.groupdict()['title']
                new_articles.append({'url': url, 'title': title, 'filename': filename})

        wget_set(new_articles)

    html_files = [f for f in os.listdir() if f.endswith(".html")]

    all_articles = list()
    for html_file in html_files:

        if not re.match(r'\d+\.html', html_file):
            sys.stderr.write('skipping %s\n' % html_file)
            continue

        article = dict()
        article['filename'] = html_file
        #article['url'] = 

        with open(article['filename'], 'r') as fh:
            lines = fh.readlines()
            for (idx, line) in enumerate(lines):
                m = re.search(r'"story-title">(?P<title>[^<]+)<', line)
                if m:
                    article['title'] = m.groupdict()['title']
                    date_p = lines[idx+2]
                    m = re.search(r'<p>(?P<date>.*)</p>', date_p)
                    assert(m)
                    date_s = m.groupdict()['date']
                    date_s = re.sub(r'[^a-zA-Z0-9:, ]', '', date_s)
                    m = re.search(r'(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w* (?P<day>\d+), (?P<year>\d+) +(?P<time>\d+:\d+) (?P<am_pm>[AP]M) (?P<zone>.*)', date_s)
                    assert(m)
                    month = m.groupdict()['month']
                    day = int(m.groupdict()['day'])
                    year = int(m.groupdict()['year'])
                    time_s = m.groupdict()['time']
                    hour = int(time_s.split(':')[0])
                    if m.groupdict()['am_pm'] == 'PM' and hour < 12:
                        hour += 12
                    minute = int(time_s.split(':')[1])
                    am_pm = m.groupdict()['am_pm']
                    month_num = month_name_to_num(month)
                    dt = datetime(year, month_num, day, hour, minute)
                    article['date_str'] = '%s %d, %s' % (month, day, year)
                    article['datetime'] = dt
            article['content'] = lines

        all_articles.append(article)

    all_articles = sorted(all_articles, key=lambda item: item['datetime'], reverse=True)

    # make index
    with open('index.html', 'w') as fh:
        fh.write(npr_template_top)
        fh.write('<a href="index.html">NPR</a> | \n')
        fh.write('<a href="../txst/index.html">Texas Standard</a> | \n')
        fh.write('<a href="../tribune/index.html">Texas Tribune</a> | \n')
        fh.write('<a href="../statesman/index.html">Statesman</a>\n')
        in_ul = False
        prev_day = 0
        for article in all_articles:
            day = article['datetime'].day
            diff_day = day != prev_day
            prev_day = day
            if diff_day:
                if in_ul:
                    fh.write('</ul>\n')
                fh.write('<p>%s</p>\n' % article['date_str'])
                fh.write('<ul>\n')
                in_ul = True
            hour = article['datetime'].hour
            am_pm = 'AM' if hour < 12 else 'PM'
            if hour > 12:
                hour -= 12
            minute = article['datetime'].minute
            fh.write('<li>%s:%02d %s: <a href="%s">%s</a></li>\n' % (hour, minute, am_pm, article['filename'], article['title']))
        if in_ul:
            fh.write('</ul>\n')
        fh.write(template_bot)

    return all_articles

def npr_create_article(article, ofh=None):

    template_top_title = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>""" + article['title'] + """</title>
<link rel="stylesheet" href="main.css" />
</head>
<body>
"""

    if ofh:
        all_in_one_file = True
    else:
        all_in_one_file = False
        ofh = open(article['filename'], "w")

    if not all_in_one_file:
        ofh.write(template_top_title)

    on = False
    on_n = False
    need_original_story_link = True

    for line in article['content']:

        line = re.sub(r'href="/([^"]+)"', r'href="https://text.npr.org/\1"', line)

        skip = False
        if re.search(r'Related Story:', line):
            skip = True

        if re.search('>Original Story<', line):
            need_original_story_link = False

        if not on and re.search(r'<article>', line):
            on_n = True
        elif on and re.search(r'</article>', line):
            if need_original_story_link:
                url = 'https://text.npr.org/%s' % (re.sub(r'\.html', '', article['filename']))
                ofh.write('<a href="%s">Original Story</a>\n' % url)
            on_n = False

        if (on or on_n) and not skip:
            ofh.write(line)

        on = on_n

    if not all_in_one_file:
        ofh.write(template_bot)
        ofh.close()

def npr_fetch():

    try:
        os.mkdir('npr')
    except FileExistsError:
        pass
    shutil.copyfile('main.css', './npr/main.css')
    os.chdir('npr')

    articles = npr_get_articles()

    all_in_one_file = False

    if all_in_one_file:
        fh = open("npr_articles.html", "w")
        fh.write(npr_template_top)
    else:
        fh = None

    for article in articles:
        npr_create_article(article, fh)

    if all_in_one_file:
        fh.write(template_bot)
        fh.close()

    if os.path.isfile('tmp.html'):
        os.remove('tmp.html')

    os.chdir('..')

txst_template_bot = """</body>
</html>"""

def txst_get_articles(do_wget = True):

    if do_wget:
        subprocess.run(['wget', '-O', 'tmp.html', 'https://www.texasstandard.org/all-stories/'])

        new_articles = list()

        with open('tmp.html', 'r') as fh:
            lines = fh.readlines()

        for line in lines:
            m = re.search(r'<a href="(?P<href>[^"]+)">(?P<title>.*)</a> *</h4>', line)
            if m:
                href = m.groupdict()['href']
                title = m.groupdict()['title']
                filename = re.sub(r'https://www.texasstandard.org/stories/(.*)/', r'\1', href) + '.html'
                url = href
                new_articles.append({'url': url, 'title': title, 'filename': filename})

        wget_set(new_articles)

    html_files = [f for f in os.listdir() if f.endswith(".html")]

    all_articles = list()
    for html_file in html_files:

        if re.match(r'(index|tmp).html', html_file):
            sys.stderr.write('skipping %s\n' % html_file)
            continue

        article = dict()
        article['filename'] = html_file
        #article['url'] = 

        with open(article['filename'], 'r') as fh:
            lines = fh.readlines()
            for (idx, line) in enumerate(lines):

                m = re.search(r'<(span|p) class="date">(?P<date>[^<]+)</(span|p)>', line)
                if m:
                    date_s = m.groupdict()['date']
                    m = re.search(r'(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w* (?P<day>\d+), (?P<year>\d+).*(?P<time>\d+:\d+) (?P<am_pm>[ap]m)', date_s)
                    assert(m)
                    month = m.groupdict()['month']
                    day = int(m.groupdict()['day'])
                    year = int(m.groupdict()['year'])
                    time_s = m.groupdict()['time']
                    hour = int(time_s.split(':')[0])
                    if m.groupdict()['am_pm'] == 'pm' and hour < 12:
                        hour += 12
                    minute = int(time_s.split(':')[1])
                    am_pm = m.groupdict()['am_pm']
                    month_num = month_name_to_num(month)
                    dt = datetime(year, month_num, day, hour, minute)
                    article['date_str'] = '%s %d, %s' % (month, day, year)
                    article['datetime'] = dt

                m = re.search(r'<title>(?P<title>[^<]+)</title>', line)
                if m:
                    article['title'] = m.groupdict()['title']
            article['content'] = lines

        all_articles.append(article)

    all_articles = sorted(all_articles, key=lambda item: item['datetime'], reverse=True)

    # create index
    with open('index.html', 'w') as ofh:
        ofh.write('<!DOCTYPE html>\n')
        ofh.write('<html>\n')
        ofh.write('<head>\n')
        ofh.write('<meta charset="utf-8" />')
        ofh.write('<meta name="viewport" content="width=device-width, initial-scale=1">')
        ofh.write('<title>Texas Standard</title>\n')
        ofh.write('<link rel="stylesheet" href="main.css" />')
        ofh.write('</head>\n')
        ofh.write('<body>\n')
        ofh.write('<a href="../npr/index.html">NPR</a> | \n')
        ofh.write('<a href="index.html">Texas Standard</a> | \n')
        ofh.write('<a href="../tribune/index.html">Texas Tribune</a> | \n')
        ofh.write('<a href="../statesman/index.html">Statesman</a>\n')
        #ofh.write('<ul>\n')
        # TODO: show dates in list
        #for article in all_articles:
        #    ofh.write('<li><a href="%s">%s</a></li>\n' % (article['filename'], article['title']))
        #ofh.write('</ul>\n')

        in_ul = False
        prev_day = 0
        for article in all_articles:
            day = article['datetime'].day
            diff_day = day != prev_day
            prev_day = day
            if diff_day:
                if in_ul:
                    ofh.write('</ul>\n')
                ofh.write('<p>%s</p>\n' % article['date_str'])
                ofh.write('<ul>\n')
                in_ul = True
            hour = article['datetime'].hour
            am_pm = 'AM' if hour < 12 else 'PM'
            if hour > 12:
                hour -= 12
            minute = article['datetime'].minute
            ofh.write('<li><a href="%s">%s</a></li>\n' % (article['filename'], article['title']))
        if in_ul:
            ofh.write('</ul>\n')

        ofh.write('</body>\n')
        ofh.write('</html>\n')

    return all_articles

def txst_create_article(article):

    template_top_title = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>""" + article['title'] + """</title>
<link rel="stylesheet" href="main.css" />
</head>
<body>
"""

    author = None
    date = None
    to_print = list()

    on = False
    on_n = False
    wrapper_seen = False
    for line in article['content']:

        m = re.search(r'<span class="author">(?P<author>[^<]+)</span>', line)
        if m:
            author = m.groupdict()['author']

        m = re.search(r'<(span|p) class="date">(?P<date>[^<]+)</(span|p)>', line)
        if m:
            date = m.groupdict()['date']

        skip = False

        if re.search(r'<.?div', line):
            skip = True
        if re.search(r'iframe', line):
            skip = True

        if not wrapper_seen and re.search(r'<div class="wpb_wrapper">', line):
            wrapper_seen = True
        elif wrapper_seen and re.search(r'<div class="wpb_wrapper">', line):
            on_n = True
        elif on and re.match('</div>', line):
            on_n = False

        if re.search('<article>', line):
            skip = True
            #on_n = True
        if on and re.search('</article>', line):
            skip = True
            #on_n = False

        if (on and on_n) and not skip:
            to_print.append(line)

        #m = re.search('t-align-left', line)
        #if m:
        #    to_print.append(line)

        on = on_n

        #m = re.search('kut_player.*src="(?P<src>[^"]+)"', line)
        #if m:
        #    src = m.groupdict()['src']
        #    subprocess.run(['wget', '-O', 'kut_player.html', src])
        #    with open('tmp.html', 'r') as fh2:
        #        kut_player_lines = fh2.readlines()
        #    for kut_line in kut_player_lines:
        #        print(kut_line)

    if len(to_print) > 0:
        with open(article['filename'], 'w') as ofh:
            ofh.write(template_top_title)
            ofh.write('<article><h1 class="story-title">%s</h1>\n' % article['title'])
            ofh.write('<div class="story-head">')
            ofh.write('<p>%s</p>\n' % author)
            ofh.write('<p class="date">%s</p>\n' % date)
            ofh.write('</div>\n')
            for p in to_print:
                ofh.write(p)
            ofh.write('</article>\n')
            ofh.write(txst_template_bot)

def txst_fetch():

    try:
        os.mkdir('txst')
    except FileExistsError:
        pass
    shutil.copyfile('main.css', './txst/main.css')
    os.chdir('txst')

    articles = txst_get_articles()

    #pp.pprint(articles)

    for article in articles:
        txst_create_article(article)

    if os.path.isfile('tmp.html'):
        os.remove('tmp.html')

    os.chdir('..')

def statesman_get_articles(do_wget = True):
    articles = list()

    # TODO: use today's date
    #today = date.today()
    #month = month_num_to_name(today.month).lower()
    #url = 'https://www.statesman.com/sitemap/%d/%s/%d/' % (today.year, month, today.day)
    url = 'https://www.statesman.com/sitemap/2020/december/11/'
    if do_wget:
        subprocess.run(['wget', '-O', 'tmp.html', url])
    subprocess.run(['sed', '-i', r's/\(<\/[^>]\+>\)/\1\n/g', 'tmp.html'])

    with open('tmp.html', 'r') as fh:
        lines = fh.readlines()

    subprocess.run(['rm', 'tmp.html'])

    on = False
    for line in lines:
        line = line.rstrip()
        if re.search('<ul class=sitemap-list>', line):
            on = True
        m = re.search('li class=sitemap-list-item><a href=(?P<href>[^>]+)>(?P<title>[^>]+)<', line)
        if on and m:
            url = m.groupdict()['href']
            filename = re.sub(r'.*/(.*)/', r'\1', url) + '.html'
            title = m.groupdict()['title']
            articles.append({'url': url, 'title': title, 'filename': filename})

    # create index
    with open('index.html', 'w') as ofh:
        ofh.write('<!DOCTYPE html>\n')
        ofh.write('<html>\n')
        ofh.write('<head>\n')
        ofh.write('<meta charset="utf-8" />\n')
        ofh.write('<meta name="viewport" content="width=device-width, initial-scale=1">\n')
        ofh.write('<title>Statesman Articles</title>\n')
        ofh.write('<link rel="stylesheet" href="main.css">\n')
        ofh.write('</head>\n')
        ofh.write('<body>\n')
        ofh.write('<a href="../npr/index.html">NPR</a> | \n')
        ofh.write('<a href="../index.html">Texas Standard</a> | \n')
        ofh.write('<a href="index.html">Texas Tribune</a> | \n')
        ofh.write('<a href="../statesman/index.html">Statesman</a>\n')
        ofh.write('<ul>\n')
        for article in articles:
            ofh.write('<li><a href="%s">%s</a></li>\n' % (article['filename'], article['title']))
        ofh.write('</ul>\n')
        ofh.write('</body>\n')
        ofh.write('</html>\n')

    return articles

def statesman_create_article(article):

    subprocess.run(['wget', '-O', 'tmp.html', article['url']])

    subprocess.run(['sed', '-i', r's/\(<\/[^>]\+>\)/\1\n/g', 'tmp.html'])
 
    with open('tmp.html', 'r') as fh:
        lines = fh.readlines()

    subprocess.run(['rm', 'tmp.html'])

    to_print = list()
    author = "unknown"
    date = "unknown"
    title = "unknown"
    for line in lines:
        m = re.search(r'<title>(?P<title>[^"]+)</title>', line)
        if  m:
            title = m.groupdict()['title']
        m = re.search(r'<meta property=article:author content="(?P<author>[^"]+)"', line)
        if  m:
            author = m.groupdict()['author']

        m = re.search(r'<div class=gnt_ar_dt aria-label="Published:? (?P<date>[^"]+)"', line)
        if  m:
            date = m.groupdict()['date']

        if 'gnt_ar_b_p>' in line:
            to_print.append(line)

    template_top_title = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>""" + title + """</title>
<link rel="stylesheet" href="main.css" />
</head>
<body>
"""

    with open(article['filename'], 'w') as ofh:
        ofh.write(template_top_title)
        ofh.write('<article><h1 class="story-title">%s</h1>\n' % title)
        ofh.write('<div class="story-head">')
        ofh.write('<p>%s</p>\n' % author)
        ofh.write('<p>%s</p>\n' % date)
        ofh.write('</div>\n')
        for line in to_print:
            ofh.write(line)
        ofh.write('</article>\n')
        ofh.write(template_bot)

def statesman_fetch():
    try:
        os.mkdir('statesman')
    except FileExistsError:
        pass
    shutil.copyfile('main.css', './statesman/main.css')
    os.chdir('statesman')
    articles = statesman_get_articles()
    for article in articles:
        statesman_create_article(article)
    if os.path.isfile('tmp.html'):
        os.remove('tmp.html')
    os.chdir('..')

def tribune_get_articles():

    articles = list()

    subprocess.run(['wget', '-O', 'tmp.html', 'https://www.texastribune.org/all/?page=1'])

    with open('tmp.html', 'r') as fh:
        lines = fh.readlines()

    for line in lines:
        m = re.search(r'c-story-block__headline[^>]*><a href="(?P<href>[^"]+)">(?P<title>[^<]+)</a>', line)
        if m:
            href = m.groupdict()['href']
            filename = re.sub(r'.*/([^/]+)/', r'\1', href) + '.html'
            url = 'https://www.texastribune.org' + href
            title = '' + m.groupdict()['title']
            articles.append({'url': url, 'title': title, 'filename': filename})

    # create index
    with open('index.html', 'w') as ofh:
        ofh.write('<html>\n')
        ofh.write('<head>\n')
        ofh.write('<meta charset="utf-8" />')
        ofh.write('<meta name="viewport" content="width=device-width, initial-scale=1">')
        ofh.write('<title>Texas Tribune</title>\n')
        ofh.write('<link rel="stylesheet" href="main.css" />')
        ofh.write('</head>\n')
        ofh.write('<body>\n')
        ofh.write('<a href="../npr/index.html">NPR</a> | \n')
        ofh.write('<a href="../index.html">Texas Standard</a> | \n')
        ofh.write('<a href="../tribune/index.html">Texas Tribune</a> | \n')
        ofh.write('<a href="index.html">Statesman</a>\n')
        ofh.write('<ul>\n')
        for article in articles:
            ofh.write('<li><a href="%s">%s</a></li>\n' % (article['filename'], article['title']))
        ofh.write('</ul>\n')
        ofh.write('</body>\n')
        ofh.write('</html>\n')

    return articles

def tribune_create_article(article):

    # c-story-body

    subprocess.run(['wget', '-O', 'tmp.html', article['url']])

    with open('tmp.html', 'r') as fh:
        lines = fh.readlines()

    subprocess.run(['rm', 'tmp.html'])

    to_print = list()
    author = "unknown"
    date = "unknown"
    title = "unknown"
    for line in lines:
        m = re.search(r'<title>(?P<title>[^"]+)</title>', line)
        if  m:
            title = m.groupdict()['title']
        m = re.search(r'<meta name="author" content="(?P<author>[^"]+)">', line)
        if  m:
            author = m.groupdict()['author']

        m = re.search(r'<time class="byline--item t-byline__item l-display-ib" datetime="(?P<date>[^"]+)" title=".*">.*</time>', line)
        if  m:
            date = m.groupdict()['date']

        if '"t-align-left"' in line:
            to_print.append(line)

    template_top_title = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>""" + title + """</title>
<link rel="stylesheet" href="main.css" />
</head>
<body>
"""

    with open(article['filename'], 'w') as ofh:
        ofh.write(template_top_title)
        ofh.write('<article><h1 class="story-title">%s</h1>\n' % title)
        ofh.write('<div class="story-head">')
        ofh.write('<p>%s</p>\n' % author)
        ofh.write('<p>%s</p>\n' % date)
        ofh.write('</div>\n')
        for line in to_print:
            ofh.write(line)
        ofh.write('</article>\n')
        ofh.write(template_bot)

def tribune_fetch():
    try:
        os.mkdir('tribune')
    except FileExistsError:
        pass
    shutil.copyfile('main.css', './tribune/main.css')
    os.chdir('tribune')
    articles = tribune_get_articles()
    for article in articles:
        tribune_create_article(article)
    if os.path.isfile('tmp.html'):
        os.remove('tmp.html')
    os.chdir('..')

#def dallas_fetch():
#    # https://www.dallasnews.com/news/national/
#    # https://www.dallasnews.com/news/world/
#    pass
#
#def bbc_fetch():
#    # https://www.bbc.com/news
#    pass

if __name__ == "__main__":

    npr = False
    txst = False
    statesman = False
    tribune = False

    if len(sys.argv) == 1:
        pass
    elif sys.argv[1] == 'npr':
        npr = True
    elif sys.argv[1] == 'txst':
        txst = True
    elif sys.argv[1] == 'statesman':
        statesman = True
    elif sys.argv[1] == 'tribune':
        tribune = True

    if npr:
        npr_fetch()
    if txst:
        txst_fetch()
    if statesman:
        statesman_fetch()
    if tribune:
        tribune_fetch()
