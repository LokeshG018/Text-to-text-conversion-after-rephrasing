"""Train the GRU seq2seq model.   python train_gru.py [--epochs 10]"""
from rnn_seq2seq import main

if __name__ == "__main__":
    main(default_cell="gru")
