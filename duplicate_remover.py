#!/usr/bin/env python3
import tempfile
import os
import time
import hashlib
import filecmp
import shutil

# In order to increase performance, we do not read all content of huge files
# To guarantee correct operation, additional verification of files with the same hash has been provided.
PACKAGE_SIZE = 4096          # bytes
MD5_MAX_PACKAGES = 12800     # 50 MB
VERSION = '1.0'

############################# INTERFACE FUNCTIONS #############################

def toReadableSize(byte_size):
    unit = ["B", "KB", "MB", "GB", "TB"]
    unit_idx = 0
    while byte_size // 10000 > 0 and unit_idx < 3:
        byte_size /= 1024
        unit_idx += 1
    return "{:.1f} ".format(byte_size) + unit[unit_idx]


def getFunctionalityOption(options):
    option = getNumberFromInput()
    while(option not in options):
        print("Provided invaild option number, try again : ", end = '')
        option = getNumberFromInput()
    return option

def getFilePrefix():
    prefix = input()
    if prefix != "":
        return prefix + "_"
    return ""

def getTrueFalseFromInput():
    while(True):
        response = input()
        if(response.lower() in ["y","yes"]):
            return True
        if(response.lower() in ["n","no"]):
            return False
        print("Invaild response,please choose one of (y/n): ", end = '')

def getDirFromInput():
    input_dir = input()
    while(not os.path.isdir(input_dir)):
        input_dir = input("Incorrect dir, try again: ")
    return input_dir

def getNumberFromInput():
    while(True):
        str_number = input()
        try:
            return int(str_number)
        except ValueError:
            print("Input is not a number, try again: ", end = '')


def getNumberNotLessThanXFromInput(x):
    number = getNumberFromInput()
    while(number < x):
        print("Number can't be less than %d , try again : ", x, end = '')
        number = getNumberFromInput()
    return number

def printStats(total_files, total_size, final_files, final_size):
    if total_files == 0 or total_size == 0:
        return
    removed_files = total_files - final_files
    removed_size = total_size - final_size
    reduced_files = final_files / total_files * 100
    reduced_size = final_size / total_size * 100
    print("\t\tFiles \tSize")
    print("Total: \t\t{} \t{}".format(total_files, toReadableSize(total_size) ))
    print("Left: \t\t{} \t{}".format(final_files, toReadableSize(final_size)))
    print("Removed: \t{} \t{}".format(removed_files, toReadableSize(removed_size)))
    print("Reduced to: \t{:.1f}% \t{:.1f}%".format(reduced_files, reduced_size))

############################# UTILS #############################

def removeDir(rm_dir):
    try:
        shutil.rmtree(rm_dir)
        return True
    except:
        return False


def waitOnEmptyDir(root_dir):
    isEmpty = False
    while not isEmpty:
        isEmpty = True
        for root, _, files in os.walk(root_dir):
            for file_name in files:
                if os.path.isfile(os.path.join(root, file_name)):
                    isEmpty = False
        time.sleep(0.05)

def waitOnPathExist(fileDir, exist = True):
    while os.path.isdir(fileDir) is not exist :
        time.sleep(0.05)

def createTempDir(parent_dir):
    temp_dir = tempfile.mkdtemp(dir = parent_dir)
    waitOnPathExist(temp_dir)
    return temp_dir

def getUniqueName(path, name_prefix, collection):
    _, extension = os.path.splitext(path)
    mtime = os.path.getmtime(path)
    m_time = time.strftime('%Y-%m-%d_%H_%M_%S', time.localtime(mtime))
    name = name_prefix + m_time
    if name in collection:
        collection[name] += 1
        name += "(" + str(collection[name]) + ")" + extension
    else:
        collection[name] = 0
        name = name + extension
    return name

def moveAndRenameFile(root, file_name, dst_dir, prefix, collection):
    old_path = os.path.join(root, file_name)
    new_name = getUniqueName(old_path, prefix, collection)
    new_path = os.path.join(dst_dir, new_name)
    shutil.move(old_path, new_path)

def moveFile(src_root, src_name, dst_root, dst_name):
    src = os.path.join(src_root, src_name)
    dst = os.path.join(dst_root, dst_name)
    shutil.move(src, dst)

def isFileInArray(file_path, path_array):
    for arr_file_path in path_array:
        if filecmp.cmp(file_path, arr_file_path, shallow = False):
            return True
    return False

def getHashOfFile(file_path):
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5()
        count = 0
        while (chunk := f.read(PACKAGE_SIZE)) and count < MD5_MAX_PACKAGES:
            count += 1
            file_hash.update(chunk)
    return str(os.stat(file_path).st_size) + file_hash.hexdigest()

def analyzeDir(root_dir):
    count = 0
    size = 0
    for root, _, files in os.walk(root_dir):
        for name in files:
            path = os.path.join(root, name)
            size += os.stat(path).st_size
            count += 1

    return count, size

############################# CODE #############################

def extractCollectionFromDir(root_dir):
    def doNothing(file_path):
        pass
    return collectFilesAndOnDuplicatedCallback(root_dir, doNothing)

def removeDuplicatedFiles(root_dir, collection = {}):
    def remove(file_path):
        try:
            os.remove(file_path)
        except:
            print("Error while deleting file ", file_path)
    return collectFilesAndOnDuplicatedCallback(root_dir, remove, collection)

def collectFilesAndOnDuplicatedCallback(root_dir, callback, collection = {}):
    for root, _, files in os.walk(root_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_hash = getHashOfFile(file_path)
            if file_hash in collection:
                if isFileInArray(file_path, collection[file_hash]):
                    callback(file_path)
                else:
                    collection[file_hash].append(file_path)
            else:
                collection[file_hash] = [file_path]
    return collection

def rename_files(root_dir, prefix, all_unique):
    collection = {}
    for root, _, files in os.walk(root_dir):
        temp_dir = createTempDir(root)
        if not all_unique:
            collection = {}
        for file_name in files:
            moveAndRenameFile(root, file_name, temp_dir, prefix, collection)
        for file_name in os.listdir(temp_dir):
            moveFile(temp_dir, file_name, root, file_name)
        waitOnEmptyDir(temp_dir)
        shutil.rmtree(temp_dir)


def moveFilesToRoot(root_dir):
    print("Provide prefix for file naming convention: ", end = '')
    prefix = getFilePrefix()
    collection = {}
    temp_dir = createTempDir(root_dir)
    for root, _, files in os.walk(root_dir):
        if root == temp_dir:
            continue
        for file_name in files:
            moveAndRenameFile(root, file_name, temp_dir, prefix, collection)
    for name in os.listdir(root_dir):
        path = os.path.join(root_dir, name)
        if path != temp_dir:
            removeDir(path)
    for name in os.listdir(temp_dir):
        moveFile(temp_dir, name, root_dir, name)
    waitOnEmptyDir(temp_dir)
    shutil.rmtree(temp_dir)


def menuRemoveWithSourceDir():
    print("Please provide 'DIRECTORY TO BE ANALYZED' and 'DIRECTORY TO BE CLEANED'.\n"
    + "(Files in 'DIRECTORY TO BE ANALYZED' directory will not be removed")

    print("Provide DIRECTORY TO BE ANALYZED: \t", end = '')
    analyze_dir = getDirFromInput()
    print("Provide DIRECTORY TO BE CLEANED: \t", end = '')
    removing_dir = getDirFromInput()
    collection = extractCollectionFromDir(analyze_dir)

    c1, s1 = analyzeDir(removing_dir)
    removeDuplicatedFiles(removing_dir, collection)

    print("Info: If you move files to root, files will be renamed")
    print("Do you want to move files to root directory? (y/n): ", end = '')
    move_files = getTrueFalseFromInput()
    if move_files:
        moveFilesToRoot(removing_dir)

    c2, s2 = analyzeDir(removing_dir)
    printStats(c1, s1, c2, s2)


def menuRemoveInDir():
    print("Provide root dir: ", end = '')
    root_dir = getDirFromInput()

    c1, s1 = analyzeDir(root_dir)
    removeDuplicatedFiles(root_dir)

    print("Info: If you move files to root, files will be renamed")
    print("Do you want to move files to root directory? (y/n): ", end = '')
    move_files = getTrueFalseFromInput()
    if move_files:
        moveFilesToRoot(root_dir)

    c2, s2 = analyzeDir(root_dir)
    printStats(c1, s1, c2, s2)


def menuRename():
    print("Provide root dir: ", end = '')
    root_dir = getDirFromInput()
    print("Provide prefix for file naming convention: ", end = '')
    prefix = getFilePrefix()
    print("Do names of all files in root dir tree should be unique? (y/n): ", end = '')
    all_unique = getTrueFalseFromInput()
    rename_files(root_dir, prefix, all_unique)


def menuMoveFilesToRoot():
    print("Provide root dir: ", end = '')
    root_dir = getDirFromInput()
    moveFilesToRoot(root_dir)


print("Duplicate Remover v" + VERSION + " - Script functionalities: \n" + \
        "(1) Remove any duplicate files in the specified directory.\n" + \
        "(2) Takes two directories and remove files from only one of them. It analyze one directory and then remove duplicated files from the other one.\n" + \
        "(3) Rename all files in directory tree using last modification datetime.\n" + \
        "(4) Move all files to root directory.")

print("Choose Functionality: ", end = '')
option = getFunctionalityOption([1, 2, 3, 4])

if(option == 1):
    menuRemoveInDir()
elif(option == 2):
    menuRemoveWithSourceDir()
elif(option == 3):
    menuRename()
elif(option == 4):
    menuMoveFilesToRoot()

input("Press Enter to continue...")
