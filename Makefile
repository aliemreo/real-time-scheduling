# Makefile for RTS Parser
CC = gcc
CXX = g++
CFLAGS = -Wall -Wextra -std=c99
CXXFLAGS = -Wall -Wextra -std=c++11

# Targets
all: test_parser

# Build the parser test program
test_parser: rts_parser.o test_parser.o
	$(CC) $(CFLAGS) -o test_parser.exe rts_parser.o test_parser.o

# Compile parser implementation
rts_parser.o: rts_parser.c rts_parser.h
	$(CC) $(CFLAGS) -c rts_parser.c -o rts_parser.o

# Compile test program
test_parser.o: test_parser.c rts_parser.h
	$(CC) $(CFLAGS) -c test_parser.c -o test_parser.o

# Clean build artifacts
clean:
	rm -f *.o test_parser.exe

# Test with example files
test: test_parser
	./test_parser.exe example1_simple.txt
	./test_parser.exe example2_with_aperiodic.txt
	./test_parser.exe example3_dynamic.txt
	./test_parser.exe example4_complex.txt

.PHONY: all clean test
