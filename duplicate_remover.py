#!/usr/bin/env python3
import ctypes
import logging
import subprocess
import sys
import tempfile
import os
import time
import hashlib
import filecmp
import shutil
from functools import wraps

# In order to increase performance, we do not read all content of huge files
# To guarantee correct operation, additional verification of files with the same hash has been provided.
PACKAGE_SIZE = 102400  # 100 KB
MD5_MAX_PACKAGES = 1  # 10 KB
VERSION = '2.0'

logging.basicConfig()
logging.root.setLevel(logging.DEBUG)
logger = logging.getLogger('default')


############################# INTERFACE FUNCTIONS #############################

def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Function {func.__name__}{args} {kwargs} Took {total_time:.4f} seconds')
        return result

    return timeit_wrapper


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        return os.getuid() == 0


def rerun_with_admin_rights():
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    except:
        subprocess.call(['sudo', 'python3', *sys.argv])


def to_readable_size(byte_size):
    unit = ["B", "KB", "MB", "GB", "TB"]
    unit_idx = 0
    while byte_size // 10000 > 0 and unit_idx < 3:
        byte_size /= 1024
        unit_idx += 1
    return "{:.1f} ".format(byte_size) + unit[unit_idx]


def get_number_from_list(options):
    number = get_number_from_input()
    while number not in options:
        print("Provided invalid number, try again : ", end='')
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
        print("Invalid response, please choose one of (y/n): ", end='')


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


def print_cleaner_stats(initial_count, initial_size, final_count, final_size):
    if initial_count == 0 or initial_size == 0:
        return
    removed_files = initial_count - final_count
    removed_size = initial_size - final_size
    reduced_files = final_count / initial_count * 100
    reduced_size = final_size / initial_size * 100
    print("\t\tFiles \tSize")
    print("Initial: \t{} \t{}".format(initial_count, to_readable_size(initial_size)))
    print("Left: \t\t{} \t{}".format(final_count, to_readable_size(final_size)))
    print("Removed: \t{} \t{}".format(removed_files, to_readable_size(removed_size)))
    print("Reduced to: \t{:.1f}% \t{:.1f}%".format(reduced_files, reduced_size))


def print_sync_stats(
        count_total, size_total,
        count_removed, size_removed,
        count_copied, size_copied
):
    print("\t\tFiles \tSize")
    print("Total: \t\t{} \t{}".format(count_total, to_readable_size(size_total)))
    print("Slave Removed: \t{} \t{}".format(count_removed, to_readable_size(size_removed)))
    print("Slave Copied: \t{} \t{}".format(count_copied, to_readable_size(size_copied)))


############################# UTILS #############################

def remove_file(path):
    try:
        os.remove(path)
    except Exception as e:
        logger.info("Error while deleting file " + path)
        logger.exception(e)


def remove_dir(dir_path):
    try:
        shutil.rmtree(dir_path)
        wait_on_dir_exist(dir_path, exist=False)
    except Exception as e:
        logger.info("Error while removing dir " + dir_path)
        logger.exception(e)


def remove_empty_folders(path):
    if not os.path.isdir(path):
        return

    for f in os.listdir(path):
        fullpath = os.path.join(path, f)
        if os.path.isdir(fullpath):
            remove_empty_folders(fullpath)

    if len(os.listdir(path)) == 0:
        remove_dir(path)


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


def wait_on_dir_exist(fileDir, exist=True):
    while os.path.isdir(fileDir) is not exist:
        time.sleep(0.05)


def create_temp_dir(parent_dir):
    temp_dir = tempfile.mkdtemp(dir=parent_dir)
    wait_on_dir_exist(temp_dir)
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


def has_duplicates_in_array(file_path, array_base_path, rel_path_array):
    for arr_file_path in map(lambda p: os.path.join(array_base_path, p), rel_path_array):
        if filecmp.cmp(file_path, arr_file_path, shallow=False):
            return True
    return False


def get_hash_of_file(file_path):
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256()
        count = 0
        while (chunk := f.read(PACKAGE_SIZE)) and count < MD5_MAX_PACKAGES:
            count += 1
            file_hash.update(chunk)
    return str(os.stat(file_path).st_size) + file_hash.hexdigest()


def analyze_dir(root_dir, recursively=True):
    count = 0
    size = 0

    if recursively:
        for root, _, files in os.walk(root_dir):
            for name in files:
                path = os.path.join(root, name)
                size += os.stat(path).st_size
                count += 1
    else:
        for filename in os.listdir(root_dir):
            path = os.path.join(root_dir, filename)
            if os.path.isfile(path):
                size += os.stat(path).st_size
                count += 1

    return count, size


def analyze_paths(paths):
    size = 0
    for path in paths:
        size += os.stat(path).st_size

    return len(paths), size


############################# CODE #############################

def for_files(root_dir, debug_msg, callback):
    for root, _, files in os.walk(root_dir):
        logger.debug(debug_msg + root)
        for file_name in files:
            file_path = os.path.join(root, file_name)
            rel_path = os.path.relpath(file_path, root_dir)
            file_hash = get_hash_of_file(file_path)
            callback(file_path, rel_path, file_hash)


def collect_files_by_hash(root_dir):
    collection = {}

    def callback(file_path, rel_path, file_hash):
        if file_hash in collection:
            collection[file_hash].append(rel_path)
        else:
            collection[file_hash] = [rel_path]

    for_files(root_dir, "Collecting files from: ", callback)
    return collection


def collect_files_by_rel_path(root_dir):
    collection = {}

    def callback(file_path, rel_path, file_hash):
        collection[rel_path] = file_hash

    for_files(root_dir, "Collecting files from: ", callback)
    return collection


def remove_duplicated_files(root_dir):
    collection = {}

    def callback(file_path, rel_path, file_hash):
        if file_hash in collection:
            if has_duplicates_in_array(file_path, root_dir, collection[file_hash]):
                logger.info("Removing duplicated file: " + os.path.relpath(file_path, root_dir))
                remove_file(file_path)
            else:
                collection[file_hash].append(rel_path)
        else:
            collection[file_hash] = [rel_path]

    for_files(root_dir, "Removing duplicated files from: ", callback)


def remove_duplicated_files_with_source_dir(source_dir, cleaning_dir):
    collection = collect_files_by_hash(source_dir)

    def callback(file_path, rel_path, file_hash):
        if file_hash in collection and has_duplicates_in_array(file_path, source_dir, collection[file_hash]):
            logger.info("Removing duplicated file: " + os.path.relpath(file_path, cleaning_dir))
            remove_file(file_path)

    for_files(cleaning_dir, "Removing duplicated files from: ", callback)


def find_existing_and_extra_files_by_path(base_dir, work_dir, with_deep_compare=False):
    logger.info("Reading Base dir - Started")
    base_dir_collection = collect_files_by_rel_path(base_dir)
    logger.info("Reading Base dir - Finished")

    logger.info("Reading Work dir - Started")
    work_dir_collection = collect_files_by_rel_path(work_dir)
    logger.info("Reading Work dir - Finished")

    logger.info("Checking differences - Started")
    base_rel_paths = set(base_dir_collection.keys())
    work_rel_paths = set(work_dir_collection.keys())

    new_files = base_rel_paths.difference(work_rel_paths)
    extra_files = work_rel_paths.difference(base_rel_paths)
    existing_files = set()

    for path in work_rel_paths.intersection(base_rel_paths):
        if with_deep_compare:
            base_file_path = os.path.join(base_dir, path)
            work_file_path = os.path.join(work_dir, path)
            if filecmp.cmp(base_file_path, work_file_path, shallow=False):
                existing_files.add(path)
            else:
                new_files.add(path)
                extra_files.add(path)
        elif base_dir_collection[path] == work_dir_collection[path]:
            existing_files.add(path)
        else:
            new_files.add(path)
            extra_files.add(path)

    logger.info("Checking differences - Finished")

    return existing_files, new_files, extra_files


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


def synchronize_data(master_dir, slave_dir, deep_compare):
    existing_files, new_files, extra_files = find_existing_and_extra_files_by_path(master_dir, slave_dir, deep_compare)

    to_be_removed = list(map(lambda p: os.path.join(slave_dir, p), extra_files))
    to_be_copied = list(map(lambda p: os.path.join(master_dir, p), new_files))

    count_total, size_total = analyze_dir(master_dir)
    count_copied, size_copied = analyze_paths(to_be_copied)
    count_removed, size_removed = analyze_paths(to_be_removed)

    logger.info("Removing extra files - Started")
    for path, rel_path in zip(to_be_removed, extra_files):
        logger.info("Removing extra file: " + rel_path)
        remove_file(path)
    logger.info("Removing extra files - Finished")

    logger.info("Removing empty directories - Started")
    remove_empty_folders(slave_dir)
    logger.info("Removing empty directories - Finished")

    logger.info("Copying new files - Started")
    for master_path, rel_path in zip(to_be_copied, new_files):
        logger.info("Copying file: " + rel_path)
        slave_path = os.path.join(slave_dir, rel_path)
        deep_file_copy(master_path, slave_path)
    logger.info("Copying new files - Finished")

    print_sync_stats(
        count_total, size_total,
        count_removed, size_removed,
        count_copied, size_copied
    )


def remove_files_with_same_name(root_path, recursively=True):
    for dir_path, _, filenames in os.walk(root_path):
        print('Current path: ' + dir_path)
        register = {}
        for filename in filenames:
            name, file_extension = os.path.splitext(filename)
            if not name or len(name) == 0 or not file_extension or len(file_extension) == 0:
                continue
            if name in register:
                register[name].append(file_extension)
            else:
                register[name] = [file_extension]

        register = {k: tuple(sorted(v)) for k, v in register.items() if len(v) > 1}
        extensions_tuples = {tuple(v) for v in register.values()}
        extensions_tuples = {tuple(map(lambda s: s.upper(), v)) for v in extensions_tuples}

        if len(extensions_tuples) == 0:
            print('Nothing to do in directory.')
        else:
            decisions = {}
            for case in extensions_tuples:
                case_decisions = {}
                print('Detected same filename with extensions: ' + ', '.join(case))
                for ext in case:
                    print('Remove ' + ext + ' file (y/n) ? ', end='')
                    case_decisions[ext] = get_bool_from_input()
                decisions[case] = case_decisions

            for name, exts in register.items():
                case_decisions = decisions[tuple(map(lambda s: s.upper(), exts))]
                for ext in exts:
                    if case_decisions[ext.upper()]:
                        filename = name + ext
                        logger.info('Removing file: ' + filename)
                        remove_file(os.path.join(dir_path, filename))

        if not recursively:
            break


############################### MENU INTERFACES ###############################


def menu_remove_with_source_dir():
    print("Please provide 'DIRECTORY TO BE ANALYZED' and 'DIRECTORY TO BE CLEANED'.\n"
          + "(Files in 'DIRECTORY TO BE ANALYZED' directory will not be removed")

    print("Provide DIRECTORY TO BE ANALYZED: \t", end='')
    analyse_dir_path = get_dir_from_input()
    print("Provide DIRECTORY TO BE CLEANED: \t", end='')
    removing_dir_path = get_dir_from_input()

    c1, s1 = analyze_dir(removing_dir_path)

    remove_duplicated_files_with_source_dir(analyse_dir_path, removing_dir_path)

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
    print("Do you want to use deep file comparison? If no hash and size comparison will be used: ", end='')
    deep_compare = get_bool_from_input()

    synchronize_data(master_dir, slave_dir, deep_compare)


def menu_remove_files_with_same_name():
    print("Provide dir: ", end='')
    root_dir = get_dir_from_input()
    print("Do you want to perform the action for subdirectories as well? (y/n): ", end='')
    recursively = get_bool_from_input()
    c1, s1 = analyze_dir(root_dir, recursively=recursively)
    remove_files_with_same_name(root_dir, recursively)
    c2, s2 = analyze_dir(root_dir, recursively=recursively)
    print_cleaner_stats(c1, s1, c2, s2)


def start_menu():
    print(
        "Duplicate Remover v" + VERSION + " - Script functionalities: \n" +
        "(1) Remove any duplicate files in the specified directory.\n" +
        "(2) Takes two directories and remove files from only one of them. " +
        "It analyze one directory and then remove duplicated files from the other one.\n" +
        "(3) Rename all files in directory tree using last modification datetime.\n" +
        "(4) Move all files to root directory.\n" +
        "(5) Synchronize data in directories.\n"
        "(6) Remove files with same name basing on extensions."
    )

    print("Choose Functionality: ", end='')
    option = get_number_from_list([x for x in range(1, 7)])

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
    elif option == 6:
        menu_remove_files_with_same_name()


if is_admin():
    start_menu()
    input("Press Enter to continue...")
else:
    rerun_with_admin_rights()
