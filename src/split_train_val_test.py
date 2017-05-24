import sys
import math
import random
random.seed(920110)

TRAIN_RATIO = 0.96
VALIDATE_RATIO = 0.02
TEST_RATIO = 1. - TRAIN_RATIO - VALIDATE_RATIO

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print >> sys.stderr, 'Usage: python %s <im2latex.lst> <im2latex_tabulars.lst>'%sys.argv[0]
        sys.exit(1)
    with open(sys.argv[1]) as fim2latex:
        with open(sys.argv[2]) as ftabulars:
            articles = {}
            tabulars = {}
            for tabular_id,line in enumerate(ftabulars):
                article = line.split('\t',1)[0].strip()
                articles[tabular_id] = article

            total = 0
            datapoints = {}
            for line in fim2latex:
                if len(line.strip()) > 0:
                    tabular_id, image, mode = line.strip().split()
                    tabular_id = int(tabular_id)
                    article = articles[tabular_id]
                    datapoints.setdefault(article, []).append(line.strip())
                    total += 1

            shuffled_articles = list(set(articles.values()))
            random.shuffle(shuffled_articles)
            written = 0
            lines_train, lines_validate, lines_test = [], [], []
            for article in shuffled_articles:
                if written < int(math.floor(TRAIN_RATIO*total)):
                    lines = lines_train
                elif written < int(math.floor((TRAIN_RATIO+VALIDATE_RATIO)*total)):
                    lines = lines_validate
                else:
                    lines = lines_test
                for line in datapoints[article]:
                    lines.append(line)
                    written += 1
            with open('im2latex_train.lst', 'w') as ftrain:
                with open('im2latex_validate.lst', 'w') as fvalidate:
                    with open('im2latex_test.lst', 'w') as ftest:
                        random.shuffle(lines_train)
                        random.shuffle(lines_validate)
                        random.shuffle(lines_test)
                        for line in lines_train:
                            ftrain.write(line+'\n')
                        for line in lines_validate:
                            fvalidate.write(line+'\n')
                        for line in lines_test:
                            ftest.write(line+'\n')
    
