#include "inst_replacer.h"


File_Process::File_Process(std::string asm_path, std::string output_path)
        :_asm_path(asm_path), _output_path(output_path){
        std::ifstream ifs;
        std::ofstream ofs;
        ifs.open(asm_path,std::ios::in) ;
        if (!ifs.is_open()) {
            std::cout << "文件打开失败" << std::endl;
        }
        std::string codeline;
        while(getline(ifs,codeline)){
            if(codeline==".Ldebug_info0:")
            {
                break;
            }

            source.push_back(codeline);
        }
        ifs.close();
        //  std::cout<<source.size()<<std::endl;
        }


Pattern_Search::Pattern_Search(std::vector<std::string> &source,std::vector<std::string> &pc,std::vector<std::string> &ins){
        split_by_basicblock(source, pc, ins);
        preprocess();
}


void Pattern_Search::split_by_basicblock(std::vector<std::string> &source,std::vector<std::string> &pc,std::vector<std::string> &ins){
    std::string codeline;
    std::vector<std::string> code;
    for(int i = 0; i <source.size();i++)
    {
        codeline = source[i];
        int p1 = 0;
        int p2 = codeline.size();
        while(codeline[p1]=='\t') p1++;
        while(codeline[p2]=='\t') p2--;
        // p2 = p1++;
        // codeline = regex_replace(codeline, regex("^\\s+"), "");
	    // codeline = regex_replace(codeline, regex("\\s+$"), "");  
        code.push_back(codeline.substr(p1, p2-p1));
        // cout<<codeline.substr(p1, p2-p1+1)<<endl;
    }
    // cout<<code[18][code[18].size()-1]<<endl;
    
    for(int i = 0;i < code.size();i++)
    {
        int len = code[i].length();
        
        if(code[i][len-1]==':'||code[i][0] == 'b')
        {
            
            std::vector<std::string> block;
            std::vector<std::string> number;
            std::vector<std::string> ins_b;
            for(int j =i+1;j<code.size();j++)
            {
                len = code[j].size();
                if(code[j][len-1]==':')
                {
                    basic_block.push_back(block);
                    line_number.push_back(number);
                    ins_block.push_back(ins_b);
                    i=j-1;
                    break;
                }
                else if(j==code.size()-1){
                    block.push_back(code[j]);
                    number.push_back(pc[j]);
                    ins_b.push_back(ins[j]);
                    basic_block.push_back(block);
                    line_number.push_back(number);
                    ins_block.push_back(ins_b);
                    i=j-1;
                    break;
                }
                else{
                    if(code[j].size()>0)
                    {
                        block.push_back(code[j]);
                        number.push_back(pc[j]);
                        ins_b.push_back(ins[j]);
                    }
                    
                }
                   
            }
            block.clear();
            number.clear();
            ins_b.clear();
        }
    }
    // std::cout<<basic_block.size()<<std::endl;
}

void Pattern_Search::preprocess(){
    std::vector<std::tuple<std::string, std::string, std::string, std::string,int>> r_code;
    std::vector<std::string> tmp;
    std::vector<Instruction> instruction;
    Instruction ins;
    for(int i = 0; i < basic_block.size(); i++)
    {
        for(int j = 0 ;j < basic_block[i].size(); j++)
        {
            std::string tmp = basic_block[i][j];
            if(tmp[0]=='.')
            {
                continue;
            }
            else
            {
                
                std::vector<std::string> tmp_line={"None","None","None","None"};
                int pos = 0;
                int pos2 = 0;
                int len = tmp.size();
                pos2 = tmp.find("\t", pos);
               
                if(pos2 == -1){
                    // v.push_back(tmp);
                    ins.op = tmp;
                }
                else
                {
                    //  cout<<tmp<<endl;
                    // cout<<pos2<<endl;
                    // cout<<tmp.substr(pos, pos2 - pos)<<endl;
                    // ins.pos =  line_number[i][j];
                    ins.op = tmp.substr(pos, pos2 - pos);
                    ins.s_code =  basic_block[i][j];
                    ins.pc = line_number[i][j];
                    ins.bin = ins_block[i][j];
                    // v.push_back(tmp.substr(pos, pos2 - pos));
                    // cout<<"bbb"<<endl;
                    pos = pos2 + 1;
                    // cout<<tmp<<endl;
                    while (pos < len) {
                        // cout<<"aaa"<<endl;
                        pos2 = tmp.find(",", pos);
                        // cout<<"bbb"<<endl;
                        if(pos2 == -1) 
                            pos2 = len;
                        // cout<<"ccc"<<endl;
                        if(tmp[pos]==' ')
                            pos++;
                        // cout<<"ddd"<<endl;
                        if(tmp[pos]=='[')
                        {
                            // cout<<pos2<<endl;
                            // cout<<tmp[pos2]<<endl;
                            if(tmp[pos2-1] != ']'){
                                while(tmp[pos2]!=']'){
                                    pos2++;
                                }
                                pos2++;
                            }
                                
                            
                        }
                        // cout<<"eee"<<endl;
                        // v.push_back(tmp.substr(pos, pos2 - pos));
                        ins.operand.push_back(tmp.substr(pos, pos2 - pos));
                        // cout<<"fff"<<endl;
                        pos = pos2 + 1;
                        // cout<<"ccc"<<endl;
                    }
                    // cout<<"eee"<<endl;
                }
                instruction.push_back(ins);
                // for(int l = 0 ; l < ins.operand.size(); l++){
                //     std::cout<<ins.operand[l]<<std::endl;
                // }
                ins.clear();
                // if(v.size()==0)
                // for(int k=0;k<v.size();k++)
                    // cout<<v.size()<<endl;
                
                // for(int k = 0; k <v.size();k++)
                // {
                //     if(k == 4) break;
                //     tmp_line[k] = v[k];
                // }
                // v.clear();
                // r_code.push_back(make_tuple(tmp_line[0],tmp_line[1],tmp_line[2],tmp_line[3],line_number[i][j]));
                // cout<<line_number[i][j]<<endl;
                // cout<<tmp_line[0]<<endl;
                // cout<<get<0>(r_code[0])<<endl;
            }
        }
        split_code.push_back(instruction);
        instruction.clear();
    }

        for(int i = 0; i < split_code.size(); i++){
            for(int j = 0; j < split_code[i].size(); j++){
                for(int k = 0; k < split_code[i][j].operand.size(); k++){
                    getOperand(tmp, split_code[i][j].operand[k]);
                }
                split_code[i][j].operand = tmp;
                tmp.clear();
            }
        }

    // std::cout<<split_code.size()<<std::endl;
}
// void Pattern_Search::confict(){

// }
Search_Result Pattern_Search::find_continuous_pattern(){
    Search_Result res;
    int flag1=0;
    int flag2=0;
    int i0,i1,i2;

    // std::vector<std::string> ii1,ii2,ii3;
    // std::cout<<split_code[0].size()<<std::endl;
    for(auto &r_code : split_code){
        for(int i = 0; i <r_code.size(); ++i){
        flag1=0;
        flag2=0;
        // std::cout<<r_code.size()<<std::endl; 
        // std::cout<<r_code[i].op<<std::endl;
        // if(std::get<0>(r_code[i])=="add"||std::get<0>(r_code[i])=="sub"||std::get<0>(r_code[i])=="and"
        //     ||std::get<0>(r_code[i])=="or"||std::get<0>(r_code[i])=="xor")
        if(r_code[i].op =="add"||r_code[i].op =="sub"||r_code[i].op =="or"||r_code[i].op =="and"||r_code[i].op =="xor")
        {   
             
            // i1=std::get<4>(r_code[i]);     
            i1 = r_code[i].pos;      
            if(i-1>=0&&is_relate(r_code[i], r_code[i-1])&&r_code[i-1].op=="ldr"){
               
                flag1=1;
                i0=r_code[i-1].pos;
                 
            } 
            else{
                flag1=0;
            }
            //  std::cout<<is_relate(r_code[i], r_code[i+1])<<std::endl; 
            if(i+1<r_code.size()&&is_relate(r_code[i], r_code[i+1]) && r_code[i+1].op=="str"){
                //  cout<<"ddd"<<endl;
                flag2=1;
                i2=r_code[i+1].pos;
            }
            else{
                //  cout<<"fff"<<endl;
                flag2=0;
            }
            // cout<<"aaa"<<endl;
            // std::cout<<"bbb"<<std::endl; 
            if(flag1==1&&flag2==1)
            {
               
                res.ins.push_back(r_code[i-1]);
                res.ins.push_back(r_code[i]);
                res.ins.push_back(r_code[i+1]);
                
                // res.pattern_pos.push_back({i0,i1,i2});
            }
            
        }
    //     // else if()
    }
    }
    
   
   
    return res;

    // return pattern_pos;
}



Search_Result Pattern_Search::find_discontinuous_pattern(){
    Search_Result res;
    int flag1=0;
    int flag2=0;
    // int i0,i1,i2;
    int pos1, pos2;

    std::vector<std::string> ii1,ii2,ii3;
    // std::cout<<split_code[0].size()<<std::endl;
    for(auto &r_code : split_code){
        for(int i = 0; i <r_code.size(); ++i){
        flag1=0;
        flag2=0;
        // std::cout<<std::get<0>(r_code[i])<<std::endl;
        // if(std::get<0>(r_code[i])=="add"||std::get<0>(r_code[i])=="sub"||std::get<0>(r_code[i])=="and"
        //     ||std::get<0>(r_code[i])=="or"||std::get<0>(r_code[i])=="xor")
        if(r_code[i].op =="add"||r_code[i].op =="sub"||r_code[i].op =="or"||r_code[i].op =="and"||r_code[i].op =="xor")
        {   
             
            // i1 = r_code[i].pos;  
            for(int j = i-1; j >=0; --j)
            {
                if(r_code[j].op[0]=='b'||r_code[j].op == "str"
                    ||(is_relate(r_code[i], r_code[j])&&r_code[j].op != "ldr")){
                    flag1 = 0;
                    break;
                }

                // if(is_relate(r_code[i], r_code[j]))
                if(r_code[j].op=="ldr")
                {
                    // errs()<<flag1<<"\n";
                    if(is_relate(r_code[i], r_code[j]))
                    {
                        flag1=1;
                        // i0=r_code[j].pos;
                        pos1 = j;
                        break;
                    }
                        
                    else
                    {
                        flag1=0;
                        break;
                    }
                }
                
            }       
            // if(i-1>=0&&is_relate(r_code[i], r_code[i-1],ii1, ii2)&&std::get<0>(r_code[i-1])=="ldr"){
               
            //     flag1=1;
            //     i0=std::get<4>(r_code[i-1]);
                 
            // } 
            // else{
            //     flag1=0;
            // }
            

            for(int j = i+1; j <r_code.size(); ++j)
            {
                if(r_code[j].op[0]=='b'||r_code[j].op == "ldr"
                ||(is_relate(r_code[i], r_code[j])&&r_code[j].op != "str")){
                    flag2 = 0;
                    break;
                }
                if(r_code[j].op=="str")
                {
                     
                    if(is_relate(r_code[i], r_code[j]))
                    {
                        flag2=1;
                        // i2=r_code[j].pos;
                        pos2 = j;
                        break;
                    }
                        
                    else
                    {
                        flag2=0;
                        break;
                    }
                }
                
            }
            // if(i+1<r_code.size()&&is_relate(r_code[i], r_code[i+1], ii1, ii3) && std::get<0>(r_code[i+1])=="str"){
            //     //  cout<<"ddd"<<endl;
            //     flag2=1;
            //     i2=std::get<4>(r_code[i+1]);
            // }
            // else{
            //     //  cout<<"fff"<<endl;
            //     flag2=0;
            // }
            // cout<<"aaa"<<endl;
            if(flag1==1&&flag2==1)
            {
                bool flag3 = 1;
                bool flag4 = 0;
                std::string ch = r_code[pos1].operand[0];
                for(int j = pos2+1; j <r_code.size(); j++){
                    if(r_code[j].op[0] = 'b') break;
                    for(int k = 0; k < r_code[j].operand.size(); k++){
                        if(ch == r_code[j].operand[k]){
                            if(r_code[j].op == "ldr"&&ch == r_code[j].operand[0]){
                                flag4 = 1;
                                break;
                            }
                            else{
                                flag3 = 0;
                                flag4 = 1;
                                break;
                            }
                        }
                            
                    }
                    if(flag4)
                        break;
                    
                }
                // std::cout<<"aa"<<std::endl;
                if(flag3==1){
                    res.ins.push_back(r_code[pos1]);
                    res.ins.push_back(r_code[i]);
                    res.ins.push_back(r_code[pos2]);
                }
                
            }
            
        }
    //     // else if()
    }
    }
    
   
   
    return res;

    // return pattern_pos;
}

bool Pattern_Search::is_relate(Instruction &i1, Instruction &i2)
{
    // ii1.clear();
    // ii2.clear();
    // // cout<<get<1>(i1)<<endl;
   
    // getOperand(ii1, std::get<1>(i1));
    // getOperand(ii1, std::get<2>(i1));
    // getOperand(ii1, std::get<3>(i1));
    // getOperand(ii2, std::get<1>(i2));
    // getOperand(ii2, std::get<2>(i2));
    // getOperand(ii2, std::get<3>(i2));
    // operandCheck(ii1);
    // operandCheck(ii2);
    // cout<<"vvv"<<endl;

    // for(auto &s: ii2)
    //     cout<<s<<endl;
    // ii1.push_back( get<1>(i1));
    // ii1.push_back(get<2>(i1));
    // ii1.push_back(get<3>(i1));
    // ii2.push_back(get<1>(i2));
    // ii2.push_back(get<2>(i2));
    // ii2.push_back(get<3>(i2));
    // cout<<ii1.size()<<endl;
    // cout<<ii2.size()<<endl;
    for(int i = 0; i< i1.operand.size();i++)
    {
        //  cout<<"aaa"<<endl;
        if(i1.operand[i]=="None")
        {
            continue;
        }
        else
        {
            std::string lr = i1.operand[i];
            for(int j = 0; j< i2.operand.size();j++)
            {
                 if(i2.operand[j]=="None"){
                    continue;
                }
                else{
                    std::string rr= i2.operand[j];
                    if(lr == rr){
                        return true;
                    }
                }   
            }  
        }   
    }
    // cout<<"zzz"<<endl;
    // if(cast<Value>(i1)==i2->getOperand(0))
    //     return true;
    return false;
}

void Pattern_Search::getOperand(std::vector<std::string> &str, std::string reg){
    int pos = 0;
    int pos2 = 0;
    int len = reg.size();
    if(reg[0] == '['){
        pos = 1;
        while (pos < len) {
            // cout<<"aaa"<<endl;
            pos2 = reg.find(",", pos);
            // cout<<"bbb"<<endl;
            if(pos2 == -1) 
                pos2 = len-1;
            // cout<<"ccc"<<endl;
            if(reg[pos]==' ')
                pos++;
            // cout<<"ddd"<<endl;
            // cout<<"eee"<<endl;
            str.push_back(reg.substr(pos, pos2 - pos));
            // cout<<"fff"<<endl;
            pos = pos2 + 1;
            // cout<<"ccc"<<endl;
        }
    }
    else
        str.push_back(reg);
    
}

void Pattern_Search::operandCheck(std::vector<std::string> &str){
    for(int i = 0; i < str.size(); i++){
        // if(str[i][0] == 'l'){
        //     str.erase(str.begin()+i);
        //     i--;
        // }
        if(str[i][0] == 'w')
            str[i][0] = 'x';
            
    }
}

bool Pattern_Replace::load_alu_str(Instruction ins1,Instruction ins2,Instruction ins3){    
    if((ins1.operand[0] == ins2.operand[1]||ins1.operand[0] == ins2.operand[2])&&ins2.operand[0] == ins3.operand[0]){
            if(ins1.operand.size() == ins3.operand.size()){
            // if(ins1.operand.size() == ins3.operand.size()&&(ins2.operand[2][0]=='x'||ins2.operand[2][0]=='w')&&ins2.operand.size()<=3&&(ins1.operand[1][0]=='x'||ins1.operand[1][0]=='w')){    
                if(ins1.operand.size() == 3 && ins1.operand[2] == ins3.operand[2])
                    patternType.push_back("padd1");
                else if (ins1.operand.size() == 4 && ins1.operand[3] == ins3.operand[3])
                    patternType.push_back("padd1+lsl");
                else
                    return false;
                realPattern.push_back({ins1.pos,ins2.pos,ins3.pos});
                realOplist.push_back(ins1.operand);
                realOplist.push_back(ins2.operand);
                realOplist.push_back(ins3.operand);
            }
    }
    
    
    return true;
}

bool Pattern_Replace::load_alu_load(Instruction ins1,Instruction ins2,Instruction ins3){
    // std::cout<<ins1.operand[0]<<std::endl;
     if((ins1.operand[0] == ins2.operand[1]||ins1.operand[0] == ins2.operand[2])&&ins2.operand[0] == ins3.operand[1]){
            if(ins1.operand.size() == ins3.operand.size()&&(ins2.operand[2][0]=='x'||ins2.operand[2][0]=='w')&&ins2.operand.size()<=3&&(ins1.operand[1][0]=='x'||ins1.operand[1][0]=='w')){
                patternType.push_back("plats");
                realPattern.push_back({ins1.pos,ins2.pos,ins3.pos});
                realOplist.push_back(ins1.operand);
                realOplist.push_back(ins2.operand);
                realOplist.push_back(ins3.operand);
            }
    }
    return true;
}


void Pattern_Replace::find_pattern_type(Search_Result &res){
     std::cout<<res.ins.size()<<std::endl;
// std::cout<<"aaa"<<std::endl;
    for(int i = 0; i< res.ins.size(); i=i+3){
    // cout<<i<<endl;
    
       load_alu_str(res.ins[i], res.ins[i+1], res.ins[i+2]);    // cout<<"aa"<<endl;  
    //    load_alu_load(res.ins[i], res.ins[i+1], res.ins[i+2]);      
    }
     std::cout<<realPattern.size()<<std::endl;
    //  for(auto &s : realOplist){
    //     for(auto &a : s){
    //         std::cout<<a<<" ";
    //     }
    //     std::cout<<""<<std::endl;
    //  }
}



void Pattern_Replace::file_replace(std::vector<std::string> &source){
    std::ofstream ofs;
    ofs.open(_output_path, std::ios::out);
    if (!ofs.is_open()) {
        std::cout << "文件打开失败" << std::endl;
    }
    std::string newinst;
    
    for(int i = 0; i < realPattern.size();i++)
    {
         std::cout<<source[realPattern[i][0]]<<std::endl; 
         std::cout<<source[realPattern[i][1]]<<std::endl; 
         std::cout<<source[realPattern[i][2]]<<std::endl; 
         std::cout<<" "<<std::endl; 
    }
    // std::cout<<"aaaaaaaaaa"<<std::endl;

    for(int i = 0; i < realPattern.size();i++)
    {
        // std::cout<<"aa"<<std::endl; 
        std::vector<int> pos = realPattern[i];
        // std::cout<<"aa"<<std::endl; 
        source.erase(begin(source)+pos[0]-2*i);
        source.erase(begin(source)+pos[1]-1-2*i);
        source.erase(begin(source)+pos[2]-2-2*i);
        // std::cout<<realOplist[3*i][1]<<std::endl; 
        if(patternType[i] == "padd1+lsl")
            newinst = "\tpadd1 " + realOplist[3*i + 1][2] + ", ["+realOplist[3*i][1] + ", "+realOplist[3*i][2]+ ", "+realOplist[3*i][3] +"]";
        else if(patternType[i] == "padd1")
             newinst = "\tpadd1 " + realOplist[3*i + 1][2] + ", ["+realOplist[3*i][1] + ", "+realOplist[3*i][2]+"]";
        else if(patternType[i] == "plats")
             newinst ="\tplats " + realOplist[3*i + 1][2] + ", " +realOplist[3*i][1]+ ", " + realOplist[3*i+2][0];

        std::cout<<newinst<<std::endl;
        // std::cout<<"aa"<<std::endl;
        source.insert(begin(source)+pos[0]-2*i, newinst);
    }
    
     for(int i = 0; i < source.size(); i++){
        ofs<<source[i]<<std::endl;
    }
    ofs.close();
}
