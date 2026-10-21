"""Train the LSTM seq2seq model.   python train_lstm.py [--bidirectional] [--epochs 10]"""
from rnn_seq2seq import main

if __name__ == "__main__":
    main(default_cell="lstm")
