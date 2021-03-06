import argparse
import numpy as np
from skimage.io import imread, imsave
from skimage.transform import resize as imresize
from scipy.spatial.distance import cosine
from scipy.spatial.distance import euclidean
from scipy.spatial import distance_matrix
import os
import sys
import glob
import time
import pandas as pd
from utils.util import fast_hist
from utils.rgb_ind_convertor import *


parser = argparse.ArgumentParser()

parser.add_argument('--dataset', type=str, default='R3D',
					help='define the benchmark')

parser.add_argument('--result_dir', type=str, default='./out',
					help='define the storage folder of network prediction')


###ALSO ADD FUNCTION TO PARSE BOUNDARIES FROM WALLS

def evaluateRooms_cosine(benchmark_path, result_dir, num_of_classes=11, suffix=None, im_resize=True, gt_resize=True, train=False):
    """

    Parameters
    ----------
    benchmark_path : string
        Path to .txt file containing dataset paths.
    result_dir : string
        Directory containing result images to evaluate.
    num_of_classes : int, optional
        Number of room classes. The default is 11.
    suffix : string, optional
        Suffix to append to file name.
    im_resize : boolean, optional
        Whether to resize result images to 512x512. The default is True.
    gt_resize : boolean, optional
        Whether to resize ground truth images to 512x512. The default is True.
    train : boolean, optional
        Whether to evaluate training data or test data. The default is False.

    Returns
    -------
    None.

    """
    gt_paths = open(benchmark_path, 'r').read().splitlines()
    r_paths = [p.split('\t')[3] for p in gt_paths] # 1 denote wall, 2 denote door, 3 denote room
    im_paths = [os.path.join(result_dir, p.split('/')[-1].split('.')[0] + '_pred.png') for p in r_paths]
    data_dir = os.path.dirname(benchmark_path)
    sims=[]
    names = []
    for i in range(len(im_paths)):
        try:
            res_im  = imread(im_paths[i], pilmode='RGB')
            name = os.path.basename(im_paths[i]).split('_')[0]
            if train:
                gt_im = imread(os.path.join(data_dir, 'newyork/train/' + name + '_rooms.png'), pilmode='RGB')
                gt_im_ind = rgb2ind(gt_im, color_map=floorplan_fuse_map) 
            elif not train:
                gt_im = imread(os.path.join(data_dir, 'newyork/test/' + name + '_rooms.png'), pilmode='RGB')
                gt_im_ind = rgb2ind(im, color_map=floorplan_fuse_map)
                
            if im_resize:
                res_im = imresize(res_im, (512,512,3), mode='constant', cval=0, preserve_range=True)
            if gt_resize:
                gt_im_ind = imresize(gt_im_ind, (512,512,3), mode='constant', cval=0, preserve_range=True)
            res_im_1d = res_im.flatten()
            gt_im_1d = gt_im_ind.flatten()
            res_im_1d = res_im_1d + 1e-6
            gt_im_1d = gt_im_1d + 1e-6
            cos = cosine(res_im_1d, gt_im_1d)
            sim = 1-cos
            print("Image " + str(name) + " similarity " + str(sim))
            sims.append(sim)
            names.append(name)
        except FileNotFoundError:
            pass
    df = pd.DataFrame([names, sims]).T
    df.columns=['image', 'similarity']
    df.sort_values(by='similarity', inplace=True, ascending=False)
    df.reset_index(drop=True, inplace=True)
    if suffix:  
        df.to_csv('Cosine_Similarity_Results_' + suffix + '.csv')
    elif not suffix:
            df.to_csv('Cosine_RoomSimilarity_Results.csv')

    aveSim = np.mean(sims)
    print("Average cosine similarity " + str(aveSim))
    return df
                
def evaluateBounds_cosine(benchmark_path, result_dir, suffix=None, im_resize=True, gt_resize=True, train=False):
    """

    Parameters
    ----------
    benchmark_path : string
        Path to .txt file containing dataset paths.
    result_dir : string
        Directory containing result images to evaluate.
    suffix : string, optional
        Suffix to append to file name
    im_resize : boolean, optional
        Whether to resize result images to 512x512. The default is True.
    gt_resize : boolean, optional
        Whether to resize ground truth images to 512x512. The default is True.
    train : boolean, optional
        Whether to evaluate training data or test data. The default is False.

    Returns
    -------
    None.

    """
    gt_paths = open(benchmark_path, 'r').read().splitlines()
    d_paths = [p.split('\t')[2] for p in gt_paths] # 1 denote wall, 2 denote door, 3 denote room
    im_paths = [os.path.join(result_dir, p.split('/')[-1].split('.')[0]).replace('_close', '_doors_windows') + '.png' for p in d_paths]
    data_dir = os.path.dirname(benchmark_path)
    sims=[]
    names = []
    for i in range(len(im_paths)):
        try:
            res_im  = imread(im_paths[i], pilmode='L')
            name = os.path.basename(im_paths[i]).split('_')[0]
            if train:
                gt_im = imread(os.path.join(data_dir, 'newyork/train/' + name + '_close.png'), pilmode='L')
            elif not train:
                gt_im = imread(os.path.join(data_dir, 'newyork/test/' + name + '_close.png'))
                
            if im_resize:
                res_im = imresize(res_im, (512,512,3), mode='constant', cval=0, preserve_range=True)
            if gt_resize:
                gt_im = imresize(gt_im, (512,512,3), mode='constant', cval=0, preserve_range=True)
            res_im_1d = res_im.flatten()
            gt_im_1d = gt_im.flatten()
            res_im_1d = res_im_1d + 1e-6
            gt_im_1d = gt_im_1d + 1e-6
            cos = cosine(res_im_1d, gt_im_1d)
            sim = 1-cos
            print("Image " + str(name) + " similarity " + str(sim))
            sims.append(sim)
            names.append(name)
        except FileNotFoundError:
            pass
    df = pd.DataFrame([names, sims]).T
    df.columns=['image', 'similarity']
    df.sort_values(by='similarity', inplace=True, ascending=False)
    df.reset_index(drop=True, inplace=True)
    if suffix:
        df.to_csv('Cosine_EntranceSimilarity_Results_' + suffix + '.csv')
    elif not suffix:
        df.to_csv('Cosine_EntranceSimilarity_Results.csv')
    aveSim = np.mean(sims)
    print("Average cosine similarity " + str(aveSim))
    return df
      

def evaluateBounds_euclidean(benchmark_path, result_dir, suffix=None, im_resize=True, gt_resize=True, train=True):
    """

    Parameters
    ----------
    benchmark_path : string
        Path to .txt file containing dataset paths.
    result_dir : string
        Directory containing result images to evaluate.
    suffix : string, optional
        Suffix to append to file name
    im_resize : boolean, optional
        Whether to resize result images to 512x512. The default is True.
    gt_resize : boolean, optional
        Whether to resize ground truth images to 512x512. The default is True.
    train : boolean, optional
        Whether to evaluate training data or test data. The default is False.

    Returns
    -------
    None.

    """
    gt_paths = open(benchmark_path, 'r').read().splitlines()
    d_paths = [p.split('\t')[2] for p in gt_paths] # 1 denote wall, 2 denote door, 3 denote room
    im_paths = [os.path.join(result_dir, p.split('/')[-1].split('.')[0]).replace('_close', '_doors_windows') + '.png' for p in d_paths]
    data_dir = os.path.dirname(benchmark_path)
    dists=[]
    names = []
    for i in range(len(im_paths)):
        try:
            res_im  = imread(im_paths[i], pilmode='L')
            name = os.path.basename(im_paths[i]).split('_')[0]
            if train:
                gt_im = imread(os.path.join(data_dir, 'newyork/train/' + name + '_close.png'), pilmode='L')
            elif not train:
                gt_im = imread(os.path.join(data_dir, 'newyork/test/' + name + '_close.png'))
                
            if im_resize:
                res_im = imresize(res_im, (512,512,3), mode='constant', cval=0, preserve_range=True)
            if gt_resize:
                gt_im = imresize(gt_im, (512,512,3), mode='constant', cval=0, preserve_range=True)
            res_im_1d = res_im.flatten()
            gt_im_1d = gt_im.flatten()
            res_im_1d = res_im_1d + 1e-6
            gt_im_1d = gt_im_1d + 1e-6
            dist = euclidean(res_im_1d, gt_im_1d)
            print("Image " + str(name) + " euclidean distance " + str(dist))
            dists.append(dist)
            names.append(name)
        except FileNotFoundError:
            print("Passing " + str(im_paths[i]))
        #    pass
    df = pd.DataFrame([names, dists]).T
    df.columns=['image', 'euclidean_distance']
    df.sort_values(by='euclidean_distance', inplace=True, ascending=False)
    df.reset_index(drop=True, inplace=True)
    if suffix:
        df.to_csv('EuclideanDistance_Entrance_Results_' + suffix + '.csv')
    elif not suffix:
        df.to_csv('EuclideanDisance_Entrance_Results.csv')
    aveDist = np.mean(dists)
    print("Average euclidean distance " + str(aveDist))
    return df

def evaluateBounds_pairWiseDistance(benchmark_path, result_dir, suffix=None, im_resize=True, gt_resize=True, train=True):
    """

    Parameters
    ----------
    benchmark_path : string
        Path to .txt file containing dataset paths.
    result_dir : string
        Directory containing result images to evaluate.
    suffix : string, optional
        Suffix to append to file name
    im_resize : boolean, optional
        Whether to resize result images to 512x512. The default is True.
    gt_resize : boolean, optional
        Whether to resize ground truth images to 512x512. The default is True.
    train : boolean, optional
        Whether to evaluate training data or test data. The default is False.

    Returns
    -------
    None.

    """
    gt_paths = open(benchmark_path, 'r').read().splitlines()
    d_paths = [p.split('\t')[2] for p in gt_paths] # 1 denote wall, 2 denote door, 3 denote room
    im_paths = [os.path.join(result_dir, p.split('/')[-1].split('.')[0]).replace('_close', '_doors_windows') + '.png' for p in d_paths]
    data_dir = os.path.dirname(benchmark_path)
    dists=[]
    names = []
    for i in range(len(im_paths)):
        try:
            res_im  = imread(im_paths[i], pilmode='L')
            name = os.path.basename(im_paths[i]).split('_')[0]
            if train:
                gt_im = imread(os.path.join(data_dir, 'newyork/train/' + name + '_close.png'), pilmode='L')
            elif not train:
                gt_im = imread(os.path.join(data_dir, 'newyork/test/' + name + '_close.png'))
                
            if im_resize:
                res_im = imresize(res_im, (512,512), mode='constant', cval=0, preserve_range=True)
            if gt_resize:
                gt_im = imresize(gt_im, (512,512), mode='constant', cval=0, preserve_range=True)
     #       res_im_1d = res_im.flatten()
     #       gt_im_1d = gt_im.flatten()
     #       res_im_1d = res_im_1d + 1e-6
     #       gt_im_1d = gt_im_1d + 1e-6
            dist = distance_matrix(res_im, gt_im)
            dist = np.mean(dist)
            print("Image " + str(name) + " Pairwise distance " + str(dist))
            dists.append(dist)
            names.append(name)
        except FileNotFoundError:
            print("Passing " + str(im_paths[i]))
        #    pass
    names.append('MEAN')
    dists.append(np.mean(dists))
    df = pd.DataFrame([names, dists]).T
    df.columns=['image', 'pairwise_distance']
    df.sort_values(by='pairwise_distance', inplace=True, ascending=False)
    df.reset_index(drop=True, inplace=True)
    if suffix:
        df.to_csv('PairwiseDistance_Entrance_Results_' + suffix + '.csv')
    elif not suffix:
        df.to_csv('PairwiseDisance_Entrance_Results.csv')
    aveDist = np.mean(dists)
    print("Average Pairwise Distance " + str(aveDist))
    return df

          
def evaluate_semantic(benchmark_path, result_dir, num_of_classes=11, need_merge_result=False, im_downsample=True, gt_downsample=True):
    gt_paths = open(benchmark_path, 'r').read().splitlines()
    d_paths = [p.split('\t')[2] for p in gt_paths] # 1 denote wall, 2 denote door, 3 denote room
    r_paths = [p.split('\t')[3] for p in gt_paths] # 1 denote wall, 2 denote door, 3 denote room
    cw_paths = [p.split('\t')[-1] for p in gt_paths] # 1 denote wall, 2 denote door, 3 denote room, last one denote close wall
    im_names = [p.split('/')[-1].split('.')[0] for p in gt_paths]
    im_paths = [os.path.join(result_dir, p.split('/')[-1].split('.')[0] + '_pred.png') for p in r_paths]
    if need_merge_result:
        im_d_paths = [os.path.join(result_dir, p.split('/')[-1].split('.')[0].replace('close', 'doors_windows.png')) for p in d_paths]
        im_cw_paths = [os.path.join(result_dir, p.split('/')[-1].split('.')[0].replace('close_wall', 'close_walls.png')) for p in cw_paths]

    n = len(im_paths)
	# n = 1
    hist = np.zeros((num_of_classes, num_of_classes))
    for i in range(n):
        im = imread(im_paths[i], pilmode='RGB')
        if need_merge_result:
            im_d = imread(im_d_paths[i], pilmode='L')
            im_cw = imread(im_cw_paths[i], pilmode='L')
		# create fuse semantic label
        cw = imread(cw_paths[i], pilmode='L')
        dd = imread(d_paths[i], pilmode='L')
        rr = imread(r_paths[i], pilmode='RGB')

        if im_downsample: #really means resize, not downsample
            im = imresize(im, (512, 512, 3), preserve_range=True)
            if need_merge_result:
                im_d = imresize(im_d, (512, 512), preserve_range=True)
                im_cw = imresize(im_cw, (512, 512), preserve_range=True)
                im_d = im_d / 255
                im_cw = im_cw / 255

        if gt_downsample: #really means resize, not downsample
            cw = imresize(cw, (512, 512), preserve_range=True)
            dd = imresize(dd, (512, 512), preserve_range=True)  
            rr = imresize(rr, (512, 512, 3), preserve_range=True)

		# normalize
        cw = cw / 255
        dd = dd / 255

        im_ind = rgb2ind(im, color_map=floorplan_fuse_map) 
        if im_ind.sum()==0:
            im_ind = rgb2ind(im+1)
        rr_ind = rgb2ind(rr, color_map=floorplan_fuse_map) 
        if rr_ind.sum()==0:
            rr_ind = rgb2ind(rr+1)

        if need_merge_result:
            im_d  = (im_d>0.5).astype(np.uint8)
            im_cw = (im_cw>0.5).astype(np.uint8)
            im_ind[im_cw==1] = 10
            im_ind[im_d ==1] = 9

		# merge the label and produce 
        cw = (cw>0.5).astype(np.uint8)
        dd = (dd>0.5).astype(np.uint8)
        rr_ind[cw==1] = 10
        rr_ind[dd==1] = 9

        name = im_paths[i].split('/')[-1]
        r_name = r_paths[i].split('/')[-1]
		
        print('Evaluating {}(im) <=> {}(gt)...'.format(name, r_name))

        hist += fast_hist(im_ind.flatten(), rr_ind.flatten(), num_of_classes)

    print('*'*60)
	# overall accuracy
    acc = np.diag(hist).sum() / hist.sum()
    print('overall accuracy {:.4}'.format(acc))
    # per-class accuracy, avoid div zero
    acc = np.diag(hist) / (hist.sum(1) + 1e-6)
    print('room-type: mean accuracy {:.4}, room-type+bd: mean accuracy {:.4}'.format(np.nanmean(acc[:7]), (np.nansum(acc[:7])+np.nansum(acc[-2:]))/9.))
    for t in range(0, acc.shape[0]):
        if t not in [7, 8]:
            print('room type {}th, accuracy = {:.4}'.format(t, acc[t]))

    print('*'*60)
	# per-class IU, avoid div zero
    iu = np.diag(hist) / (hist.sum(1) + 1e-6 + hist.sum(0) - np.diag(hist))
    print('room-type: mean IoU {:.4}, room-type+bd: mean IoU {:.4}'.format(np.nanmean(iu[:7]), (np.nansum(iu[:7])+np.nansum(iu[-2:]))/9.))
    for t in range(iu.shape[0]):
        if t not in [7,8]: # ignore class 7 & 8
            print('room type {}th, IoU = {:.4}'.format(t, iu[t]))

if __name__ == '__main__':
	FLAGS, unparsed = parser.parse_known_args()

	if FLAGS.dataset.lower() == 'r2v':
		benchmark_path = './dataset/r2v_test.txt'
	else:
		benchmark_path = './dataset/r3d_test.txt'

	result_dir = FLAGS.result_dir

	tic = time.time()
	evaluate_semantic(benchmark_path, result_dir, need_merge_result=False, im_downsample=False, gt_downsample=True) # same as previous line but 11 classes by combining the opening and wall line

	print("*"*60)
	print("Evaluate time: {} sec".format(time.time()-tic))