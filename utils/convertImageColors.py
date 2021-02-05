#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  4 12:50:30 2021

@author: smith
"""
import os
os.chdir('/d2/studies/TF2DeepFloorplan')
from skimage.io import imread, imsave
from utils.rgb_ind_convertor import *

directory = '/d2/studies/TF2DeepFloorplan/ams3/'

files = os.listdir(directory)

for file in files[:10]:
    if file.endswith('.png'):
        fullpath=os.path.join(directory, file)
        im = imread(fullpath, pilmode='RGB')
        f_ind = rgb2ind(im, color_map=floorplan_fuse_map)
        f_rgb = ind2rgb(f_ind, color_map=floorplan_fuse_map)
        if not os.path.exists(os.path.join(directory, 'convertedImages/')):
            os.mkdir(os.path.join(directory, 'convertedImages/'))
        imsave(os.path.join(directory, 'convertedImages/' + file), f_rgb)

