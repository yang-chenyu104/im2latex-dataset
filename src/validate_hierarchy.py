import sys, os

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print >> sys.stderr, 'Usage: python %s <im2latex_tabulars.hier.lst> <im2latex_tabulars.flat.lst>'%sys.argv[0]
        sys.exit(1)

    with open(sys.argv[1]) as fin:
        with open(sys.argv[2], 'w') as fout:
            for line in fin:
                if len(line.strip()) > 0:
                    tokens = line.strip().split(' ')
                    tokens_out = []
                    i = 0
                    while i < len(tokens):
                        token = tokens[i]
                        if token == '<__CELL__>':
                            i += 1
                            token = tokens[i]
                            items = token.split('<__SPLIT__>')
                            tokens_out.extend(items)
                        else:
                            tokens_out.append(token)
                        i += 1
                fout.write(' '.join(tokens_out) + '\n')

