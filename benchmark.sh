#!/bin/bash
PLUGIN=$1   # "sdk" or "juce"
OUTPUT="results_${PLUGIN}.csv"
echo "run,cycles,instructions,cache_misses" > $OUTPUT

for i in $(seq 1 20); do
    # perf stat outputs to stderr, capture it
    RESULT=$(sudo perf stat -p $(pgrep reaper | tail -1) \
        -e cycles,instructions,cache-misses \
        sleep 30 2>&1)
    
    CYCLES=$(echo "$RESULT" | grep "cycles" | awk '{print $1}' | tr -cd '0-9')
    INSTR=$(echo "$RESULT"  | grep "instructions" | awk '{print $1}' | tr -cd '0-9')
    CACHE=$(echo "$RESULT"  | grep "cache-misses" | awk '{print $1}' | tr -cd '0-9')
    
    echo "$i,$CYCLES,$INSTR,$CACHE" >> $OUTPUT
    echo "Run $i done"
done
