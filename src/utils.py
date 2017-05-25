import re

# special symbol for \n
NEWLINE = '<__NEWLINE__>'
SPACE = '<__SPACE__>'

BASIC_SKELETON = r"""
\documentclass[12pt]{article}
\pdfpagewidth 16in
\pdfpageheight 16in
\pagestyle{empty}
\usepackage{amsmath}
\usepackage{multirow}
\usepackage{booktabs}
\begin{document}

\begin{tabular}%s\end{tabular}

\end{document}
"""

def detokenize(tokens):
    tokens_out = []
    need_blank = False
    for token in tokens:
        if need_blank:
            if (token[0] >= 'a' and token[0] <= 'z') or (token[0] >= 'A' and token[0] <= 'Z'):
                token = ' ' + token
            need_blank = False
        if token == NEWLINE:
            token = '\n'
        if token == '\\'+SPACE:
            token = '\ '
        if token == SPACE:
            token = ' '
        if token[0] == '\\':
            if (token[1] >= 'a' and token[1] <= 'z') or (token[1] >= 'A' and token[1] <= 'Z'):
                need_blank = True
        tokens_out.append(token)
    return ''.join(tokens_out)

def repl(m):
    punctuation = m.group(1)
    if punctuation == ' ':
        punctuation = '\\SpAcEsPaCe'
    elif punctuation == '\\':
        punctuation = '\\EsCaPeSlAsH'
    elif punctuation == '%':
        punctuation = '\\EsCaPePeRcEnT'
    return '\\SlAsHsLaSh'+punctuation+'\\\\'

def pre_tokenize(text):
    text = text.replace(NEWLINE, '\n').strip()
    return re.sub(r'\\([^a-zA-Z])', repl, text)

def post_tokenize(tokens):
    tokens_out = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == 'par':
            token = NEWLINE
        elif token == ' ':
            token = SPACE
        elif token == 'SlAsHsLaSh':
            i = i + 1
            token = tokens[i]
            if token == 'SpAcEsPaCe':
                token = '\\' + SPACE
            elif token == 'EsCaPeSlAsH':
                token = '\\\\'
            elif token == 'EsCaPePeRcEnT':
                token = '\\%'
            else:
                token = '\\' + token
            i = i + 1
        elif len(token) > 1: # mathcal -> \mathcal
            token = '\\'+token
        if '\\active::' in token:
            token = token.replace('\\active::', '')
        tokens_out.append(token)
        i = i + 1
    return tokens_out
