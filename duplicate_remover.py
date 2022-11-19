#!/usr/bin/env python3
import logging
import tempfile
import os
import time
import hashlib
import filecmp
import shutil

# In order to increase performance, we do not read all content of huge files
# To guarantee correct operation, additional verification of files with the same hash has been provided.
PACKAGE_SIZE = 4096  # bytes
MD5_MAX_PACKAGES = 12800  # 50 MB
VERSION = '2.0'

logging.basicConfig()
logging.root.setLevel(logging.INFO)
logger = logging.getLogger('default')


############################# INTERFACE FUNCTIONS #############################

def to_readable_size(byte_size):
    unit = ["B", "KB", "MB", "GB", "TB"]
    unit_idx = 0
    while byte_size // 10000 > 0 and unit_idx < 3:
        byte_size /= 1024
        unit_idx += 1
    return "{:.1f} ".format(byte_size) + unit[unit_idx]


def get_functionality_option(options):
    number = get_number_from_input()
    while number not in options:
        print("Provided invaild option number, try again : ", end='')
        number = get_number_from_input()
    return number


def get_file_prefix():
    prefix = input()
    if prefix != "":
        return prefix + "_"
    return ""


def get_bool_from_input():
    while True:
        response = input()
        if response.lower() in ["y", "yes"]:
            return True
        if response.lower() in ["n", "no"]:
            return False
        print("Invalid response,please choose one of (y/n): ", end='')


def get_dir_from_input():
    input_dir = input()
    while not os.path.isdir(input_dir):
        input_dir = input("Incorrect dir, try again: ")
    input_dir = os.path.abspath(input_dir)
    return input_dir


def get_number_from_input():
    while True:
        str_number = input()
        try:
            return int(str_number)
        except ValueError:
            print("Input is not a number, try again: ", end='')


def get_number_from_input_not_less_than(x):
    number = get_number_from_input()
    while number < x:
        print("Number can't be less than %d , try again : ", x, end='')
        number = get_number_from_input()
    return number


def print_cleaner_stats(total_files, total_size, final_files, final_size):
    if total_files == 0 or total_size == 0:
        return
    removed_files = total_files - final_files
    removed_size = total_size - final_size
    reduced_files = final_files / total_files * 100
    reduced_size = final_size / total_size * 100
    print("\t\tFiles \tSize")
    print("Total: \t\t{} \t{}".format(total_files, to_readable_size(total_size)))
    print("Left: \t\t{} \t{}".format(final_files, to_readable_size(final_size)))
    print("Removed: \t{} \t{}".format(removed_files, to_readable_size(removed_size)))
    print("Reduced to: \t{:.1f}% \t{:.1f}%".format(reduced_files, reduced_size))


def print_sync_stats(
        count_total, size_total,
        count_skipped, size_skipped,
        count_removed, size_removed,
        count_copied, size_copied
):
    print("\t\tFiles \tSize")
    print("Total: \t\t{} \t{}".format(count_total, to_readable_size(size_total)))
    print("Skipped: \t{} \t{}".format(count_skipped, to_readable_size(size_skipped)))
    print("Slave Removed: \t{} \t{}".format(count_removed, to_readable_size(size_removed)))
    print("Slave Copied: \t{} \t{}".format(count_copied, to_readable_size(size_copied)))


############################# UTILS #############################

def remove_file(path):
    try:
        os.remove(path)
    except:
        print("Error while deleting file ", path)


def remove_dir(dir_path):
    try:
        shutil.rmtree(dir_path)
    except:
        print("Error while deleting dir ", dir_path)


def remove_empty_folders(path):
    if not os.path.isdir(path):
        return

    for f in os.listdir(path):
        fullpath = os.path.join(path, f)
        if os.path.isdir(fullpath):
            remove_empty_folders(fullpath)

    if len(os.listdir(path)) == 0:
        os.rmdir(path)


def deep_file_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def wait_on_empty_dir(root_dir):
    isEmpty = False
    while not isEmpty:
        isEmpty = True
        for root, _, files in os.walk(root_dir):
            for file_name in files:
                if os.path.isfile(os.path.join(root, file_name)):
                    isEmpty = False
        time.sleep(0.05)


def wait_on_path_exist(fileDir, exist=True):
    while os.path.isdir(fileDir) is not exist:
        time.sleep(0.05)


def create_temp_dir(parent_dir):
    temp_dir = tempfile.mkdtemp(dir=parent_dir)
    wait_on_path_exist(temp_dir)
    return temp_dir


def get_unique_name(path, name_prefix, collection):
    _, extension = os.path.splitext(path)
    m_time = os.path.getmtime(path)
    m_time = time.strftime('%Y-%m-%d_%H_%M_%S', time.localtime(m_time))
    name = name_prefix + m_time
    if name in collection:
        collection[name] += 1
        name += "(" + str(collection[name]) + ")" + extension
    else:
        collection[name] = 0
        name = name + extension
    return name


def move_and_rename_file(root, file_name, dst_dir, prefix, collection):
    old_path = os.path.join(root, file_name)
    new_name = get_unique_name(old_path, prefix, collection)
    new_path = os.path.join(dst_dir, new_name)
    shutil.move(old_path, new_path)


def move_file(src_root, src_name, dst_root, dst_name):
    src = os.path.join(src_root, src_name)
    dst = os.path.join(dst_root, dst_name)
    shutil.move(src, dst)


def get_duplicates_from_array(file_path, path_array):
    duplicates = []
    for arr_file_path in path_array:
        if filecmp.cmp(file_path, arr_file_path, shallow=False):
            duplicates.append(arr_file_path)
    return duplicates


def get_hash_of_file(file_path):
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5()
        count = 0
        while (chunk := f.read(PACKAGE_SIZE)) and count < MD5_MAX_PACKAGES:
            count += 1
            file_hash.update(chunk)
    return str(os.stat(file_path).st_size) + file_hash.hexdigest()


def analyze_dir(root_dir):
    count = 0
    size = 0
    for root, _, files in os.walk(root_dir):
        for name in files:
            path = os.path.join(root, name)
            size += os.stat(path).st_size
            count += 1

    return count, size


def analyze_paths(paths):
    size = 0
    for path in paths:
        size += os.stat(path).st_size

    return len(paths), size


############################# CODE #############################

def extract_collection_from_dir(root_dir, initCollection={}):
    def do_nothing(*args):
        pass

    return collect_files_with_callbacks(root_dir, do_nothing, do_nothing, True, True, initCollection)


def remove_duplicated_files(root_dir, initCollection={}):
    def do_nothing(*args):
        pass

    def remove(file_path, files_with_same_content):
        remove_file(file_path)

    return collect_files_with_callbacks(root_dir, remove, do_nothing, False, True, initCollection)


def find_existing_and_extra_files(base_dir, work_dir):
    base_dir_existing = set()
    work_dir_extra_files = set()
    work_dir_existing_in_other_path = set()

    def on_new(file_path):
        work_dir_extra_files.add(file_path)

    def on_duplicate(file_path, files_with_same_content):
        base_dir_path = os.path.join(base_dir, os.path.relpath(file_path, work_dir))
        if base_dir_path in files_with_same_content:
            base_dir_existing.add(base_dir_path)
        else:
            work_dir_existing_in_other_path.add(file_path)

    base_dir_collection = extract_collection_from_dir(base_dir)
    collect_files_with_callbacks(work_dir, on_duplicate, on_new, False, False, base_dir_collection)

    return base_dir_collection, base_dir_existing, work_dir_extra_files, work_dir_existing_in_other_path


def collect_files_with_callbacks(root_dir,
                                 on_duplicate_callback,
                                 on_new_callback,
                                 collectOnDuplicate,
                                 collectOnNew,
                                 collection={}):
    for root, _, files in os.walk(root_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_hash = get_hash_of_file(file_path)
            if file_hash in collection:
                files_with_same_content = get_duplicates_from_array(file_path, collection[file_hash])
                if len(files_with_same_content) > 0:
                    on_duplicate_callback(file_path, files_with_same_content)
                    if collectOnDuplicate:
                        collection[file_hash].append(file_path)
                else:
                    on_new_callback(file_path)
                    if collectOnNew:
                        collection[file_hash].append(file_path)
            else:
                on_new_callback(file_path)
                if collectOnNew:
                    collection[file_hash] = [file_path]
    return collection


def rename_files(root_dir, prefix, all_unique):
    collection = {}
    for root, _, files in os.walk(root_dir):
        temp_dir = create_temp_dir(root)
        if not all_unique:
            collection = {}
        for file_name in files:
            move_and_rename_file(root, file_name, temp_dir, prefix, collection)
        for file_name in os.listdir(temp_dir):
            move_file(temp_dir, file_name, root, file_name)
        wait_on_empty_dir(temp_dir)
        shutil.rmtree(temp_dir)


def move_files_to_root(root_dir, prefix):
    collection = {}
    temp_dir = create_temp_dir(root_dir)
    for root, _, files in os.walk(root_dir):
        if root == temp_dir:
            continue
        for file_name in files:
            move_and_rename_file(root, file_name, temp_dir, prefix, collection)
    for name in os.listdir(root_dir):
        path = os.path.join(root_dir, name)
        if path != temp_dir:
            remove_dir(path)
    for name in os.listdir(temp_dir):
        move_file(temp_dir, name, root_dir, name)
    wait_on_empty_dir(temp_dir)
    shutil.rmtree(temp_dir)


def synchronize_data(master_dir, slave_dir):
    m_collection, m_existing, s_extra, s_existing_in_other_path = find_existing_and_extra_files(master_dir, slave_dir)

    to_be_skipped = m_existing
    to_be_removed = s_extra.union(s_existing_in_other_path)

    count_removed, size_removed = analyze_paths(to_be_removed)
    for path in to_be_removed:
        logger.info("Removing extra file: " + os.path.relpath(path, slave_dir))
        remove_file(path)

    logger.info("Removing empty directories")
    remove_empty_folders(slave_dir)

    master_files = {path for paths in m_collection.values() for path in paths}
    to_be_copied = master_files.difference(to_be_skipped)
    for master_file in to_be_copied:
        rel_path = os.path.relpath(master_file, master_dir)
        logger.info("Moving file: " + rel_path)
        slave_file = os.path.join(slave_dir, rel_path)
        deep_file_copy(master_file, slave_file)

    count_total, size_total = analyze_dir(master_dir)
    count_skipped, size_skipped = analyze_paths(to_be_skipped)
    count_copied, size_copied = analyze_paths(to_be_copied)

    print_sync_stats(
        count_total, size_total,
        count_skipped, size_skipped,
        count_removed, size_removed,
        count_copied, size_copied
    )


############################### MENU INTERFACES ###############################


def menu_remove_with_source_dir():
    print("Please provide 'DIRECTORY TO BE ANALYZED' and 'DIRECTORY TO BE CLEANED'.\n"
          + "(Files in 'DIRECTORY TO BE ANALYZED' directory will not be removed")

    print("Provide DIRECTORY TO BE ANALYZED: \t", end='')
    analyse_dir_path = get_dir_from_input()
    print("Provide DIRECTORY TO BE CLEANED: \t", end='')
    removing_dir_path = get_dir_from_input()
    collection = extract_collection_from_dir(analyse_dir_path)

    c1, s1 = analyze_dir(removing_dir_path)
    remove_duplicated_files(removing_dir_path, collection)

    print("Info: If you move files to root, files will be renamed")
    print("Do you want to move files to root directory? (y/n): ", end='')
    move_files = get_bool_from_input()
    if move_files:
        print("Provide prefix for file naming convention: ", end='')
        prefix = get_file_prefix()
        move_files_to_root(removing_dir_path, prefix)

    c2, s2 = analyze_dir(removing_dir_path)
    print_cleaner_stats(c1, s1, c2, s2)


def menu_remove_in_dir():
    print("Provide root dir: ", end='')
    root_dir = get_dir_from_input()

    c1, s1 = analyze_dir(root_dir)
    remove_duplicated_files(root_dir)

    print("Info: If you move files to root, files will be renamed")
    print("Do you want to move files to root directory? (y/n): ", end='')
    move_files = get_bool_from_input()
    if move_files:
        print("Provide prefix for file naming convention: ", end='')
        prefix = get_file_prefix()
        move_files_to_root(root_dir, prefix)

    c2, s2 = analyze_dir(root_dir)
    print_cleaner_stats(c1, s1, c2, s2)


def menu_rename():
    print("Provide root dir: ", end='')
    root_dir = get_dir_from_input()
    print("Provide prefix for file naming convention: ", end='')
    prefix = get_file_prefix()
    print("Do names of all files in root dir tree should be unique? (y/n): ", end='')
    all_unique = get_bool_from_input()
    rename_files(root_dir, prefix, all_unique)


def menu_move_files_to_root():
    print("Provide root dir: ", end='')
    root_dir = get_dir_from_input()
    print("Provide prefix for file naming convention: ", end='')
    prefix = get_file_prefix()
    move_files_to_root(root_dir, prefix)


def menu_sync_data():
    print("Provide master dir: ", end='')
    master_dir = get_dir_from_input()
    print("Provide slave dir: ", end='')
    slave_dir = get_dir_from_input()
    synchronize_data(master_dir, slave_dir)


def start_menu():
    print(
        "Duplicate Remover v" + VERSION + " - Script functionalities: \n" +
        "(1) Remove any duplicate files in the specified directory.\n" +
        "(2) Takes two directories and remove files from only one of them. " +
        "It analyze one directory and then remove duplicated files from the other one.\n" +
        "(3) Rename all files in directory tree using last modification datetime.\n" +
        "(4) Move all files to root directory.\n" +
        "(5) Synchronize data in directories"
    )

    print("Choose Functionality: ", end='')
    option = get_functionality_option([x for x in range(1, 6)])

    if option == 1:
        menu_remove_in_dir()
    elif option == 2:
        menu_remove_with_source_dir()
    elif option == 3:
        menu_rename()
    elif option == 4:
        menu_move_files_to_root()
    elif option == 5:
        menu_sync_data()


start_menu()
input("Press Enter to continue...")
