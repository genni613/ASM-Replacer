from elftools.elf.elffile import ELFFile
import sys

def modify_elf_file(input_file, output_file, address, new_value):
    with open(input_file, 'rb') as f:
        elffile = ELFFile(f)

        # Locate the section containing the address
        section_data = None
        section_offset = None
        for section in elffile.iter_sections():
            start = section['sh_addr']
            end = start + section['sh_size']
            #print(f"Checking section: {section.name}, start: {hex(start)}, end: {hex(end)}")  # Debug info
            if start <= address < end:
                # Found the section containing the address
                #print(f"Found section: {section.name} containing the address: {hex(address)}")  # Debug info
                section_data = bytearray(section.data())
                section_offset = section['sh_offset']
                offset = address - start
                #print(f"Section offset: {hex(section_offset)}, data offset: {hex(offset)}")  # Debug info
                # Assuming we are modifying a 4-byte integer
                section_data[offset:offset+4] = new_value.to_bytes(4, byteorder='big')  # Change to 'big' endian
                break
        else:
            raise ValueError("Address not found in any section")

    with open(input_file, 'rb') as f:
        original_data = f.read()

    # Create the modified file with changes
    modified_data = bytearray(original_data)
    modified_data[section_offset:section_offset + len(section_data)] = section_data

    with open(output_file, 'wb') as f:
        f.write(modified_data)
    #print(f"Modification successful. Output written to {output_file}")  # Debug info

def parse_hex(value, expected_length):
    if len(value) != expected_length:
        raise ValueError(f"Expected {expected_length} hex digits, got {len(value)}")
    return int(value, 16)

if __name__ == "__main__":
    if len(sys.argv) != 5:
        #print(f"Usage: {sys.argv[0]} <input file> <output file> <6-digit address> <8-digit new value>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    address = parse_hex(sys.argv[3], 6)
    new_value = parse_hex(sys.argv[4], 8)

    modify_elf_file(input_file, output_file, address, new_value)
