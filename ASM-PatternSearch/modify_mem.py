import re
import sys

def process_file(file_path, output_file):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        pattern = re.compile(r'bl.*(memset|memcpy|mempcpy)')
        # pattern = re.compile(r'bl.*(\b__mempcpy\b|\b__memcpy\b)')
        # pattern = re.compile(r'bl.*(\bexpand_builtin_memset\b|\b__memset\b|\b__memcpy\b|\b__mempcpy\b)')

    with open(output_file, 'w') as out:
        for line in lines:
            if re.search(pattern, line):
                line = line.replace(':', '').replace('\t', ' ')
                modified_line = line.lstrip(' ').replace(' bl', 'bl', 1)
                out.write(modified_line)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test.py <file_path>")
    else:
        file_path = sys.argv[1]
        output_file = 'raw.txt'  # You can change this if needed
        process_file(file_path, output_file)