#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  tabular2image.py
#  Turns bunch of LaTeX tabulars into images and dataset listing
#
#  © Copyright 2016, Anssi "Miffyli" Kanervisto
#  
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  

"""
Purpose of this script is to turn list of tex tabulars into images
and a dataset list for OpenAI im2latex task.
Script outputs two lists:
    - im2latex.lst
        - Each row is: [idx of LaTeX tabular] [image name] [render type]
            - idx of tabular is the line number in im2latex_tabulars.lst
            - image name is name of the image (without filetype) 
            - render type is name of the method used to draw the picture
              (See RENDERING_SETUPS)
    - im2latex_tabulars.lst
        - List of LaTeXs, one per line
            -> All \\n characters are replaced by <__NEWLINE__>
"""

import glob
import sys
import os
import shutil
import hashlib
from multiprocessing import Pool
from subprocess import call

# Max number of tabulars included
MAX_NUMBER = float('inf')

THREADS = 96

IMAGE_DIR = "tabular_images"
PDF_DIR = "tabular_pdfs"
DATASET_FILE = "im2latex.lst"
NEW_TABULAR_FILE = "im2latex_tabulars.lst"

NEWLINE = '<__NEWLINE__>'
# Running a thread pool masks debug output. Set DEBUG to 1 to run
# tabulars over images sequentially to see debug errors more clearly
DEBUG = False
DEVNULL = open(os.devnull, "w")

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

# Different settings used to render images
# in format key: [skeleton, rendering_call]
#   - skeleton is the LaTeX code in which tabular is inserted 
#     (see BASIC_SKELETON)
#   - rendering_call is the system call made to turn .tex into .png
# Each rendering setup is done for each tabular.
# key/name is used to identify different renderings in dataset file

#RENDERING_SETUPS = {"basic": [BASIC_SKELETON, "./textogif -png -dpi 200 %s"]}
RENDERING_SETUPS = {"basic": [BASIC_SKELETON, 
                              "convert -density 200 -quality 100 %s.pdf %s.png",
                              lambda filename: os.path.isfile(filename + ".png")]
                   }

def remove_temp_files(name):
    """ Removes .aux, .log, .pdf and .tex files for name """
    os.remove(name+".aux")
    os.remove(name+".log")
    os.remove(name+".tex")

def tabular_to_image(tabular):
    """ Turns given tabular into images based on RENDERING_SETUPS
    returns list of lists [[image_name, rendering_setup], ...], one list for
    each rendering.
    Return None if couldn't render the tabular"""
    #tabular = tabular.strip("%")
    if len(tabular.strip()) < 1:
        return []
    source_article, tabular = tabular.split('\t', 1)
    tabular = tabular.replace(NEWLINE, "\n").strip()
    #name = hashlib.sha1(tabular.encode('utf-8')).hexdigest()[:15]
    name = hashlib.sha1(tabular.encode('utf-8')).hexdigest()
    ret = []
    try:
        for rend_name, rend_setup in RENDERING_SETUPS.items():
            full_path = name+"_"+rend_name
            if len(rend_setup) > 2 and rend_setup[2](full_path):
                print("Skipping, already done: " + full_path)
                ret.append([full_path, rend_name])
                continue
            # Create latex source
            latex = rend_setup[0] % tabular
            # Write latex source
            with open(full_path+".tex", "w") as f:
                f.write(latex)
            
            # Call pdflatex to turn .tex into .pdf
            code = call(["pdflatex", '-interaction=nonstopmode', '-halt-on-error', full_path+".tex"],
                        stdout=DEVNULL, stderr=DEVNULL)
            if code != 0:
                os.system("rm -rf "+full_path+"*")
                return None
            
            # Turn .pdf to .png
            # Handles variable number of places to insert path.
            # i.e. "%s.tex" vs "%s.pdf %s.png"
            full_path_strings = rend_setup[1].count("%")*(full_path,)
            code = call((rend_setup[1] % full_path_strings).split(" "),
                        stdout=DEVNULL, stderr=DEVNULL)
            
            #Remove files
            try:
                remove_temp_files(full_path)
            except Exception as e:
                # try-except in case one of the previous scripts removes these files
                # already
                return None
            
            # Detect of convert created multiple images -> multi-page PDF
            resulted_images = glob.glob(full_path+"-*") 
            
            if code != 0:
                # Error during rendering, remove files and return None
                os.system("rm -rf "+full_path+"*")
                return None
            elif len(resulted_images) > 1:
                # We have multiple images for same tabular
                # Discard result and remove files
                os.system("rm -rf "+full_path+"*")
                #for filename in resulted_images:
                #    os.system("rm -rf "+filename+"*")
                return None
            else:
                try:
                    pdf_path = os.path.join(PDF_DIR, full_path+".pdf")
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    shutil.move(full_path+".pdf", PDF_DIR)
                except Exception as e:
                    # try-except in case one of the previous scripts removes these files
                    # already
                    os.system("rm -rf "+full_path+"*")
                    return None
                ret.append([full_path, rend_name])
        return ret
    except Exception as e:
        return None
    
            
def main(tabular_list):
    tabulars = open(tabular_list).read().split("\n")
    if MAX_NUMBER < float('inf'):
        tabulars = tabulars[:MAX_NUMBER]
    global PDF_DIR
    PDF_DIR = os.path.realpath(PDF_DIR)
    need_mkdirs = [IMAGE_DIR, PDF_DIR]
    for need_mkdir in need_mkdirs:
        if not os.path.exists(need_mkdir):
            os.makedirs(need_mkdir)
    print("Turning tabulars into images...")

    # Change to image dir because textogif doesn't seem to work otherwise...
    oldcwd = os.getcwd()
    # Check we are not in image dir yet (avoid exceptions)
    if not IMAGE_DIR in os.getcwd():
        os.chdir(IMAGE_DIR)
    
    names = None
    
    if DEBUG:
        names = [tabular_to_image(tabular) for tabular in tabulars]
    else:
        pool = Pool(THREADS)
        names = list(pool.imap(tabular_to_image, tabulars))
    
    os.chdir(oldcwd)

    zipped = list(zip(tabulars, names))
    
    new_dataset_lines = []
    new_tabulars = []
    ctr = 0
    for tabular in zipped:
        if tabular[1] is None:
            continue
        for rendering_setup in tabular[1]:
            new_dataset_lines.append(str(ctr)+" "+" ".join(rendering_setup))
        new_tabulars.append(tabular[0])
        ctr += 1
    
    with open(NEW_TABULAR_FILE, "w") as f:
        f.write("\n".join(new_tabulars))
    
    with open(DATASET_FILE, "w") as f:
        f.write("\n".join(new_dataset_lines))

def check_validity(dataset_file, tabular_file, tabular_dir):
    """ Checks if lists are valid, ie. no files missing etc """
    dataset_lines = open(dataset_file).read().split("\n")
    tabular_file = open(tabular_file).read().split("\n")
    tabular_images = os.listdir(tabular_dir)
    max_id = 0
    missing_files = 0
    
    for line in dataset_lines:
        if line == "": continue
        splt = line.split(" ")
        max_id = splt[0]
        if not splt[1]+".png" in tabular_images:
            missing_files += 1
    
    if int(max_id)+1 != len(tabular_file): 
        print("Max id in dataset != tabular_file length (%d vs %d)" % 
              (int(max_id), len(tabular_file)))
    
    print("%d files missing" % missing_files)
    
if __name__ == '__main__':
    if len(sys.argv) != 2 and len(sys.argv) != 4:
        print("To generate datasets:           python %s tabularlist\n"%sys.argv[0]+
              "To validate generated datasets: "+
                "python %s dataset_list tabular_list tabular_dir"%sys.argv[0])
    elif len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        check_validity(sys.argv[1], sys.argv[2], sys.argv[3]) 

