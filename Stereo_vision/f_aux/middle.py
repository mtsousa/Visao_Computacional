# This code adapted from https://blog.csdn.net/weixin_44899143/article/details/89186891

from pathlib import Path
import numpy as np
import csv
import re
import cv2
import os.path
import matplotlib.pyplot as plt

def read_calib(calib_file_path):
    with open(calib_file_path, 'r') as calib_file:
        calib = {}
        csv_reader = csv.reader(calib_file, delimiter='=')
        for attr, value in csv_reader:
            calib.setdefault(attr, value)

    return calib

def read_pfm(pfm_file_path, base_new):
    with open(pfm_file_path, 'rb') as pfm_file:
        header = pfm_file.readline().decode().rstrip()
        channels = 3 if header == 'PF' else 1

        dim_match = re.match(r'^(\d+)\s(\d+)\s$', pfm_file.readline().decode('utf-8'))
        if dim_match:
            width, height = map(int, dim_match.groups())
        else:
            raise Exception("Malformed PFM header.")

        scale = float(pfm_file.readline().decode().rstrip())
        if scale < 0:
            endian = '<' # littel endian
            scale = -scale
        else:
            endian = '>' # big endian

        dispariy = np.fromfile(pfm_file, endian + 'f')

    img = np.reshape(dispariy, newshape=(height, width, channels))
    img[img==np.inf] = 0
    img = np.flipud(img)

    matrix_gt = cv2.normalize(img, None, 0, 1, cv2.NORM_MINMAX, cv2.CV_32F)
    np.save(os.path.join(base_new, 'gt_disparidade.npy'), matrix_gt)

    groundtruth = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    show(groundtruth, "disparity")
    cv2.imwrite(os.path.join(base_new, 'gt_disparity.png'), groundtruth)

    return dispariy, [(height, width, channels), scale]


def create_depth_map(pfm_file_path, base_new, calib=None):

    dispariy, [shape,scale] = read_pfm(pfm_file_path, base_new)

    if calib is None:
        raise Exception("Loss calibration information.")
    else:
        fx = float(calib['cam0'].split(' ')[0].lstrip('['))
        base_line = float(calib['baseline'])
        doffs = float(calib['doffs'])

		# scale factor is used here
        depth_map = fx*base_line / (dispariy / scale + doffs)
        depth_map = np.reshape(depth_map, newshape=shape)
        depth_map = np.flipud(depth_map).astype('uint8')

        return depth_map

def show(img, win_name='image'):
    if img is None:
        raise Exception("Can't display an empty image.")
    else:
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win_name, (439, 331))
        cv2.imshow(win_name, img)
        cv2.waitKey()
        cv2.destroyWindow(win_name)


def main():
    base = os.path.abspath(os.path.dirname(__file__))
    if os.name == 'nt':
	    base_new = base.replace('\\f_aux', '')
    else:
	    base_new = base.replace('/f_aux', '')

    # Define vectors for images and their respective paths
    data = [os.path.join(base_new, 'data', 'Middlebury', 'Jadeplant-perfect'),
			    os.path.join(base_new, 'data', 'Middlebury', 'Playtable-perfect')]
    name = ['Jadeplant', 'Playtable']
    
    for i in range(len(name)):
        pfm_file_dir = Path(data[i])
        calib_file_path = pfm_file_dir.joinpath('calib.txt')
        disp_left = pfm_file_dir.joinpath('disp0.pfm')
        
        # calibration information
        calib = read_calib(calib_file_path)
        
        # create depth map
        depth_map_left = create_depth_map(disp_left, data[i], calib)
        cv2.imwrite(os.path.join(data[i], 'gt_depth_map.jpg'), depth_map_left)
        show(depth_map_left, "depth_map")

if __name__ == '__main__':
    main()