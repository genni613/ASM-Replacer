all: main.o inst_replacer.o test

main.o: main.cpp
	g++ -c main.cpp
inst_replacer.o : inst_replacer.cpp inst_replacer.h
	g++ -c inst_replacer.cpp inst_replacer.h
test : main.o inst_replacer.o 
	g++ -o test main.o inst_replacer.o 
# gcc -o hello hello.c