This is based on the word-level LSTM provided in the TensorFlow tutorials: 
https://github.com/tensorflow/models/tree/master/tutorials/rnn/ptb
But with a number of major changes! 

# The Dataset
Use the dataset from the email, there's no point putting it on GitHub and wasting my space!

# Running the system
The simplest way to run the system is to extract the files to some location, leaving the internal directory structure intact, and run the ./run.sh shell script. This will train and run the entire system for you, which takes a little over 2 hours on my machine. 

The system will default to a lookahead length of 20. This can be changed by editing the variable declaration on line 7 of run.sh. The window length (i.e. the length of the input window to the LSTM, also set to 20) is set on line 340 of ptb\_word\_lm.py 

N.B. the variable format in run.sh must strictly be VAR\_NAME=VAR\_VALUE without  any spaces, since other Python files will read the values while running and expect them to be in this format!

# Inspecting the output
When finished, a huge amount of output will have been written out. The LSTMs themselves will have been written to the train\_data directory. It should have subdirectories with numbered names 1, 2, ..., lookahead length. Each subdirectory contains the corresponding LSTM for that lookahead offset. There should also be a new directory called outputs. Inside outputs will be the following directory structure: 

* **/outputs**
 * **lstm\_linkset.txt** - The actual links computed by the system. Each line corresponds to a single link. Each link is represented as a comma-separated list of indexes into the validation dataset.
 * **clusters.txt** - The activity types that the clustering assigned each link/activity to. Each line in lstm\_linkset.txt has a corresponding line in clusters.txt of the form new\_event\_*, denoting the type of activity. 
 * **raw\_output.txt** - The dataset, with events replaced by corresponding types. For example, suppose we have the input dataset: 
      `A B C D E F`
    And B, C and D are found to belong to an activity of type new\_event\_3, then the raw\_output for this dataset would be:
      `A new_event_3 new_event_3 new_event_3 E F`
    I.e. B, C and D are replaced with new\_event 3.
 * **final\_output.txt** - The dataset, with entire activities replaced by a single event of the corresponding type. So the A B C D E F dataset above would simply be replaced by: 
      `A new_event_3 E F`
 * **/probabilities** - Directory of probability files. There is one file for each lookahead offset, named lstm\_probability\_offset\_1 through to lstm\_probability\_offset\_m. Each file consists of probability vectors, one per line, produced by the corresponding LSTM.
 * **/word2ids** - Directory for files holding the word2ids dictionary for each LSTM. This dictionary is used in the TensorFlow code to map event names (words) to offsets within the output (probability) vectors. The files are named lstm\_word2id\_offset\_1 through to lstm\_word2id\_offset\_m.
 * **/perplexity** - Directory of files holding the perplexity of each LSTM. Note that this is just a single floating-point value stored in a file. The files are named lstm\_perplexity\_offset\_1 through to lstm\_perplexity\_offset\_m.

N.B. you should delete or move ALL of these output files before running run.sh from scratch again! 

# Basic outline of the code
The run.sh script runs in three parts: 
* **Part 1:** Create the directory structure to write the output files to
* **Part 2:** Train and run the LSTMs, writing the results to files. This is done using the ptb_word_lm.py file, and the file is invoked once for each lookahead offset 1...m
* **Part 3:** Build the links/activities, and cluster them together into activity types

The Python files included are: 
* **util.py** - Taken from the tutorial code, unmodified. 
* **reader.py** - Taken from the tutorial code. Used to read the input datasets. There are a few changes here: 
  * For each run, the ptb_word_lm.py file sets the value of the lookahead variable in the file to the lookahead offset for this LSTM. 
  * The file now stores the word2id dictionary for each LSTM in the word2id variable, and also has functions added to write them to the outputs/word2ids directory as described above. 
* **ptb\_word\_lm.py** - Taken from the tutorial code. Has a few minor modifications: 
  * Passes the lookahead length to reader.py
  * Writes ALL files not written out by reader.py and hierarchy.py
  * Although we default to using the default (small) LSTM configuration, note that I've changed the specs of the small config to match the large config more closely! 
* **integrate.py** - Used to build the actual links. Not called directly: hierarchy.py calls it instead. Note that for now we just integrate naively, i.e. without using perplexity weighting as John suggested. 
* **hierarchy.py** - Builds links using integrate.py, and clusters them together. The clustering code isn't hugely important at this stage, since we have to get the training/integration/link-finding working first. This file writes out the following files: 
  * *outputs/lstm\_linkset.txt* - produced the by naive\_integrate() function in integrate.py
  * *outputs/clusters.txt* - produced by the cluster\_types\_2() function in hierarchy.py
  * *outputs/raw\_output.txt* - produced by the types\_to\_raw\_output() function in hierarchy.py
  * *outputs/final\_output.txt* - produced by the ttd2() (types to dataset) function in hierarchy.py 


