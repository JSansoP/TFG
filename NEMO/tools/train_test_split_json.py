import json
import sys
import random

TEST_SIZE = 0.2
SEED = 42
def main():
    file = sys.argv[1]
    random.seed(SEED)
    with open(file, 'r') as f:
        #Create two new files, one for training and one for testing, with the same name as the original file but with the suffixes _train and _test
        train_file = file.replace(".json", "_train.json")
        test_file = file.replace(".json", "_test.json")
        #Each line contains a json object, so we can just read the file line by line
        lines = f.readlines()
        #Shuffle the lines
        random.shuffle(lines)
        #Calculate the number of lines to use for testing
        test_size = int(len(lines) * TEST_SIZE)
        #Write the first test_size lines to the test file
        with open(test_file, 'w') as f_test:
            f_test.writelines(lines[:test_size])
        #Write the remaining lines to the train file
        with open(train_file, 'w') as f_train:
            f_train.writelines(lines[test_size:])
        print("Done!")




if __name__=="__main__":
    main()