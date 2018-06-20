import os
import cv2
import numpy as np
import progressbar
import random

import loader

DIM_TRAIN = '/home/tangih/Documents/datasets/image_matting/Adobe_Deep_Image_Matting_Dataset/Adobe-licensed/'
DIM_TEST = '/home/tangih/Documents/datasets/image_matting/Adobe_Deep_Image_Matting_Test_Set'
SYNTHETIC_DATASET = '/home/tangih/Documents/datasets/3d_models/SYNTHETIC/'
VOC_DATASET = '/home/tangih/Documents/datasets/VOCtrainval_11-May-2012/VOCdevkit/VOC2012/JPEGImages/'


def create_bgra(fg_path, alpha_path, out_path):
    """ convert fg-jpg and alpha-jpg image into BGRA dataset """
    fg = cv2.imread(fg_path)
    alpha = cv2.imread(alpha_path, 0)
    bgra = np.zeros((fg.shape[0], fg.shape[1], 4), dtype=np.uint8)
    bgra[:, :, :3] = fg
    bgra[:, :, 3] = alpha
    cv2.imwrite(out_path, bgra)


def convert_dataset(fg_folder, alpha_folder, out_folder):
    """ convert fg-jpg and alpha-jpg dataset into BGRA dataset """
    filenames = os.listdir(fg_folder)
    print('Converting dataset...')
    for filename in progressbar.progressbar(filenames):
        fg_path = os.path.join(fg_folder, filename)
        alpha_path = os.path.join(alpha_folder, filename)
        name, _ = filename.split('.')
        new_filename = name+'.png'
        out_path = os.path.join(out_folder, new_filename)
        if not os.path.isfile(alpha_path):
            print('Could not find alpha matte for {}'.format(filename))
            continue
        create_bgra(fg_path, alpha_path, out_path)


def trimap_from_matte(matte):
    """
    :param matte: the input alpha layer
    :return: trimap generated by expanding/eating the alpha layer
    """
    assert matte.dtype == np.float64
    h, w = matte.shape
    dilate, crop = 1, 3
    trimap = np.zeros((h, w), dtype=np.uint8)
    for i in range(h):
        for j in range(w):
            if matte[i, j] == 1.:
                trimap[i, j] = 255
            elif matte[i, j] == 0.:
                trimap[i, j] = 0
            else:
                side = max(dilate, crop)
                trimap[i, j] = 128
                for k in range(-side, side+1):
                    if i+k < 0 or i+k >= h:
                        continue
                    for l in range(-side, side+1):
                        if j+l < 0 or j+l >= w:
                            continue
                        if matte[i+k, j+l] == 1. and\
                                -crop <= k <= crop and -crop <= l <= crop:
                            trimap[i+k, j+l] = 128
                        elif matte[i+k, j+l] == 0. and\
                                -dilate <= k <= dilate and -dilate <= l <= dilate:
                            trimap[i+k, j+l] = 128
    return trimap


def generate_trimaps(src_folder, dst_folder):
    """
    generates trimaps dataset given alpha layers
    -----------------------------------------------
    this is a bit slow and could be improved coding
    it in C++
    """
    file_list = os.listdir(src_folder)
    for filename in progressbar.progressbar(file_list):
            target = os.path.join(dst_folder, filename)
            if os.path.isfile(target):
                continue
            matte, _ = loader.read_fg_img(os.path.join(src_folder, filename))
            trimap = trimap_from_matte(matte)
            cv2.imwrite(target, trimap)


def create_list(root_folder, dst_file):
    voc_rel = 'VOC_bg'
    fg_rel = os.path.join('fg', 'DIM_TRAIN')
    tr_rel = os.path.join('tr', 'DIM_TRAIN')
    fg_abs = os.path.join(root_folder, fg_rel)
    voc_abs = os.path.join(root_folder, voc_rel)
    fg_list = os.listdir(fg_abs)
    voc_list = os.listdir(voc_abs)
    n = 100
    str = ''
    for fg in fg_list:
        fg_path = os.path.join(fg_rel, fg)
        tr_path = os.path.join(tr_rel, fg)
        assert os.path.isfile(tr_path)
        ids = np.random.randint(0, len(voc_list), size=n)
        bg = ['{} {} {}'.format(fg_path,
                                tr_path,
                                os.path.join(voc_rel, voc_list[i]))
              for i in ids]
        str += '\n'.join(bg) + '\n'
    with open(dst_file, 'w') as f:
        f.write(str)


if __name__ == '__main__':
    # convert DIM dataset
    # alpha_train = os.path.join(DIM_TRAIN, 'alphas', 'imgs')
    # alpha_test = os.path.join(DIM_TEST, 'alpha')
    # fg_train = os.path.join(DIM_TRAIN, 'fgs', 'imgs')
    # fg_test = os.path.join(DIM_TEST, 'fg')
    out_train = os.path.join(SYNTHETIC_DATASET, 'fg', 'DIM_TRAIN')
    out_test = os.path.join(SYNTHETIC_DATASET, 'fg', 'DIM_TEST')
    # convert_dataset(fg_train, alpha_train, out_train)
    # convert_dataset(fg_test, alpha_test, out_test)

    # generate trimaps
    generate_trimaps(out_train, os.path.join(SYNTHETIC_DATASET, 'trimap', 'DIM_TRAIN'))
    generate_trimaps(out_test, os.path.join(SYNTHETIC_DATASET, 'trimap', 'DIM_TEST'))
