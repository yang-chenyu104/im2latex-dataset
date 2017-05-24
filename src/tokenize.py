import sys
from plasTeX.TeX import TeX

BASIC_SKELETON = r"""
\documentclass[12pt]{article}
\pagestyle{empty}
\usepackage{booktabs}
\usepackage{amsmath}
\usepackage{multirow}
\begin{document}

\begin{tabular}%s\end{tabular}

\end{document}
"""

# special symbol for \n
NEWLINE = '<__NEWLINE__>'
SPACE = '<__SPACE__>'

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print >> sys.stderr, 'Usage: python %s <tabulars> <tokenized-tabulars>'%sys.argv[0]
        sys.exit(1)
    with open(sys.argv[1]) as fin:
        with open(sys.argv[2], 'w') as fout:
            for line in fin:
                _, tabular = line.split('\t', 1)
                tex = TeX()
                tex.input(BASIC_SKELETON%(tabular.replace(NEWLINE, '\n').strip()))
                tokens = [token for token in tex.itertokens()]
                tokens_out = []
                for token in tokens:
                    if token == 'par':
                        token = NEWLINE
                    elif token == ' ':
                        token = SPACE
                    elif len(token) > 1: # mathcal -> \mathcal
                        token = '\\'+token
                    elif token == '\\':
                        token = '\\\\'
                    if token == '%':
                        token = '\\%'
                    if '\\active::' in token:
                        token = token.replace('\\active::', '')
                    tokens_out.append(token)
                fout.write(' '.join(tokens_out)[272:-85] + '\n')
