import os
import argparse
from shutil import rmtree, copyfile
from functools import reduce

supported_img_ext = [".png", ".jpg", ".bmp", ".jpeg"]


def main():
    handler = argparse.ArgumentParser()
    handler.add_argument("--imgdir", "-d")
    handler.add_argument("--outdir", "-o")
    handler.add_argument("--format", "-f", default=False, action='store_true')
    flags = handler.parse_args()
    imgdir = os.path.expanduser(flags.imgdir)
    format = flags.format
    outdir = os.path.expanduser(flags.outdir)
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    assert os.path.exists(imgdir), "{} is not exists.".format(imgdir)
    # Classes dir
    listdirs = [_dir for _dir in os.listdir(imgdir) if
                os.path.exists(os.path.join(imgdir, _dir)) and not os.path.isfile(os.path.join(imgdir, _dir))]
    for index, item in enumerate(listdirs):
        # rename_folder(imgdir, item, str(index + 1).zfill(4), format_file_name=True)
        aggregate_subfolder(imgdir, outdir, item, format)
    print("Done.")


def concat(arr_1, arr_2):
    return arr_1 + arr_2


def rename_folder(basedir, folder_name, new_folder_name, format_file_name=False, supported_img_ext=supported_img_ext):
    os.rename(os.path.join(basedir, folder_name), os.path.join(basedir, new_folder_name))

    if format_file_name:
        file_list = [_file for _file in os.listdir(os.path.join(basedir, new_folder_name)) if
                     os.path.isfile(os.path.join(basedir, new_folder_name, _file)) and
                     os.path.splitext(os.path.join(basedir, new_folder_name, _file))[-1].lower() in supported_img_ext]
        for file_idx, file_ in enumerate(file_list):
            rename_file(os.path.join(basedir, new_folder_name), file_,
                        new_folder_name + "_" + str(file_idx + 1).zfill(4) + os.path.splitext(file_)[-1])


def rename_new_file(filename_with_path, indice, format_file_name=False):
    path_parts = filename_with_path.split(os.sep)
    assert len(path_parts) >= 3, "Wrong input format.\n"
    if format_file_name:
        path_parts[-2] = path_parts[0] + "_" + str(indice + 1).zfill(4)
    else:
        path_parts[-2] = path_parts[-2] + "_" + path_parts[-1]
    path_parts = path_parts[:-1]
    return str(os.sep).join(path_parts)


def aggregate_subfolder(input_dir, output_dir, folder_name, format_file_name=False, support_img_ext=supported_img_ext):
    if not os.path.exists(os.path.join(output_dir, folder_name)):
        os.mkdir(os.path.join(output_dir, folder_name))
    # subfolders = os.listdir(os.path.join(input_dir, folder_name))
    subfolders = [os.path.join(folder_name, subfolder) for subfolder in
                  os.listdir(os.path.join(input_dir, folder_name))]
    input_files = [list(map(lambda x: os.path.join(subfolder, x), os.listdir(os.path.join(input_dir, subfolder)))) for
                   subfolder in subfolders]
    if len(input_files) == 0:
        return
    input_files = reduce(concat, input_files)
    # output_files = [rename_new_file(input) for input in input_files]
    for indice, input_file in enumerate(input_files):
        copy_file(input_file, rename_new_file(input_file, indice, format_file_name=format_file_name), input_dir,
                  output_dir)


def rename_file(file_basedir, file_name, file_new_name):
    os.rename(os.path.join(file_basedir, file_name), os.path.join(file_basedir, file_new_name))


def copy_file(input_file, output_file, input_dir, output_dir):
    copyfile(os.path.join(input_dir, input_file), os.path.join(output_dir, output_file))


main()
