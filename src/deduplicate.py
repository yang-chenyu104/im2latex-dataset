#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  deduplicate.py
#  Parses arxiv tar files of source files for latex tabulars
#
#  © Copyright 2017, mitar (https://github.com/mitar)
#                    Anssi "Miffyli" Kanervisto
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
import sys
import shutil

def main(im2latex_file, tabulars_file):
    im2latex_tmp_file = '.tmp.' + im2latex_file
    tabulars_tmp_file = '.tmp.' + tabulars_file

    # for im2latex file, remove duplicate entries and reassign tabular ids
    old2new = {}
    max_id = 0
    images = set([])
    with open(im2latex_file) as fim2latex:
        with open(im2latex_tmp_file, "w") as fout:
            for line in fim2latex:
                if len(line.strip()) > 0:
                    tabular_id, image, mode = line.strip().split()
                    tabular_id = int(tabular_id)
                    if image not in images:
                        images.add(image)
                        if tabular_id not in old2new:
                            new_id = max_id
                            max_id = max_id + 1
                            old2new[tabular_id] = new_id
                        else:
                            new_id = old2new[tabular_id]
                        fout.write('%d %s %s\n'%(new_id, image, mode))
    with open(tabulars_file) as ftabulars:
        with open(tabulars_tmp_file, "w") as fout:
            tabulars = {}
            tabular_id = 0
            for tabular_id,line in enumerate(ftabulars):
                if tabular_id in old2new:
                    new_id = old2new[tabular_id]
                    tabulars[new_id] = line.strip()
            for new_id in range(len(tabulars)):
                fout.write('%s\n'%(tabulars[new_id]))
    shutil.move(im2latex_tmp_file, im2latex_file)
    shutil.move(tabulars_tmp_file, tabulars_file)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("usage: python %s <im2latex.lst> <im2latex_tabulars.lst>\n"%sys.argv[0]+    
              "im2latex.lst and im2latex_tabulars.lst should be the output by src/tabular2image.py\n"+
              "These two files will be overwritten, duplicate entries will be removed.")
    else:
        main(sys.argv[1], sys.argv[2])

