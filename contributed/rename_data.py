import os
import cv2
import sys
import xml.etree.ElementTree as ET
import argparse
from datetime import datetime as dt
from functools import reduce


# Usage: -d <imgDir> -aS <labelDir>
def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-d', '--imgDir', help='Images directory')
    parser.add_argument('-e', '--ext', default='png', help='extension wanna change to')

    args = parser.parse_args()
    dirname = os.getcwd()
    imgdir = args.imgDir
    new_extenstion = args.ext

    # absImgDir = dirname + '/' + imgDir
    abs_dir = os.path.abspath(imgdir)

    if not os.path.exists(imgdir):
        sys.exit('Error! ImgDir is not correct.')

    folders = os.listdir(abs_dir)
    # files = clearOldName(files, imgDir)
    # files = [filename for filename in files if os.path.isfile(os.path.join(absImgDir, filename))]

    folders = [folder for folder in folders if os.path.isdir(os.path.join(imgdir, folder))]
    #  if os.path.isdir(folder)
    folders = [[os.path.join(folder, file_dir) for file_dir in os.listdir(os.path.join(imgdir, folder))] for folder in
               folders]
    folders = reduce((lambda x, y: x + y), folders)
    folders = list(map(lambda x: os.path.join(imgdir, x), folders))
    files = [[os.path.join(folder, file_dir) for file_dir in os.listdir(folder)] for folder in folders]
    files = reduce((lambda x, y: x + y), files)

    # files = [[os.path.join(folder, file_dir) for file_dir in os.listdir(folder)] for folder in folders]

    print("Starting............")
    print("--------------------")

    for idx, filename in enumerate(files):
        # rename_prepend(filename, str(idx) + "_")
        rename_ext(filename, ext=new_extenstion)

    print("Done")


def get_ext(filename):
    parts = filename.split(".")
    return parts[len(parts) - 1]


def rename_ext(filename, ext):
    dir_, file_ = os.path.split(filename)
    name_, ext_ = os.path.splitext(file_)
    # if ext_.lower() not in [".bmp", ".jpg", ".png"]:
    #     return
    if ext is not None and ext[0] == '.':
        ext = ext[1:]
    newname = os.path.join(dir_, name_ + "." + ext)
    os.rename(filename, newname)


def rename_prepend(filename, prepend):
    # ext = "." + getExt(filename)
    # nameNoExt = ".".join(filename.split(".")[:-1])
    dir_, file_ = os.path.split(filename)
    name_, ext_ = os.path.splitext(file_)
    if ext_.lower() not in [".bmp", ".jpg", ".png"]:
        return
    newname = os.path.join(dir_, prepend + file_)
    os.rename(filename, newname)


def clear_old_name(files, imgdir):
    for idx, file in enumerate(files):
        ext = "." + getExt(file)
        os.rename(os.path.join(imgdir, file),
                  os.path.join(imgdir, str(dt.now().strftime("%Y%m%d%H%M%S.%f")) + "_" + str(idx) + ext))
    return os.listdir(imgdir)


main()
