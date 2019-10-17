#!/bin/bash

# Run the LSTMs by running this script
# Before running, set the parameters here, as documented in the README file. You'll probably only want to change the first three parameters
K3_TRAIN_ROOT=train_data
K3_TEST_ROOT=test_data
LOOKAHEAD_LEN=10
# You probably won't want to change the parameters below here
DELTAS_FILE=/media/eoin/BigDisk/hierarchy/Layer\ 1/deltas/offset_{}
PROBABILITY_FILE=/media/eoin/BigDisk/hierarchy/Layer\ 1/misc/probabilities/offset_{}
#outputs/probabilities/lstm_probabilities_offset_{}
WORD2ID_FILE=/media/eoin/BigDisk/hierarchy/Layer\ 1/misc/word2ids/offset_{}
PERPLEXITY_FILE=/media/eoin/BigDisk/hierarchy/Layer 1/misc/perplexities/offset_{}
LINKSET=outputs/lstm_linkset.txt
CLUSTER_FILE=outputs/clusters.txt
RAW_OUTPUT=outputs/raw_output.txt
FINAL_OUTPUT=outputs/final_output.txt

# Part 1: directory creation
for INDEX in $(seq 1 $LOOKAHEAD_LEN)
do
    mkdir $K3_TRAIN_ROOT/$INDEX
done
mkdir outputs
cd outputs
mkdir probabilities
mkdir word2ids
mkdir perplexity
cd ..

# Part 2: Train and run the model for each lookahead offset
for INDEX in $(seq 1 $LOOKAHEAD_LEN)
do
    python3 ptb_word_lm.py --data_path=$K3_TRAIN_ROOT --save_path=$K3_TRAIN_ROOT/$INDEX --probs=$PROBABILITY_FILE --word2id=$WORD2ID_FILE --test=$K3_TEST_ROOT --perplex=$PERPLEXITY_FILE
done

# Part 3: Build and cluster the links 
python3 deltify.py $PROBABILITY_FILE $DELTAS_FILE
#python3 hierarchy.py
#python3 new_cluster.py



