#!/bin/bash

if [[ -z $1 ]]; then
    echo "Usage: $0 <number_of_philosophers>"
    exit 1
fi

NUM_PHILOSOPHERS=$1

# Start the table node in the background
./build/table &
TABLE_PID=$!

sleep 0.5

# Start the philosopher nodes in the background
PHIL_PIDS=()
for (( i=0; i<NUM_PHILOSOPHERS; i++ )); do
    ./build/philosopher "$i" &
    PHIL_PIDS+=($!)
done

# Wait for all processes and clean up on Ctrl+C
trap "kill $TABLE_PID ${PHIL_PIDS[*]} 2>/dev/null; exit" SIGINT SIGTERM
wait