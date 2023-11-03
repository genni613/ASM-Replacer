#include <stdio.h>
#include <fstream>
#include <iostream>
#include <vector>
#include <string>
#include <regex>
#include <tuple>


class Pattern{
    public:
    std::vector<std::string> op_list;
    std::vector<std::vector<int>> relation;
};

class Instruction{
    public:
    std::string op;
    std::vector<std::string> operand;
    int pos;
    std::string pc;
    std::string s_code;
    std::string bin;
    void clear(){
        operand.clear();
        op.clear();
    }
};


class File_Process{
    public:
    File_Process(std::string asm_path, std::string output_path);
    ~File_Process() {}
    std::vector<std::string> source;

    private:
    std::string _asm_path;
    std::string _output_path;
    
};

class Search_Result{
    public:
    Search_Result(){}
    ~Search_Result(){}
    std::vector<Instruction> ins;

};

class Pattern_Search{
    public:
    Pattern_Search(std::vector<std::string> &source,std::vector<std::string> &pc,std::vector<std::string> &ins);
    ~Pattern_Search() {}
    void split_by_basicblock(std::vector<std::string> &source,std::vector<std::string> &pc,std::vector<std::string> &ins);
    void preprocess();  
    bool confict();
    Search_Result find_continuous_pattern();
    Search_Result find_discontinuous_pattern();
    bool is_relate(Instruction &i1, Instruction &i2);
    void getOperand(std::vector<std::string> &str, std::string reg);
    void operandCheck(std::vector<std::string> &str);


    private:
    std::vector<std::vector<std::string>> operandList;
    std::vector<std::vector<std::string>> basic_block;
    
    
    // std::vector<Pattern> _pattern;
    // std::vector<std::string> _source;
    std::vector<std::vector<std::string>> line_number;
    std::vector<std::vector<std::string>> ins_block;
    std::vector<std::vector<Instruction>> split_code;
};

class Pattern_Replace{
    public:
    Pattern_Replace(std::string output_path):_output_path(output_path){}
    ~Pattern_Replace() {}
    void find_pattern_type(Search_Result &res);
    void file_replace(std::vector<std::string> &source);
    bool load_alu_str(Instruction ins1,Instruction ins2,Instruction ins3);
    bool load_alu_load(Instruction ins1,Instruction ins2,Instruction ins3);
    private:
    std::string _output_path;
    std::vector<std::vector<int>> realPattern;
    std::vector<std::vector<std::string>> realOplist;
    std::vector<std::string> patternType;
};
