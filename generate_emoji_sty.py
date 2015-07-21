from bs4 import BeautifulSoup
import base64
import os
import json
import requests
import requests_cache

# http://www.unicode.org/emoji/charts/index.html
# http://www.unicode.org/emoji/charts/full-emoji-list.html
PAGE_URL = 'http://www.unicode.org/emoji/charts/full-emoji-list.html'

def get_header_names(header):
    cols = header.find_all('th')
    cols = [c.get_text() for c in cols]
    cols = [c.replace('*','') for c in cols]
    cols = [c.lower() for c in cols]
    return cols

def extract_image(column):
    if 'miss' in column['class']:
        return None

    if 'miss7' in column['class']:
        return None

    data = column.img['src']
    data_start = data.find("base64,")
    if data_start == -1:
        return None
    
    data = base64.b64decode(data[data_start + len("base64,"):])
    return data

def save_image(folder, imgSrc, filename):
    if os.path.exists(folder) is False:
        os.mkdir(folder)

    filename = os.path.join(folder, filename)
    if os.path.exists(filename):
        return

    img = extract_image(imgSrc)
    if img is not None:
        with open(filename, 'wb') as out:
            out.write(img)

preamble = r"""\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{emoji}
\RequirePackage{graphicx}
\RequirePackage{kvoptions}
\RequirePackage{ifthen}
\RequirePackage{ifxetex}

\SetupKeyvalOptions{family=emoji, prefix=emoji@}

\newcommand{\@emojifolder}{ios}
\DeclareVoidOption{ios}{
    \renewcommand{\@emojifolder}{ios}
}
\DeclareVoidOption{android}{
    \renewcommand{\@emojifolder}{android}
}
\DeclareVoidOption{twitter}{
    \renewcommand{\@emojifolder}{twitter}
}
\DeclareVoidOption{windows}{
    \renewcommand{\@emojifolder}{windows}
}
\DeclareVoidOption{bw}{
    \renewcommand{\@emojifolder}{bw}
}
\DeclareVoidOption{text}{
    \renewcommand{\@emojifolder}{text}
}
\DeclareStringOption{font}

\ProcessKeyvalOptions*

\newenvironment{ios-emojis}{%
  \let\@oldemojifolder\@emojifolder%
  \renewcommand{\@emojifolder}{ios}%
}{%
  \renewcommand{\@emojifolder}{\@oldemojifolder}%
}

\newenvironment{android-emojis}{%
  \let\@oldemojifolder\@emojifolder%
  \renewcommand{\@emojifolder}{android}%
}{%
  \renewcommand{\@emojifolder}{\@oldemojifolder}%
}

\newenvironment{twitter-emojis}{%
  \let\@oldemojifolder\@emojifolder%
  \renewcommand{\@emojifolder}{twitter}%
}{%
  \renewcommand{\@emojifolder}{\@oldemojifolder}%
}

\newenvironment{windows-emojis}{%
  \let\@oldemojifolder\@emojifolder%
  \renewcommand{\@emojifolder}{windows}%
}{%
  \renewcommand{\@emojifolder}{\@oldemojifolder}%
}

\newenvironment{bw-emojis}{%
  \let\@oldemojifolder\@emojifolder%
  \renewcommand{\@emojifolder}{bw}%
}{%
  \renewcommand{\@emojifolder}{\@oldemojifolder}%
}

\newenvironment{text-emojis}{%
  \let\@oldemojifolder\@emojifolder%
  \renewcommand{\@emojifolder}{text}%
}{%
  \renewcommand{\@emojifolder}{\@oldemojifolder}%
}

\newcommand{\emoji}[2][\@emojifolder]{%
  \ifthenelse{\equal{#1}{text}}{%
	\ifxetex%
	  \ifx\emoji@font\@empty%
	  \else%
	    {\fontspec{\emoji@font}\char"#2}%
	  \fi%
	\else%
	\fi%
  }{%
    \includegraphics[height=1em]{#1/#2.png}%
  }%
}

"""

def scrape():
    soup = BeautifulSoup(requests.get(PAGE_URL).text, "html5lib")
    table = soup('table')[0]

    header = table.find('tr')
    keys = get_header_names(header)

    with open('emoji.sty', 'w') as out:
        out.write(preamble)

        out.write("\\ifxetex\n\\else\n")
        for row in header.find_next_siblings('tr'):
            fields = {k:c for k, c in zip(keys, row.find_all('td')) }
            codes = fields['code'].text.replace('U+', '').split(' ')
            filename = "-".join(codes) + ".png"

            save_image('ios', fields['apple'], filename)
            save_image('android', fields['andr'], filename)
            save_image('twitter', fields['twit'], filename)
            save_image('windows', fields['wind'], filename)
            save_image('bw', fields['b&w'], filename)

            if len(codes) > 1:
                continue

            code = "".join(codes)
            img = r"\includegraphics[height=1em]{\@emojifolder/%s}" % filename
            out.write("\\DeclareUnicodeCharacter{%s}{%s}\n" % (code, img))

        out.write("\\fi\n")
        out.write("\n\\endinput")

if __name__ == '__main__':
    requests_cache.install_cache('scrape_cache')
    scrape()
