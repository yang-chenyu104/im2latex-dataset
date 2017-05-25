import sys, os
from multiprocessing import Pool
from subprocess import call
import numpy as np
from PIL import Image
import difflib
from LevSeq import StringMatcher
import distance
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from utils import detokenize, BASIC_SKELETON

THREADS = 48
DEVNULL = open(os.devnull, "w")


def calc_match(item):
    image1, image2 = item
    if not os.path.exists(image1):
        print (image1)
        return 0
    if not os.path.exists(image2):
        print (image2)
        return 0

    _, _, match1, match2 = img_edit_distance_file(image1, image2, os.path.join('debug', os.path.basename(image1)))
    if match1:
        return 1
    else:
        print (image1)
        return 0

# return (edit_distance, ref, match, match w/o)
def img_edit_distance(im1, im2, out_path=None):
    img_data1 = np.asarray(im1, dtype=np.uint8) # height, width
    img_data1 = np.transpose(img_data1)
    h1 = img_data1.shape[1]
    w1 = img_data1.shape[0]
    img_data1 = (img_data1<=128).astype(np.uint8)
    if im2:
        img_data2 = np.asarray(im2, dtype=np.uint8) # height, width
        img_data2 = np.transpose(img_data2)
        h2 = img_data2.shape[1]
        w2 = img_data2.shape[0]
        img_data2 = (img_data2<=128).astype(np.uint8)
    else:
        img_data2 = []
        h2 = h1
    if h1 == h2:
        seq1 = [''.join([str(i) for i in item]) for item in img_data1]
        seq2 = [''.join([str(i) for i in item]) for item in img_data2]
    elif h1 > h2:# pad h2
        seq1 = [''.join([str(i) for i in item]) for item in img_data1]
        seq2 = [''.join([str(i) for i in item])+''.join(['0']*(h1-h2)) for item in img_data2]
    else:
        seq1 = [''.join([str(i) for i in item])+''.join(['0']*(h2-h1)) for item in img_data1]
        seq2 = [''.join([str(i) for i in item]) for item in img_data2]

    seq1_int = [int(item,2) for item in seq1]
    seq2_int = [int(item,2) for item in seq2]
    big = int(''.join(['0' for i in range(max(h1,h2))]),2)
    seq1_eliminate = []
    seq2_eliminate = []
    seq1_new = []
    seq2_new = []
    for idx,items in enumerate(seq1_int):
        if items>big:
            seq1_eliminate.append(items)
            seq1_new.append(seq1[idx])
    for idx,items in enumerate(seq2_int):
        if items>big:
            seq2_eliminate.append(items)
            seq2_new.append(seq2[idx])
    if len(seq2) == 0:
        return (len(seq1), len(seq1), False, False)

    def make_strs(int_ls, int_ls2):
        d = {}
        seen = []
        def build(ls):
            for l in ls:
                if int(l, 2) in d: continue
                found = False
                l_arr = np.array(map(int, l))
            
                for l2,l2_arr in seen:
                    if np.abs(l_arr -l2_arr).sum() < 5:
                        d[int(l, 2)] = d[int(l2, 2)]
                        found = True
                        break
                if not found:
                    d[int(l, 2)] = unichr(len(seen))
                    seen.append((l, np.array(map(int, l))))
                    
        build(int_ls)
        build(int_ls2)
        return "".join([d[int(l, 2)] for l in int_ls]), "".join([d[int(l, 2)] for l in int_ls2])
    #if out_path:
    seq1_t, seq2_t = make_strs(seq1, seq2)

    edit_distance = distance.levenshtein(seq1_int, seq2_int)
    match = True
    if edit_distance>0:
        matcher = StringMatcher(None, seq1_t, seq2_t)

        ls = []
        for op in matcher.get_opcodes():
            if op[0] == "equal" or (op[2]-op[1] < 5):
                ls += [[int(r) for r in l]
                       for l in seq1[op[1]:op[2]]
                       ] 
            elif op[0] == "replace":
                a = seq1[op[1]:op[2]]
                b = seq2[op[3]:op[4]]
                ls += [[int(r1)*3 + int(r2)*2
                        if int(r1) != int(r2) else int(r1)
                        for r1, r2 in zip(a[i] if i < len(a) else [0]*1000,
                                          b[i] if i < len(b) else [0]*1000)]
                       for i in range(max(len(a), len(b)))]
                match = False
            elif op[0] == "insert":

                ls += [[int(r)*3 for r in l]
                       for l in seq2[op[3]:op[4]]]
                match = False
            elif op[0] == "delete":
                match = False
                ls += [[int(r)*2 for r in l] for l in seq1[op[1]:op[2]]]

        vmax = 3
        plt.imshow(np.array(ls).transpose(), vmax=vmax)

        cmap = LinearSegmentedColormap.from_list('mycmap', [(0. /vmax, 'white'),
                                                            (1. /vmax, 'grey'),
                                                            (2. /vmax, 'blue'),
                                                            (3. /vmax, 'red')])

        plt.set_cmap(cmap)
        plt.axis('off')
        plt.savefig(out_path, bbox_inches="tight")

    match1 = match
    seq1_t, seq2_t = make_strs(seq1_new, seq2_new)

    if len(seq2_new) == 0 or len(seq1_new) == 0:
        if len(seq2_new) == len(seq1_new):
            return (edit_distance, max(len(seq1_int),len(seq2_int)), match1, True)# all blank
        return (edit_distance, max(len(seq1_int),len(seq2_int)), match1, False)
    match = True
    matcher = StringMatcher(None, seq1_t, seq2_t)

    ls = []
    for op in matcher.get_opcodes():
        if op[0] == "equal" or (op[2]-op[1] < 5):
            ls += [[int(r) for r in l]
                   for l in seq1[op[1]:op[2]]
                   ] 
        elif op[0] == "replace":
            a = seq1[op[1]:op[2]]
            b = seq2[op[3]:op[4]]
            ls += [[int(r1)*3 + int(r2)*2
                    if int(r1) != int(r2) else int(r1)
                    for r1, r2 in zip(a[i] if i < len(a) else [0]*1000,
                                      b[i] if i < len(b) else [0]*1000)]
                   for i in range(max(len(a), len(b)))]
            match = False
        elif op[0] == "insert":

            ls += [[int(r)*3 for r in l]
                   for l in seq2[op[3]:op[4]]]
            match = False
        elif op[0] == "delete":
            match = False
            ls += [[int(r)*2 for r in l] for l in seq1[op[1]:op[2]]]

    match2 = match


    return (edit_distance, max(len(seq1_int),len(seq2_int)), match1, match2)

def img_edit_distance_file(file1, file2, output_path=None):
    img1 = Image.open(file1).convert('L')
    if os.path.exists(file2):
        img2 = Image.open(file2).convert('L')
    else:
        img2 = None
    return img_edit_distance(img1, img2, output_path)

def remove_temp_files(name):
    """ Removes .aux, .log, .pdf and .tex files for name """
    os.remove(name+".aux")
    os.remove(name+".log")
    #os.remove(name+".tex")
    os.remove(name+".pdf")

def tabular_to_image(render):
    try:
        image_name, tabular = render
        with open(image_name + '.tex', 'w') as fout:
            fout.write(BASIC_SKELETON%tabular)

        call(["pdflatex", '-interaction=nonstopmode', '-halt-on-error', image_name],
                        stdout=DEVNULL, stderr=DEVNULL)
        os.system("convert -density 200 -quality 100 %s.pdf %s.png"%(image_name, image_name))
        remove_temp_files(image_name)


    except Exception as e:
        pass


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print >> sys.stderr, 'Usage: python %s <im2latex.lst> <tabular_images> <im2latex_tabulars.tok.lst> <tabular_images_validate>'%sys.argv[0]
        sys.exit(1)

    tabular_images = sys.argv[2]
    tabular_images_validate = sys.argv[4]
    if not os.path.exists(tabular_images_validate):
        os.makedirs(tabular_images_validate)
    # Change to image dir because textogif doesn't seem to work otherwise...
    oldcwd = os.getcwd()

    with open(sys.argv[1]) as fim2latex:
        images = {}
        for line in fim2latex:
            if len(line.strip()) > 0:
                tabular_id, image, mode = line.strip().split()
                tabular_id = int(tabular_id)
                images[tabular_id] = image
    renders = []
    with open(sys.argv[3]) as ftabulars:
        for tabular_id,line in enumerate(ftabulars):
            if len(line.strip()) > 0:
                tokens = line.strip().split(' ')
                line_out = detokenize(tokens)
                renders.append((images[tabular_id], line_out))

    # Check we are not in image dir yet (avoid exceptions)
    if not tabular_images_validate in os.getcwd():
        os.chdir(tabular_images_validate)

    pool = Pool(THREADS)
    pool.map(tabular_to_image, renders)
    os.chdir(oldcwd)

    pool = Pool(THREADS)
    total_match = 0
    num_total = 0
    for match in pool.imap(calc_match, [(os.path.join(tabular_images,item[0]+'.png'), os.path.join(tabular_images_validate,item[0]+'.png')) for item in renders]):
        total_match += match
        num_total += 1

    print ('%d out of %d correct!'%(total_match, num_total))
