# ASM-Tansfer
## 使用方法
1、注入依赖
```bash
apt-get install llvm
```

2、将ASM-PatternSearch部分生成的raw.txt（需要修改的原始指令）文件放置该目录下

3、执行如下语句，生成res.txt（修改后的指令）
```bash
python asm-transfer.py
```
