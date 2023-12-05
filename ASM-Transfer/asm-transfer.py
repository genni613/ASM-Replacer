import re
import os
import binascii

REG = r"(?:[xw](?:\d+|zr)|sp)"
WHITE = r"[ \t]*"
IMM = r"(?:#?(?:0x)?[0-9a-fA-F]+)"

# ext："lsl"等
# amount "3" 等
EXTEND = {"uxtw": 0b010, "lsl": 0b011, "sxtw": 0b110, "sxtx": 0b111}
AMOUNT = {0: 0, 2: 1, 3: 1}
def encode_shift(ext:str, amount:str):
	if (not ext or not amount): return 0
	return (EXTEND[ext] << 13) | (AMOUNT[int(amount)] << 12)

# rm: "x3"、"w4"等
REGENC = {"xzr": 31, "wzr": 31, "sp": 31, 'w0': 0, 'x0': 0, 'w1': 1, 'x1': 1, 'w2': 2, 'x2': 2, 'w3': 3, 'x3': 3, 'w4': 4, 'x4': 4, 'w5': 5, 'x5': 5, 'w6': 6, 'x6': 6, 'w7': 7, 'x7': 7, 'w8': 8, 'x8': 8, 'w9': 9, 'x9': 9, 'w10': 10, 'x10': 10, 'w11': 11, 'x11': 11, 'w12': 12, 'x12': 12, 'w13': 13, 'x13': 13, 'w14': 14, 'x14': 14, 'w15': 15, 'x15': 15, 'w16': 16, 'x16': 16, 'w17': 17, 'x17': 17, 'w18': 18, 'x18': 18, 'w19': 19, 'x19': 19, 'w20': 20, 'x20': 20, 'w21': 21, 'x21': 21, 'w22': 22, 'x22': 22, 'w23': 23, 'x23': 23, 'w24': 24, 'x24': 24, 'w25': 25, 'x25': 25, 'w26': 26, 'x26': 26, 'w27': 27, 'x27': 27, 'w28': 28, 'x28': 28, 'w29': 29, 'x29': 29, 'w30': 30, 'x30': 30, 'w31': 31, 'x31': 31}
def encode_regs(rm:str, rn:str, rt:str):
	if not rm: rm = "xzr"
	rm = REGENC[rm] << 16
	rn = REGENC[rn] << 5
	rt = REGENC[rt]
	return rm | rn | rt

def encode_reg_imms(imm:int, rn:str, rt:str):
	assert imm & 1 == 0, "imm in padd1 must be even"
	imm = (imm >> 1) << 10
	rn = REGENC[rn] << 5
	rt = REGENC[rt]
	return imm | rn | rt

malu12regpat = re.compile(f'(p(?:add|sub|or|xor|and)[12]){WHITE}({REG}){WHITE},{WHITE}\[{WHITE}({REG}){WHITE}(?:,{WHITE}({REG}))?{WHITE}(?:,{WHITE}(uxtw|lsl|sxtw|sxtx){WHITE}#?(0|2|3))?{WHITE}\]')
malu1immpat = re.compile(f'(p(?:add|sub|or|xor|and)1){WHITE}({REG}){WHITE},{WHITE}\[{WHITE}({REG}){WHITE},{WHITE}({IMM}){WHITE}\]')
# movpat = re.compile(f'mov{WHITE}({REG}){WHITE},{WHITE}({IMM})')

malu12_reg_base = {
	"padd1": 0x2000000,
	"psub1": 0x2200000,
	"pand1": 0x2400000,
	"por1":  0x2600000,
	"pxor1": 0x2800000,
	"padd2": 0x3000000,
	"psub2": 0x3200000,
	"pand2": 0x3400000,
	"por2":  0x3600000,
	"pxor2": 0x3800000,
}

malu1_imm_base = {
	"padd1": 0x22000000,
	"psub1": 0x22200000,
	"pand1": 0x22400000,
	"por1":  0x22600000,
	"pxor1": 0x22800000,
}

plats_regpat = re.compile(f'plats{WHITE}({REG}){WHITE},{WHITE}({REG}){WHITE},{WHITE}({REG}){WHITE}')
plats_reg_base = 0xe2200000

pll_regpat = re.compile(f'pll{WHITE}({REG}){WHITE},{WHITE}({REG}){WHITE},{WHITE}({REG}){WHITE}')
pll_reg_base = 0x8c000000

# 要使用此函数，先安装llvm，apt install llvm
def llvm_asm(row):
	import subprocess
	try:
		# 调用 llvm-mc 来获取机器码
		completed_process = subprocess.run(
			["llvm-mc", "-triple=aarch64-none-elf", "-assemble", "-show-encoding"],
			input=row,
			text=True,
			capture_output=True
		)
        
        # 提取输出中的机器码部分
		output = completed_process.stdout
		encoded_bytes = output.split("encoding: [")[1].split("]")[0].split(",")
				
		# 将字节列表转换为单个16进制数
		encoded_hex = "".join(reversed([e[2:] for e in encoded_bytes]))
				
		# 将16进制数转换为整数
		machine_code = int(encoded_hex, 16)
				
		return machine_code
	except Exception as e:
		return None


def assemble(row):
	if (row.strip().startswith("padd") or row.strip().startswith("psub") or row.strip().startswith("pand") or row.strip().startswith("por") or row.strip().startswith("pxor")):
		reglist = re.findall(malu12regpat, row)
		if reglist:
			inst = malu12_reg_base[reglist[0][0]]
			rm = reglist[0][3]
			rn = reglist[0][2]
			rt = reglist[0][1]
			extend = reglist[0][4]
			amount = reglist[0][5]
			size = (1 if rt[0] == 'x' else 0) << 30

			inst |= encode_regs(rm, rn, rt)
			inst |= size
			inst |= encode_shift(extend, amount)
			return inst
		else:
			reglist = re.findall(malu1immpat, row)
			if reglist:
				inst = malu1_imm_base[reglist[0][0]]
				rn = reglist[0][2]
				rt = reglist[0][1]
				imm = reglist[0][3]
				if imm[0] == "#": imm = imm[1:]
				imm = int(imm, 0)
				size = (1 if rt[0] == 'x' else 0) << 30

				inst |= encode_reg_imms(imm, rn, rt)
				inst |= size
				return inst
	elif row.strip().startswith("plats"):
		reglist = re.findall(plats_regpat, row)
		inst = plats_reg_base
		rt = reglist[0][2]
		rn = reglist[0][1]
		rm = reglist[0][0]

		inst |= encode_regs(rm, rn, rt)
		return inst
	elif row.strip().startswith("pll"):
		reglist = re.findall(pll_regpat, row)
		inst = pll_reg_base
		rt = reglist[0][2]
		rn = reglist[0][1]
		rm = reglist[0][0]

		inst |= encode_regs(rm, rn, rt)
		return inst
	elif row.strip().startswith("mov") or row.strip().startswith("add"):
		return llvm_asm(row)
	elif row.strip().startswith("nop"):
		return 0xd503201f
	else:
		return None
# 修改指令
def modify_instructions_malu1(input_filename, output_filename):
    with open(input_filename, 'r') as infile:
        lines = infile.readlines()
    
    output_lines = []
    count = 3
    for i, line in enumerate(lines):
        check = 0
        parts = line.strip().split()
        if count % 3 == 0:
            if len(parts) == 5:
                reg_val = " ".join(parts[-1:])
                # print(reg_val)
            elif len(parts) == 6:
                reg_val = " ".join(parts[-2:])
                # print(reg_val)
        if re.search(r'\badd\b', line):
            if len(parts)>3:
                reg = parts[3].split(',')[0]
                # print(reg)
                # print(parts)
            else:
                continue
            immediate = parts[-1]
            if 'add' in line and '#' in line:
                # 替换上一条指令为mov指令
                mov_instruction = "{} {} mov {},{}\n".format(parts[0], parts[1], reg, immediate)
                output_lines[-1] = mov_instruction
                # print(output_lines[-1])
                # 修改add指令为padd1指令
                padd1_instruction = "{} {} padd1 {},{}\n".format(parts[0],parts[1], reg, reg_val)
                output_lines.append(padd1_instruction)
                # print(output_lines)
                check = 1
                    
            # 提取add指令的寄存器和立即数
            if check == 0:
                reg = parts[3].split(',')[0]
                notimmediate = parts[-1]
                first_reg = parts[3].replace(',', '')
                second_reg = parts[4].replace(',', '')
                if (first_reg != second_reg):
                    notimmediate=first_reg
                    padd1_instruction = "{} {} padd1 {},{}\n".format(parts[0], parts[1], notimmediate, reg_val)
                    output_lines[-1] = padd1_instruction
                    nop_instruction = "{} {} nop\n".format(parts[0], parts[1])
                    output_lines.append(nop_instruction)
                    # print(output_lines)
                else:
                    padd1_instruction = "{} {} padd1 {},{}\n".format(parts[0], parts[1], notimmediate, reg_val)
                    output_lines[-1] = padd1_instruction
                    nop_instruction = "{} {} nop\n".format(parts[0], parts[1])
                    output_lines.append(nop_instruction)
                    # print(output_lines)

            # 添加一个nop指令
            # nop_instruction = "{:<9} {:<8}nop\n".format(hex(int(parts[0], 16) + 8)[2:], parts[1])
            # output_lines.append(nop_instruction)
        elif re.search(r'\bsub\b', line):
            if len(parts)>3:
                reg = parts[3].split(',')[0]
            else:
                continue
            immediate = parts[-1]
            if 'sub' in line and '#' in line:
                # 替换上一条指令为mov指令
                mov_instruction = "{} {} mov {},{}\n".format(parts[0], parts[1], reg, immediate)
                output_lines[-1] = mov_instruction
                
                # 修改sub指令为psub1指令
                padd1_instruction = "{} {} psub1 {},{}\n".format(parts[0],parts[1], reg, reg_val)
                output_lines.append(padd1_instruction)
                check = 1
            # 提取sub指令的寄存器和立即数
            if check == 0:
                reg = parts[3].split(',')[0]
                notimmediate = parts[-1]
                first_reg = parts[3].replace(',', '')
                second_reg = parts[4].replace(',', '')
                if (first_reg != second_reg):
                    notimmediate=first_reg
                    padd1_instruction = "{} {} psub1 {},{}\n".format(parts[0], parts[1], notimmediate, reg_val)
                    output_lines[-1] = padd1_instruction
                    nop_instruction = "{} {} nop\n".format(parts[0], parts[1])
                    output_lines.append(nop_instruction)
                else:
                    padd1_instruction = "{} {} psub1 {},{}\n".format(parts[0], parts[1], notimmediate, reg_val)
                    output_lines[-1] = padd1_instruction
                    nop_instruction = "{} {} nop\n".format(parts[0], parts[1])
                    output_lines.append(nop_instruction)
        elif re.search(r'\band\b', line):
            if len(parts)>3:
                reg = parts[3].split(',')[0]
            else:
                continue
            immediate = parts[-1]
            if 'and' in line and '#' in line:
                # 替换上一条指令为mov指令
                mov_instruction = "{} {} mov {},{}\n".format(parts[0], parts[1], reg, immediate)
                output_lines[-1] = mov_instruction
                # print(output_lines[-1])
                # 修改and指令为pand1指令
                padd1_instruction = "{} {} pand1 {},{}\n".format(parts[0],parts[1], reg, reg_val)
                # print(padd1_instruction)
                output_lines.append(padd1_instruction)
                # print(output_lines)
                check = 1
            # 提取and指令的寄存器和立即数
            if check == 0:
                reg = parts[3].split(',')[0]
                notimmediate = parts[-1]
                first_reg = parts[3].replace(',', '')
                second_reg = parts[4].replace(',', '')
                if (first_reg != second_reg):
                    notimmediate=first_reg
                    padd1_instruction = "{} {} pand1 {},{}\n".format(parts[0], parts[1], notimmediate, reg_val)
                    output_lines[-1] = padd1_instruction
                    nop_instruction = "{} {} nop\n".format(parts[0], parts[1])
                    output_lines.append(nop_instruction)
                else:
                    padd1_instruction = "{} {} pand1 {},{}\n".format(parts[0], parts[1], notimmediate, reg_val)
                    output_lines[-1] = padd1_instruction
                    # print(output_lines[-1])
                    nop_instruction = "{} {} nop\n".format(parts[0], parts[1])
                    output_lines.append(nop_instruction)
        elif re.search(r'\bor\b', line):
            if len(parts)>3:
                reg = parts[3].split(',')[0]
            else:
                continue
            immediate = parts[-1]
            if 'or' in line and '#' in line:
                # 替换上一条指令为mov指令
                mov_instruction = "{} {} mov {},{}\n".format(parts[0], parts[1], reg, immediate)
                output_lines[-1] = mov_instruction
                
                # 修改or指令为por1指令
                padd1_instruction = "{} {} por1 {},{}\n".format(parts[0],parts[1], reg, reg_val)
                output_lines.append(padd1_instruction)
                check = 1
            # 提取or指令的寄存器和立即数
            if check == 0:
                reg = parts[3].split(',')[0]
                notimmediate = parts[-1]
                first_reg = parts[3].replace(',', '')
                second_reg = parts[4].replace(',', '')
                if (first_reg != second_reg):
                    notimmediate=first_reg
                    padd1_instruction = "{} {} por1 {},{}\n".format(parts[0], parts[1], notimmediate, reg_val)
                    output_lines[-1] = padd1_instruction
                    nop_instruction = "{} {} nop\n".format(parts[0], parts[1])
                    output_lines.append(nop_instruction)
                else:
                    padd1_instruction = "{} {} por1 {},{}\n".format(parts[0], parts[1], notimmediate, reg_val)
                    output_lines[-1] = padd1_instruction
                    nop_instruction = "{} {} nop\n".format(parts[0], parts[1])
                    output_lines.append(nop_instruction)
        elif re.search(r'\bxor\b', line):
            if len(parts)>3:
                reg = parts[3].split(',')[0]
            else:
                continue
            immediate = parts[-1]
            if 'xor' in line and '#' in line:
                # 替换上一条指令为mov指令
                mov_instruction = "{} {} mov {},{}\n".format(parts[0], parts[1], reg, immediate)
                output_lines[-1] = mov_instruction
                
                # 修改or指令为pxor1指令
                padd1_instruction = "{} {} pxor1 {},{}\n".format(parts[0],parts[1], reg, reg_val)
                output_lines.append(padd1_instruction)
                check = 1
            # 提取xor指令的寄存器和立即数
            if check == 0:
                reg = parts[3].split(',')[0]
                notimmediate = parts[-1]
                first_reg = parts[3].replace(',', '')
                second_reg = parts[4].replace(',', '')
                if (first_reg != second_reg):
                    notimmediate=first_reg
                    padd1_instruction = "{} {} pxor1 {},{}\n".format(parts[0], parts[1], notimmediate, reg_val)
                    output_lines[-1] = padd1_instruction
                    nop_instruction = "{} {} nop\n".format(parts[0], parts[1])
                    output_lines.append(nop_instruction)
                else:
                    padd1_instruction = "{} {} pxor1 {},{}\n".format(parts[0], parts[1], notimmediate, reg_val)
                    output_lines[-1] = padd1_instruction
                    nop_instruction = "{} {} nop\n".format(parts[0], parts[1])
                    output_lines.append(nop_instruction)
        elif re.search(r'\bstr\b', line):
            # 对于str指令，只需输出一个nop指令
            nop_instruction = "{} {} nop\n".format(parts[0], parts[1])
            output_lines.append(nop_instruction)

        else:
            # 如果行不包含需要修改的add指令或str指令，原样写入
            output_lines.append(line)
        count += 1
        # print(output_lines)
    with open(output_filename, 'w') as outfile:
        outfile.writelines(output_lines)
    

def modify_instructions_malu2(input_filename, output_filename):
    with open(input_filename, 'r') as infile:
        lines = infile.readlines()
    
    output_lines = []
    for i in range(0, len(lines), 3):
        line=lines[i]
        next_line=lines[i+1]
    # for i, line in enumerate(lines):
        parts = line.strip().split()

        if i+1<len(lines):
            second_line = lines[i+1]
        if i+2<len(lines):
            third_line=lines[i+2]
        # print(parts)
        second_part=second_line.strip().split()
        #print("second_part:",second_part)
        third_part = third_line.strip().split()
        if 1:
            # 没有offset
            if len(parts) == 5:
                reg_addr1 = " ".join(parts[-1:]).strip('[]')
                reg_addr2 = " ".join(third_part[-1:]).strip('[]')
                reg_delta=" ".join(second_part[-1:]).strip('[]').strip(',')
                reg_val="["+reg_addr2+","+reg_addr1+"]"
                # reg_val = "["+reg_val1 + "," + reg_val2+"]"
                # print(reg_val)
            # 带有offset
            elif len(parts) == 6:
                reg_all= " ".join(parts[-2:]).strip('[]')
                reg_all2=" ".join(third_part[-2:]).strip('[]')
                reg_t1 = parts[3].split(',')[0]
                reg_t2=second_part[3].split(',')[0]
                reg_t=second_part[4].split(',')[0]

                reg_delta = " ".join(second_part[-1:]).strip('[]').strip(',')

                reg_addr2=" ".join(third_part[-1:]).strip('[]').strip(',')
                reg_arg2="["+reg_addr2+","+reg_t1+"]"
                reg_arg3="["+reg_t2+","+reg_t1+"]"
            if re.search(r'\bldr\b', line):
                if '#' in line and len(parts)==6 and len(third_part)==5 and re.search(r'\badd\b', next_line):
                    mov_instruction = "{} {} add {},{}\n".format(parts[0], parts[1],reg_t1, reg_all)
                    output_lines.append(mov_instruction)
                    # 修改add指令为padd1指令
                    padd1_instruction = "{} {} padd2 {},{}\n".format(second_part[0],second_part[1], reg_delta, reg_arg2)
                    output_lines.append(padd1_instruction)
                    nop_instruction = "{} {} nop\n".format(third_part[0], third_part[1])
                    output_lines.append(nop_instruction)
                    #print(output_lines)
                    # check = 1
                        
                # 提取add指令的寄存器和立即数
                elif len(parts)==5 and re.search(r'\badd\b|\bsub\b|\band\b|\bor\b|\bxor\b', next_line):
                    if 1:
                        #notimmediate=first_reg
                        padd1_instruction = "{} {} padd2 {},{}\n".format(parts[0], parts[1], reg_delta, reg_val)
                        output_lines.append(padd1_instruction)
                        nop_instruction = "{} {} nop\n".format(second_part[0], second_part[1])
                        output_lines.append(nop_instruction)
                        nop_instruction = "{} {} nop\n".format(third_part[0], third_part[1])
                        output_lines.append(nop_instruction)

                elif len(parts)==6 and '#' in line and len(third_part)==6 and re.search(r'\badd\b', next_line):
                    #print("success")
                    mov_instruction = "{} {} add {},{}\n".format(parts[0], parts[1],reg_t1, reg_all)
                    output_lines.append(mov_instruction)
                    mov_instruction = "{} {} add {},{}\n".format(second_part[0], second_part[1],reg_t2, reg_all2)
                    output_lines.append(mov_instruction)
                    mov_instruction = "{} {} padd2 {},{}\n".format(third_part[0], third_part[1],reg_t, reg_arg3)
                    output_lines.append(mov_instruction)

                elif '#' in line and len(parts)==6 and len(third_part)==5 and re.search(r'\bsub\b', next_line):
                    mov_instruction = "{} {} add {},{}\n".format(parts[0], parts[1],reg_t1, reg_all)
                    output_lines.append(mov_instruction)
                    # 修改add指令为padd1指令
                    padd1_instruction = "{} {} psub2 {},{}\n".format(second_part[0],second_part[1], reg_delta, reg_arg2)
                    output_lines.append(padd1_instruction)
                    nop_instruction = "{} {} nop\n".format(third_part[0], third_part[1])
                    output_lines.append(nop_instruction)

                elif len(parts)==6 and '#' in line and len(third_part)==6 and re.search(r'\bsub\b', next_line):
                    #print("success")
                    mov_instruction = "{} {} add {},{}\n".format(parts[0], parts[1],reg_t1, reg_all)
                    output_lines.append(mov_instruction)
                    mov_instruction = "{} {} add {},{}\n".format(second_part[0], second_part[1],reg_t2, reg_all2)
                    output_lines.append(mov_instruction)
                    mov_instruction = "{} {} psub2 {},{}\n".format(third_part[0], third_part[1],reg_t, reg_arg3)
                    output_lines.append(mov_instruction)

                elif '#' in line and len(parts)==6 and len(third_part)==5 and re.search(r'\band\b', next_line):
                    mov_instruction = "{} {} add {},{}\n".format(parts[0], parts[1],reg_t1, reg_all)
                    output_lines.append(mov_instruction)
                    # 修改add指令为padd1指令
                    padd1_instruction = "{} {} pand2 {},{}\n".format(second_part[0],second_part[1], reg_delta, reg_arg2)
                    output_lines.append(padd1_instruction)
                    nop_instruction = "{} {} nop\n".format(third_part[0], third_part[1])
                    output_lines.append(nop_instruction)

                elif len(parts)==6 and '#' in line and len(third_part)==6 and re.search(r'\band\b', next_line):
                    #print("success")
                    mov_instruction = "{} {} add {},{}\n".format(parts[0], parts[1],reg_t1, reg_all)
                    output_lines.append(mov_instruction)
                    mov_instruction = "{} {} add {},{}\n".format(second_part[0], second_part[1],reg_t2, reg_all2)
                    output_lines.append(mov_instruction)
                    mov_instruction = "{} {} pand2 {},{}\n".format(third_part[0], third_part[1],reg_t, reg_arg3)
                    output_lines.append(mov_instruction)

                elif '#' in line and len(parts)==6 and len(third_part)==5 and re.search(r'\bor\b', next_line):
                    mov_instruction = "{} {} add {},{}\n".format(parts[0], parts[1],reg_t1, reg_all)
                    output_lines.append(mov_instruction)
                    # 修改add指令为padd1指令
                    padd1_instruction = "{} {} por2 {},{}\n".format(second_part[0],second_part[1], reg_delta, reg_arg2)
                    output_lines.append(padd1_instruction)
                    nop_instruction = "{} {} nop\n".format(third_part[0], third_part[1])
                    output_lines.append(nop_instruction)

                elif len(parts)==6 and '#' in line and len(third_part)==6 and re.search(r'\bor\b', next_line):
                    #print("success")
                    mov_instruction = "{} {} add {},{}\n".format(parts[0], parts[1],reg_t1, reg_all)
                    output_lines.append(mov_instruction)
                    mov_instruction = "{} {} add {},{}\n".format(second_part[0], second_part[1],reg_t2, reg_all2)
                    output_lines.append(mov_instruction)
                    mov_instruction = "{} {} por2 {},{}\n".format(third_part[0], third_part[1],reg_t, reg_arg3)
                    output_lines.append(mov_instruction)

                elif '#' in line and len(parts)==6 and len(third_part)==5 and re.search(r'\bxor\b', next_line):
                    mov_instruction = "{} {} add {},{}\n".format(parts[0], parts[1],reg_t1, reg_all)
                    output_lines.append(mov_instruction)
                    # 修改add指令为padd1指令
                    padd1_instruction = "{} {} pxor2 {},{}\n".format(second_part[0],second_part[1], reg_delta, reg_arg2)
                    output_lines.append(padd1_instruction)
                    nop_instruction = "{} {} nop\n".format(third_part[0], third_part[1])
                    output_lines.append(nop_instruction)

                elif len(parts)==6 and '#' in line and len(third_part)==6 and re.search(r'\bxor\b', next_line):
                    #print("success")
                    mov_instruction = "{} {} add {},{}\n".format(parts[0], parts[1],reg_t1, reg_all)
                    output_lines.append(mov_instruction)
                    mov_instruction = "{} {} add {},{}\n".format(second_part[0], second_part[1],reg_t2, reg_all2)
                    output_lines.append(mov_instruction)
                    mov_instruction = "{} {} pxor2 {},{}\n".format(third_part[0], third_part[1],reg_t, reg_arg3)
                    output_lines.append(mov_instruction)
    with open(output_filename, 'w') as outfile:
        outfile.writelines(output_lines)
# plats
def modify_instructions_plats(input_filename, output_filename):
    with open(input_filename, 'r') as infile:
        lines = infile.readlines()
    
    output_lines = []
    count = 3
    for i in range(0, len(lines), 3):
        line=lines[i]
    # for i, line in enumerate(lines):
        check = 0
        parts = line.strip().split()

        if i+1<len(lines):
            second_line = lines[i+1]
        if i+2<len(lines):
            third_line=lines[i+2]
        # print(parts)
        second_part=second_line.strip().split()
        #print("second_part:",second_part)
        third_part = third_line.strip().split()
        if 1:
            # 没有offset
            if len(parts) == 5:
                reg_data = third_part[3].split(',')[0]
                reg_addr1 = " ".join(parts[-1:]).strip('[]')
                reg_addr2 = " ".join(third_part[-1:]).strip('[]')
                reg_delta=" ".join(second_part[-1:]).strip('[]').strip(',')
                reg_val="["+reg_addr2+","+reg_addr1+"]"
                # reg_val = "["+reg_val1 + "," + reg_val2+"]"
                # print(reg_val)
            # 带有offset
            elif len(parts) == 6:
                reg_data=third_part[3].split(',')[0]
                reg_all= " ".join(parts[-2:]).strip('[]')
                reg_all2=" ".join(third_part[-1:]).strip('[]')
                reg_t1 = parts[3].split(',')[0]
                reg_t2=second_part[3].split(',')[0]
                reg_t=second_part[4].split(',')[0]

                reg_delta = " ".join(second_part[-1:]).strip('[]').strip(',')

                reg_addr2=" ".join(third_part[-1:]).strip('[]').strip(',')
                reg_arg2="["+reg_addr2+","+reg_t1+"]"
                reg_arg3="["+reg_t2+","+reg_t1+"]"
            if re.search(r'\bldr\b', line):
                if '#' in line and len(parts)==6 and len(third_part)==6:

                    mov_instruction = "{} {} add {},{}\n".format(parts[0], parts[1],reg_t1, reg_all)
                    output_lines.append(mov_instruction)
                    # 修改add指令为padd1指令
                    padd1_instruction = "{} {} add {},{},{}\n".format(second_part[0],second_part[1], reg_t2, reg_delta, reg_addr2)
                    output_lines.append(padd1_instruction)
                    nop_instruction = "{} {} plats {},{}, {}\n".format(third_part[0], third_part[1], reg_data, reg_t1, reg_t2)
                    output_lines.append(nop_instruction)
                    #print(output_lines)
                    # check = 1
                        
                # 提取add指令的寄存器和立即数
                elif len(parts)==5:
                    if 1:
                        padd1_instruction = "{} {} plats {},{},{}\n".format(parts[0], parts[1], reg_data, reg_addr1, reg_delta)
                        output_lines.append(padd1_instruction)
                        nop_instruction = "{} {} nop\n".format(second_part[0], second_part[1])
                        output_lines.append(nop_instruction)
                        nop_instruction = "{} {} nop\n".format(third_part[0], third_part[1])
                        output_lines.append(nop_instruction)
    with open(output_filename, 'w') as outfile:
        outfile.writelines(output_lines)

# pll
def modify_instructions_pll(input_filename, output_filename):
    with open(input_filename, 'r') as infile:
        lines = infile.readlines()
    
    output_lines = []
    for i in range(0, len(lines), 3):
        line=lines[i]
    # for i, line in enumerate(lines):
        parts = line.strip().split()

        if i+1<len(lines):
            second_line = lines[i+1]
        if i+2<len(lines):
            third_line=lines[i+2]
        # print(parts)
        second_part=second_line.strip().split()
        #print("second_part:",second_part)
        third_part = third_line.strip().split()
        if 1:
            # 没有offset
            if len(parts) == 5:
                reg_data = third_part[3].split(',')[0]
                print(reg_data)
                reg_addr1 = " ".join(parts[-1:]).strip('[]')
                reg_addr2 = " ".join(third_part[-1:]).strip('[]')
                reg_delta=" ".join(second_part[-1:]).strip('[]').strip(',')
                reg_val="["+reg_addr2+","+reg_addr1+"]"
                # reg_val = "["+reg_val1 + "," + reg_val2+"]"
                # print(reg_val)
            # 带有offset
            elif len(parts) == 6:
                reg_data=third_part[3].split(',')[0]
                reg_all= " ".join(parts[-2:]).strip('[]')
                reg_all2=" ".join(third_part[-1:]).strip('[]')
                reg_t1 = parts[3].split(',')[0]
                reg_t2=second_part[3].split(',')[0]
                reg_t=second_part[4].split(',')[0]

                reg_delta = " ".join(second_part[-1:]).strip('[]').strip(',')

                reg_addr2=" ".join(third_part[-1:]).strip('[]').strip(',')
                reg_arg2="["+reg_addr2+","+reg_t1+"]"
                reg_arg3="["+reg_t2+","+reg_t1+"]"
            if re.search(r'\bldr\b', line):
                if '#' in line and len(parts)==6 and len(third_part)==6:

                    mov_instruction = "{} {} add {},{}\n".format(parts[0], parts[1],reg_t1, reg_all)
                    output_lines.append(mov_instruction)
                    # 修改add指令为padd1指令
                    padd1_instruction = "{} {} add {},{},{}\n".format(second_part[0],second_part[1], reg_data, reg_delta,reg_addr2)
                    output_lines.append(padd1_instruction)
                    nop_instruction = "{} {} pll {},{}, {}\n".format(third_part[0], third_part[1], reg_data, reg_t1, reg_data)
                    output_lines.append(nop_instruction)
                    #print(output_lines)
                    # check = 1
                        
                # 提取add指令的寄存器和立即数
                elif len(parts)==5:
                    if 1:
                        print("in")
                        #notimmediate=first_reg
                        padd1_instruction = "{} {} pll {},{},{}\n".format(parts[0], parts[1], reg_data, reg_addr1, reg_delta)
                        output_lines.append(padd1_instruction)
                        nop_instruction = "{} {} nop\n".format(second_part[0], second_part[1])
                        output_lines.append(nop_instruction)
                        nop_instruction = "{} {} nop\n".format(third_part[0], third_part[1])
                        output_lines.append(nop_instruction)

    with open(output_filename, 'w') as outfile:
        outfile.writelines(output_lines)
    

def new_instructions(input_filename):
    with open(input_filename, 'r') as file:
        # 逐行读取文件内容
        result=[]
        for line in file:
            # 使用split()函数分割行，以空格为分隔符，默认分割符
            parts = line.strip()
            # print(parts)
            instruction_parts = parts[16:]
            # print("222",instruction_parts)
            inst = assemble(instruction_parts)
            #print("333",inst)
            if (inst):
                hex_inst= "%.8x" % inst
                # print(hex_inst)
                hex_inst_str = str(hex_inst)
                little_inst=binascii.unhexlify(hex_inst_str)
                big_inst=little_inst[::-1]
                big_inst=binascii.hexlify(big_inst).decode('utf-8')
                #print(big_inst)
                # value = struct.unpack('<I', hex_inst_str)[0]
                # change_value=struct.pack('>I', value)
                # print(change_value)
                # print(parts[7:15])
                parts_list = list(parts)
                parts_list[7:15] = list(big_inst)
                new_parts=''.join(parts_list)
                result.append(new_parts+'\n')
                # print(result)
    with open('res.txt', 'w') as newfile:
        newfile.writelines(result)

if __name__ == "__main__":
    # 修改指令
    content1 = content2 = content3 = content4 = ""  # 初始化内容变量为空字符串

    if os.path.getsize('raw_malu1.txt') > 0:
        modify_instructions_malu1('raw_malu1.txt', 'res_malu1.txt')
        with open('res_malu1.txt', 'r') as file1:
            content1 = file1.read()
    if os.path.getsize('raw_malu2.txt') > 0:
        modify_instructions_malu2('raw_malu2.txt', 'res_malu2.txt')
        with open('res_malu2.txt', 'r') as file2:
            content2 = file2.read()
    if os.path.getsize('raw_plats.txt') > 0:
        modify_instructions_plats('raw_plats.txt', 'res_plats.txt')
        with open('res_plats.txt', 'r') as file3:
            content3 = file3.read()
    if os.path.getsize('raw_pll.txt') > 0:
        modify_instructions_plats('raw_pll.txt', 'res_pll.txt')
        with open('res_pll.txt', 'r') as file4:
            content4 = file4.read()
    #modify_instructions_pll('raw_pll.txt', 'res_pll.txt')

    res_file = content1 + content2 + content3 + content4
    # 合并内容到新文件
    with open('res.txt', 'w') as merged_file:
        merged_file.write(res_file)
        # merged_file.write(content3)
    # 修改PC值
    new_instructions('res.txt')
    # new_instructions('res_padd2.txt')