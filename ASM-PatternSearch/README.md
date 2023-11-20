# ASM-PatternSearch
## 使用方法
1. 输入make编译
2. 输入 ./test asm文件路径， 生成raw.txt（不包含memcpy,memset）
3. 输入python modify-mem.py $input_asm，生成raw.txt（包含memcpy,memset）
* 如：python modify-mem.py gcc_base.gcc43-64bit-raw.asm 

