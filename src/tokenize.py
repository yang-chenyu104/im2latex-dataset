import sys, re
from plasTeX.TeX import TeX
from utils import pre_tokenize, post_tokenize, BASIC_SKELETON


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print >> sys.stderr, 'Usage: python %s <tabulars> <tokenized-tabulars>'%sys.argv[0]
        sys.exit(1)
    with open(sys.argv[1]) as fin:
        with open(sys.argv[2], 'w') as fout:
            idx = 0
            for line in fin:
                _, tabular = line.split('\t', 1)
                idx += 1
                #if idx != 11:
                #    continue
                tex = TeX()
                tex.input(BASIC_SKELETON%(pre_tokenize(tabular)))
                #print (pre_tokenize(tabular))
                tokens = [token for token in tex.itertokens()]
                tokens_out = []
                #jprint (':'.join(tokens))
                tokens_out = post_tokenize(tokens)
                #print (':'.join(tokens_out))
                fout.write(' '.join(tokens_out)[385:-86] + '\n')
