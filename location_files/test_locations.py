#!/usr/bin/env python

'''
Very simple script to test if location files load

NOTE: this will also run all location save files through the savefile
updater -- so after running it, you can decide if the updated save
files should be committed to git.
'''


import os
from gnome.persist import load


loc_files = os.path.dirname(os.path.abspath(__file__))
dirs = os.listdir(loc_files)

for d in dirs:
    save_dir = os.path.join(d, '{0}_save'.format(d))
    model = os.path.join(loc_files, save_dir, 'Model.json')

    if not os.path.exists(model):
        continue

    try:
        m = load(model)
        print("successfully loaded: {0}".format(model))
    except:
        print("FAILED: {0}".format(model))
