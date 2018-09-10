#! /usr/bin/env python

import os
import sys

import pandas as pd

# Constants
PKL_FN = '/home/ggopalan/projects/apps/app_utils/pkl_files/archimedes_1535155734.pkl'
COLUMN_ORDER = ['detect_time', 'confidence', 'found', 'stream_name', 'msg_format_version', 'startX', 'endX', 'startY', 'endY' ]


def read_pkl_file(pkl_fn):
    ''' Read pkl file and return a df  '''
    pkl_df = pd.read_pickle(pkl_fn)
    return pkl_df

def print_row_in_order(df_row):
    ''' Print out the row in COLUMN_ORDER '''
    df_row_ordered = [df_row[x] for x in COLUMN_ORDER]
    for elem in df_row_ordered:
        print('{} '.format(elem), end = '')
    print('\n')
    # print(' '.join(df_row_ordered))
    
def print_pkl_df(pkl_df):
    ''' Print out the pickle df to stdout '''
    # print(pkl_df.to_string())
    # Print the header
    print(' '.join(COLUMN_ORDER))
    for i in range(len(pkl_df)):
        print_row_in_order(pkl_df.iloc[i])

if __name__ == '__main__':
    # Load the pickle file
    pkl_df = read_pkl_file(PKL_FN)
    print_pkl_df(pkl_df)


