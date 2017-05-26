#include <cstdio>
#include <cstring>
#include <stdlib.h>
#include <vector>
#include <string>
#include <iostream>

std::vector<std::string> split(const std::string &text, char sep) {
    std::vector<std::string> tokens;
    std::size_t start = 0, end = 0;
    while ((end = text.find(sep, start)) != std::string::npos) {
        if (end != start) {
            tokens.push_back(text.substr(start, end - start));
        }
        start = end + 1;
    }
    if (end != start) {
        tokens.push_back(text.substr(start));
    }
    return tokens;
}

int main(int argc, char *argv[])
{
    if (argc != 3) {
        std::cout << "Usage: ./" << argv[0] << " <im2latex_tabulars.tok.lst> <im2latex_tabulars.hier.lst>" << std::endl;
    } else {
        FILE * fp;
        FILE * fpout;
        char * line = NULL;
        size_t len = 0;
        ssize_t read;

        fp = fopen(argv[1], "r");
        fpout = fopen(argv[2], "w");
        if (fp == NULL)
            exit(EXIT_FAILURE);

        int total = 0;
        while ((read = getline(&line, &len, fp)) != -1) {
            if (++total % 1000 == 0)
                std::cout<<total<<std::endl;
            while (std::strlen(line) > 0) {
                if (line[std::strlen(line)-1] == '\n' || line[std::strlen(line)-1] == ' ')
                    line[std::strlen(line)-1] = '\0';
                else
                    break;
            }
            std::string s = line;
            std::vector<std::string> tokens = split(s, ' ');
            std::vector<std::string> tokens_out = std::vector<std::string>();
            int num_matching = 0;
            std::vector<std::string>::iterator it;
            bool flag_left = false;
            for(it = tokens.begin(); it != tokens.end(); ++it) {
                // find matching }
                if (! (*it).compare("{")) {
                    ++num_matching;
                    flag_left = true;
                } else if (! (*it).compare("}")) {
                    --num_matching;
                }
                tokens_out.push_back(*it);
                if (num_matching == 0 && flag_left) {
                    ++it;
                    break;
                }
            }
            for (; it != tokens.end(); ++it) {
                if ( ((*it).compare("<__SPACE__>") ) && ((*it).compare("\\hline")) && ((*it).compare("\\\\")) && ((*it).compare("&")))
                    break;
                tokens_out.push_back(*it);

            }
            std::vector<std::string> tokens_buffer = std::vector<std::string>();
            std::string s_buffer = "";
            bool flag = false;
            while (it != tokens.end()) {
                if ( !((*it).compare("<__SPACE__>") )) {
                    if (flag) {
                        tokens_out.push_back(*it);
                    } else {
                        tokens_buffer.push_back(*it);
                    }
                } else if ((! (*it).compare("\\hline")) || (! (*it).compare("\\\\")) || (! (*it).compare("&"))) {
                    if (s_buffer != "") {
                        tokens_out.push_back("<__CELL__>");
                        tokens_out.push_back(s_buffer.substr(11));
                    }
                    if (tokens_buffer.size() > 0) {
                        for (auto & s: tokens_buffer) {
                            tokens_out.push_back(s);
                        }
                        tokens_buffer.clear();
                    }
                    s_buffer.clear();
                    tokens_out.push_back(*it);
                    flag = true;
                } else {
                    flag = false;
                    for (auto & s: tokens_buffer) {
                        s_buffer.append("<__SPLIT__>");
                        s_buffer.append(s);
                    }
                    tokens_buffer.clear();
                    s_buffer.append("<__SPLIT__>");
                    s_buffer.append(*it);
                }
                ++it;
            }
            if (s_buffer != "") {
                for (auto & s: tokens_buffer)
                    s_buffer.append(s);
                tokens_buffer.clear();
                tokens_out.push_back("<__CELL__>");
                tokens_out.push_back(s_buffer.substr(11));
            }
            for (int i = 0; i < tokens_out.size(); ++i) {
                if (i>0)
                    fprintf(fpout, " ");
                fprintf(fpout, "%s", tokens_out[i].c_str());
            }
            fprintf(fpout, "\n");
        }

        fclose(fp);
        fclose(fpout);
        return 0;
                                           
    }
}
