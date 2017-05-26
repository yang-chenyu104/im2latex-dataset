# TABLE2LATEX Makefile

# Figure out app path
DIR := $(shell readlink $(dir $(lastword $(MAKEFILE_LIST))) -f)

CXX = g++

CXXFLAGS = -std=c++11
CXXFLAGS += -O3

SRC = $(wildcard $(DIR)/src/*.cpp)
HDR = $(wildcard $(DIR)/src/*.hpp)
BIN = $(DIR)/bin
OBJ = $(SRC:.cpp=.o)

all: tokenizer_main

tokenizer_main: $(BIN)/tokenizer

$(BIN):
	mkdir -p $(BIN)

$(BIN)/tokenizer: $(OBJ) $(BIN)
	$(CXX) $(CXXFLAGS) $(INCFLAGS) \
	$(OBJ) -o $@

$(OBJ): %.o: %.cpp $(HDR)
	$(CXX) $(CXXFLAGS) -Wno-unused-result $(INCFLAGS) -c $< -o $@

clean:
	rm -rf $(OBJ)
	rm -rf $(BIN)

.PHONY: clean tokenizer_main
