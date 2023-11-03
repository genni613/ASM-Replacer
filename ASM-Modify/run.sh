#!/bin/bash

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 input_file"
  exit 1
fi

input_file="$1"
line_count=$(wc -l < "$input_file")

for ((i=1; i<=line_count; i++))
do
  # 读取文件的第i行，获取add1和add2的值
  line=$(sed -n "${i}p" "$input_file")
  add1=$(echo "$line" | cut -d ' ' -f 1)
  add2=$(echo "$line" | cut -d ' ' -f 2)
  # echo "add1:$add1 add2:$add2"
  ./patch-elf-bfd gcc_base.gcc43-64bit w --addr $add1 $add2
  
done

