#!/bin/bash

# Script to check if input file is valid

FILE=$1

# Check if the file exists
if [[ ! -f "$FILE" ]]; then
    echo "$FILE not exists."
    exit 1
fi

echo ""
echo "------------------------------------------------"
echo "                      INPUT                     "
echo "------------------------------------------------"
echo "Virtual SERVER NAME: " `cat "$FILE" | jq .vars_pool[0].name`
echo "Virtual SERVER IP: " `cat "$FILE" | jq .var_virtual_server_vip`
echo "Virtual SERVER PORT: " `cat "$FILE" | jq .var_virtual_server_port`
echo "SSL: " `cat "$FILE" | jq .vars_ssl[0].enable`
echo "iRule: " `cat "$FILE" | jq .vars_irule[0].enable`

echo ""
echo "------------------------------------------------"
echo "                     OUTPUT                     "
echo "------------------------------------------------"
echo "NODE LIST"
array=`cat "$FILE" | jq .vars_node`
printf '%s\n' "${array[@]}"
