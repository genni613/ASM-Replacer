# ASM-Modify
## 使用方法
1、编译程序，安装依赖项
```bash
make
```
2、将res.txt(修改后的指令)和希望修改的elf文件放置该目录下

3、执行如下命令
```bash
./run.sh $input_file $input_elf
```
例：./run.sh res.txt gcc_base.gcc43-64bit

