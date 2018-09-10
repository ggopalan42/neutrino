#! /usr/bin/env python

import os
import sys

import pandas as pd

# Constants
PKL_FN = '/home/ggopalan/projects/apps/app_utils/pkl_files/archimedes_1535155734.pkl'

def read_pkl_file(pkl_fn):
    ''' Read pkl file and return a df  '''
    pkl_df = pd.read_pickle(pkl_fn)
    return pkl_df

def print_pkl_df(pkl_df):
    ''' Print out the pickle df to stdout '''
    print(pkl_df.to_string())

if __name__ == '__main__':
    # Load the pickle file
    pkl_df = read_pkl_file(PKL_FN)
    print_pkl_df(pkl_df)


