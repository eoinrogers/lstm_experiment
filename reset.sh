mkdir TEMP
cd train_data
mv ptb.*.txt ../TEMP
cd ..
rm -r outputs
rm -r train_data
mv TEMP train_data


