"""Performs face alignment and stores face thumbnails in the output directory."""
# MIT License
#
# Copyright (c) 2016 David Sandberg
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from scipy import misc
import sys
import os
import argparse
import tensorflow as tf
import numpy as np
import random
import cv2
from time import sleep

import facenet
import align.detect_face
from cfg.params_config import CONFIGURATIONS as CONF


def main(argv):
    sleep(random.random())
    global args
    args = argv
    output_dir = os.path.expanduser(args.output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Store some git revision info in a text file in the log directory
    src_path, _ = os.path.split(os.path.realpath(__file__))
    facenet.store_revision_info(src_path, output_dir, " ".join(sys.argv))
    dataset = facenet.get_dataset_dorm(args.input_dir)

    print("Creating networks and loading parameters")

    with tf.Graph().as_default():
        gpu_options = CONF["tf_gpu_options"]
        sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, log_device_placement=False))
        with sess.as_default():
            pnet, rnet, onet = align.detect_face.create_mtcnn(sess, None)

    params_dict = {"minsize": CONF["align_minsize"], "threshold": CONF["align_threshold"],  # three steps's threshold
                   "factor": CONF["align_factor"],  # scale factor
                   "pnet": pnet, "rnet": rnet, "onet": onet, }
    # Add a random key to the filename to allow alignment using multiple processes
    random_key = np.random.randint(0, high=99999)
    bounding_boxes_filename = os.path.join(output_dir, "bounding_boxes_%05d.txt" % random_key)

    output_ext = ".png"
    with open(bounding_boxes_filename, "w") as text_file:
        do_align(output_dir, text_file, dataset, params_dict, output_ext)


def do_align(output_dir, text_file, dataset, params_dict, output_ext=".png"):
    """

    :param output_dir:
    :param text_file:
    :param dataset:
    :param params_dict:
    :param output_ext:
    """
    nrof_images_total = 0
    nrof_successfully_aligned = 0
    if args.random_order:
        random.shuffle(dataset)
    print("Start aligning ...")
    for cls in dataset:
        output_class_dir = os.path.join(output_dir, cls.name)
        if not os.path.exists(output_class_dir):
            os.makedirs(output_class_dir)
            if args.random_order:
                cls.random_each_position()

        for image_path_indice, image_path in enumerate(cls.image_paths):
            nrof_images_total += 1
            filename = os.path.splitext(os.path.split(image_path)[1])[0]
            image_position = os.path.basename(os.path.dirname(image_path))
            if not os.path.exists(os.path.join(output_class_dir, image_position)):
                os.mkdir(os.path.join(output_class_dir, image_position))
            output_filename = os.path.join(output_class_dir, image_position, filename + output_ext)
            if not os.path.exists(output_filename):
                aligned_images_in_an_img = align_one_image(output_filename, image_path, text_file, params_dict)
                nrof_successfully_aligned += aligned_images_in_an_img
        print("Done aligned {} images".format(str(nrof_successfully_aligned)))

    print("Total number of images: %d" % nrof_images_total)
    print("Number of successfully aligned images: %d" % nrof_successfully_aligned)


def align_one_image(output_filename, image_path, text_file, params_dict):
    """

    :param output_filename:
    :param image_path:
    :param text_file:
    :param params_dict:
    :return: nrof_successfully_aligned
    """
    nrof_successfully_aligned = 0
    try:
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except (IOError, ValueError, IndexError) as e:
        error_message = "{}: {}".format(image_path, e)
        print(error_message)
    else:
        if img.ndim < 2:
            print('Unable to align "%s"' % image_path, " (ndim<2)")
            text_file.write("%s\n" % (output_filename))
            return nrof_successfully_aligned
        if img.ndim == 2:
            # py-lint: disable:no-member
            img = facenet.to_rgb(img)
        img = img[:, :, 0:3]

        bounding_boxes, _ = align.detect_face.detect_face(img, params_dict["minsize"], params_dict["pnet"],
                                                          params_dict["rnet"], params_dict["onet"],
                                                          params_dict["threshold"], params_dict["factor"], )
        nrof_faces = bounding_boxes.shape[0]

        if nrof_faces > 0:
            det = bounding_boxes[:, 0:4]
            det_arr = []
            img_size = np.asarray(img.shape)[0:2]
            if nrof_faces > 1:
                return nrof_successfully_aligned
            # nrof_faces == 1
            det_arr.append(np.squeeze(det))
            for i, det in enumerate(det_arr):
                det = np.squeeze(det)
                bb = np.zeros(4, dtype=np.int32)
                bb[0] = np.maximum(det[0] - args.margin / 2, 0)
                bb[1] = np.maximum(det[1] - args.margin / 2, 0)
                bb[2] = np.minimum(det[2] + args.margin / 2, img_size[1])
                bb[3] = np.minimum(det[3] + args.margin / 2, img_size[0])
                cropped = img[bb[1]: bb[3], bb[0]: bb[2], :]
                scaled = misc.imresize(cropped, (args.image_size, args.image_size), interp="bilinear")
                nrof_successfully_aligned += 1
                filename_base, file_extension = os.path.splitext(output_filename)
                if args.detect_multiple_faces:
                    output_filename_n = "{}_{}{}".format(filename_base, i, file_extension)
                else:
                    output_filename_n = "{}{}".format(filename_base, file_extension)
                misc.imsave(output_filename_n, scaled)
                text_file.write("%s %d %d %d %d\n" % (output_filename_n, bb[0], bb[1], bb[2], bb[3]))
        else:
            print('Noface: Unable to align "%s"' % image_path)
            text_file.write("%s\n" % output_filename)
        return nrof_successfully_aligned


def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=str, help="Directory with unaligned images.")
    parser.add_argument("output_dir", type=str, help="Directory with aligned face thumbnails.")
    parser.add_argument("--image_size", help="Image size (height, width) in pixels.", type=int, default=160, )
    parser.add_argument("--margin", type=int, default=44, help="Margin for the crop around \
                              the bounding box (height, width) in pixels.", )
    parser.add_argument("--random_order", action="store_true", help="Shuffles the order of images to enable alignment \
                              using multiple processes.", )
    parser.add_argument("--gpu_memory_fraction", type=float, default=1.0, help="Upper bound on the amount of GPU "
                                                                               "memory \
                              that will be used by the process.", )
    parser.add_argument("--detect_multiple_faces", type=bool, default=False,
                        help="Detect and align multiple faces per image.", )
    return parser.parse_args(argv)


if __name__ == "__main__":
    main(parse_arguments(sys.argv[1:]))
