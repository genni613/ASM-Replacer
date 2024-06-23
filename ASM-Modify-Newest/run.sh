#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 inputelf outputelf"
    exit 1
fi

inputelf=$1
outputelf=$2
tempelf="temp_${outputelf}"

# Copy the input ELF file to the output ELF file
cp "$inputelf" "$tempelf"

# Read the res.txt file line by line
while read -r line; do
    # Extract the first two columns (address and value)
    address=$(echo "$line" | awk '{print $1}')
    value=$(echo "$line" | awk '{print $2}')
    
    # Ensure address and value have the correct number of hex digits
    if [ ${#address} -ne 6 ] || [ ${#value} -ne 8 ]; then
        echo "Skipping invalid line: $line"
        continue
    fi

    # Print the current address and value being processed
    #echo "Processing address: $address, value: $value"


    # Call the elf.py script with the extracted address and value
    python elf.py "$tempelf" "$outputelf" "$address" "$value"
    
    # Update tempelf to point to the latest outputelf for the next iteration
    mv "$outputelf" "$tempelf"
done < res.txt

# Move the final tempelf to the final outputelf
mv "$tempelf" "$outputelf"
