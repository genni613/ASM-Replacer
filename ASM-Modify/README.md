# ASM-Modify
## 使用方法
1、编译程序，安装依赖项
```bash
make
```
2、将res.txt(修改后的指令)和希望修改的elf文件放置该目录下

3、执行如下命令
```bash
./run.sh res.txt
```
注：可在run.sh中修改目标elf文件，例：gcc_base.gcc43-64bit

./patch-elf-bfd gcc_base.gcc43-64bit w --addr $add1 $add2
