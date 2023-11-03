import re
import sys


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
REGENC = {"xzr": 31, "wzr": "31", "sp": 28, 'w0': 0, 'x0': 0, 'w1': 1, 'x1': 1, 'w2': 2, 'x2': 2, 'w3': 3, 'x3': 3, 'w4': 4, 'x4': 4, 'w5': 5, 'x5': 5, 'w6': 6, 'x6': 6, 'w7': 7, 'x7': 7, 'w8': 8, 'x8': 8, 'w9': 9, 'x9': 9, 'w10': 10, 'x10': 10, 'w11': 11, 'x11': 11, 'w12': 12, 'x12': 12, 'w13': 13, 'x13': 13, 'w14': 14, 'x14': 14, 'w15': 15, 'x15': 15, 'w16': 16, 'x16': 16, 'w17': 17, 'x17': 17, 'w18': 18, 'x18': 18, 'w19': 19, 'x19': 19, 'w20': 20, 'x20': 20, 'w21': 21, 'x21': 21, 'w22': 22, 'x22': 22, 'w23': 23, 'x23': 23, 'w24': 24, 'x24': 24, 'w25': 25, 'x25': 25, 'w26': 26, 'x26': 26, 'w27': 27, 'x27': 27, 'w28': 28, 'x28': 28, 'w29': 29, 'x29': 29, 'w30': 30, 'x30': 30, 'w31': 31, 'x31': 31}
def encode_regs(rm:str, rn:str, rt:str):
	if not rm: rm = "xzr"
	rm = REGENC[rm] << 16
	rn = REGENC[rn] << 5
	rt = REGENC[rt]
	return rm | rn | rt

def encode_reg_imms(imm:int, rn:str, rt:str):
	imm = imm << 12
	rn = REGENC[rn] << 5
	rt = REGENC[rt]
	return imm | rn | rt

malu12regpat = re.compile(f'(p(?:add|sub|or|xor|and)[12]){WHITE}({REG}){WHITE},{WHITE}\[{WHITE}({REG}){WHITE}(?:,{WHITE}({REG}))?{WHITE}(?:,{WHITE}(uxtw|lsl|sxtw|sxtx){WHITE}#?(0|2|3))?{WHITE}\]')
malu1immpat = re.compile(f'(p(?:add|sub|or|xor|and)1){WHITE}({REG}){WHITE},{WHITE}\[{WHITE}({REG}){WHITE},{WHITE}({IMM}){WHITE}\]')
# movpat = re.compile(f'mov{WHITE}({REG}){WHITE},{WHITE}({IMM})')

malu12_reg_base = {
	"padd1": 0x2200000,
	"psub1": 0x2200400,
	"pand1": 0x2200800,
	"por1":  0x2200c00,
	"pxor1": 0x2600000,
	"padd2": 0x3200000,
	"psub2": 0x3200400,
	"pand2": 0x3200800,
	"por2":  0x3200c00,
	"pxor2": 0x3600000,
}

malu1_imm_base = {
	"padd1": 0x22000000,
	"psub1": 0x22004000,
	"pand1": 0x22008000,
	"por1":  0x2200c000,
	"pxor1": 0x22400000,
}

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
		
	elif row.strip().startswith("mov"):
		return llvm_asm(row)
	elif row.strip().startswith("nop"):
		return 0xd503201f
	else:
		return None

# 修改指令
def modify_instructions(input_filename, output_filename):
    with open(input_filename, 'r') as infile:
        lines = infile.readlines()
    
    output_lines = []
    count = 3
    for i, line in enumerate(lines):
        check = 0
        parts = line.strip().split()
        if count % 3 == 0:
           reg_val = " ".join(parts[-2:])
        # print(reg_val)
        if re.search(r'\badd\b', line):
            if len(parts)>3:
                reg = parts[3].split(',')[0]
            else:
                continue
            immediate = parts[-1]
            if 'add' in line and '#' in line:
                # 替换上一条指令为mov指令
                mov_instruction = "{:<7}{:<8}mov {},{}\n".format(output_lines[-1][:6], output_lines[-1][7:16], reg, immediate)
                output_lines[-1] = mov_instruction
                
                # 修改add指令为padd1指令
                padd1_instruction = "{:<7}{:<8} padd1 {},{}\n".format(parts[0],parts[1], reg, reg_val)
                output_lines.append(padd1_instruction)
                check = 1
            # 提取add指令的寄存器和立即数
            if check == 0:
                reg = parts[3].split(',')[0]
                notimmediate = parts[-1]
                padd1_instruction = "{:<7}{:<8}padd1 {},{}\n".format(output_lines[-1][:6], output_lines[-1][7:16], notimmediate, reg_val)
                output_lines[-1] = padd1_instruction
                nop_instruction = "{:<7}{:<8} nop\n".format(parts[0], parts[1])
                output_lines.append(nop_instruction)
            
            # 添加一个nop指令
            # nop_instruction = "{:<9} {:<8}nop\n".format(hex(int(parts[0], 16) + 8)[2:], parts[1])
            # output_lines.append(nop_instruction)
        elif 'sub' in line:
            if len(parts)>3:
                reg = parts[3].split(',')[0]
            else:
                continue
            immediate = parts[-1]
            if 'sub' in line and '#' in line:
                # 替换上一条指令为mov指令
                mov_instruction = "{:<7}{:<8}mov {},{}\n".format(output_lines[-1][:6], output_lines[-1][7:16], reg, immediate)
                output_lines[-1] = mov_instruction
                
                # 修改sub指令为psub1指令
                padd1_instruction = "{:<7}{:<8} psub1 {},{}\n".format(parts[0],parts[1], reg, reg_val)
                output_lines.append(padd1_instruction)
                check = 1
            # 提取sub指令的寄存器和立即数
            if check == 0:
                reg = parts[3].split(',')[0]
                notimmediate = parts[-1]
                padd1_instruction = "{:<7}{:<8}psub1 {},{}\n".format(output_lines[-1][:6], output_lines[-1][7:16], notimmediate, reg_val)
                output_lines[-1] = padd1_instruction
                nop_instruction = "{:<7}{:<8} nop\n".format(parts[0], parts[1])
                output_lines.append(nop_instruction)
        elif 'and' in line:
            if len(parts)>3:
                reg = parts[3].split(',')[0]
            else:
                continue
            immediate = parts[-1]
            if 'and' in line and '#' in line:
                # 替换上一条指令为mov指令
                mov_instruction = "{:<7}{:<8}mov {},{}\n".format(output_lines[-1][:6], output_lines[-1][7:16], reg, immediate)
                output_lines[-1] = mov_instruction
                
                # 修改and指令为pand1指令
                padd1_instruction = "{:<7}{:<8} pand1 {},{}\n".format(parts[0],parts[1], reg, reg_val)
                output_lines.append(padd1_instruction)
                check = 1
            # 提取and指令的寄存器和立即数
            if check == 0:
                reg = parts[3].split(',')[0]
                notimmediate = parts[-1]
                padd1_instruction = "{:<7}{:<8}pand1 {},{}\n".format(output_lines[-1][:6], output_lines[-1][7:16], notimmediate, reg_val)
                output_lines[-1] = padd1_instruction
                nop_instruction = "{:<7}{:<8} nop\n".format(parts[0], parts[1])
                output_lines.append(nop_instruction)
        elif 'or' in line:
            if len(parts)>3:
                reg = parts[3].split(',')[0]
            else:
                continue
            immediate = parts[-1]
            if 'or' in line and '#' in line:
                # 替换上一条指令为mov指令
                mov_instruction = "{:<7}{:<8}mov {},{}\n".format(output_lines[-1][:6], output_lines[-1][7:16], reg, immediate)
                output_lines[-1] = mov_instruction
                
                # 修改or指令为por1指令
                padd1_instruction = "{:<7}{:<8} por1 {},{}\n".format(parts[0],parts[1], reg, reg_val)
                output_lines.append(padd1_instruction)
                check = 1
            # 提取or指令的寄存器和立即数
            if check == 0:
                reg = parts[3].split(',')[0]
                notimmediate = parts[-1]
                padd1_instruction = "{:<7}{:<8}por1 {},{}\n".format(output_lines[-1][:6], output_lines[-1][7:16], notimmediate, reg_val)
                output_lines[-1] = padd1_instruction
                nop_instruction = "{:<7}{:<8} nop\n".format(parts[0], parts[1])
                output_lines.append(nop_instruction)
        elif 'xor' in line:
            if len(parts)>3:
                reg = parts[3].split(',')[0]
            else:
                continue
            immediate = parts[-1]
            if 'xor' in line and '#' in line:
                # 替换上一条指令为mov指令
                mov_instruction = "{:<7}{:<8}mov {},{}\n".format(output_lines[-1][:6], output_lines[-1][7:16], reg, immediate)
                output_lines[-1] = mov_instruction
                
                # 修改or指令为pxor1指令
                padd1_instruction = "{:<7}{:<8} pxor1 {},{}\n".format(parts[0],parts[1], reg, reg_val)
                output_lines.append(padd1_instruction)
                check = 1
            # 提取xor指令的寄存器和立即数
            if check == 0:
                reg = parts[3].split(',')[0]
                notimmediate = parts[-1]
                padd1_instruction = "{:<7}{:<8}pxor1 {},{}\n".format(output_lines[-1][:6], output_lines[-1][7:16], notimmediate, reg_val)
                output_lines[-1] = padd1_instruction
                nop_instruction = "{:<7}{:<8} nop\n".format(parts[0], parts[1])
                output_lines.append(nop_instruction)
        elif 'str' in line:
            # 对于str指令，只需输出一个nop指令
            nop_instruction = "{:<7}{:<8} nop\n".format(parts[0], parts[1])
            output_lines.append(nop_instruction)
        else:
            # 如果行不包含需要修改的add指令或str指令，原样写入
            output_lines.append(line)
        count += 1
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
            # print(instruction_parts)
            inst = assemble(instruction_parts)
            if (inst):
                hex_inst= "%.8x" % inst
                hex_inst_str = str(hex_inst)
                # print(hex_inst_str)
                # print(parts[7:15])
                parts_list = list(parts)
                parts_list[7:15] = list(hex_inst_str)
                new_parts=''.join(parts_list)
                result.append(new_parts+'\n')
    with open('res2.txt', 'w') as newfile:
        newfile.writelines(result)

if __name__ == "__main__":
    # 修改指令
    modify_instructions('raw.txt', 'res.txt')
    new_instructions('res.txt')
    