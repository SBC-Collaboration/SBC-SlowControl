#!/bin/bash
i=0
while true; do
echo "I am here"
sleep 2
echo "I am there" 
echo i: $i
((i=i+1))
done
echo "quit the loop"

