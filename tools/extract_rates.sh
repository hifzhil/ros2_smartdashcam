#!/bin/bash

# Extract average rates and save them to data.txt
grep "average rate:" "$1" | awk '{print NR, $3}' > data.txt 