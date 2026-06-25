import os
import numpy as np
from numpy.dtypes import StringDType
from datetime import datetime
import argparse
import gc
import subprocess
from enum import Enum
import shutil

class Task(Enum):
    name2keywords = 1
    manual = 2

class WriteMode(Enum):
    overwrite = 1
    add = 2
    remove = 3

class MatchCase(Enum):
    keep = 1
    lower = 2
    upper = 3

_INPUT_PATH = "./input/"
_TEMP_PATH = "./temp/"
_tags = [] 
_USE_SIDECAR_FILE = False
_TASK = Task.name2keywords
_WRITE_MODE = WriteMode.add
_KEYWORDS_START_SYMBOL = ""
_TREE_OFFSET = 0
_ALLOWED_SUBJECTS_PATH = "./whitelist.txt"
_IGNORED_SUBJECTS_PATH = "./blacklist.txt"

arg_descriptions = {
    "INPUT_PATH": "input media path. Default value: ./input/",
    "TEMP_PATH": "output temporary media path (*CAN BE AUTOMATICALLY DELETED!*). Default value: ./temp/",
    "tags": "set any number of comma (,) separated xmp subject tags. Example 'tag1,tag2, name'. Default value is empty.",
    "USE_SIDECAR_FILE": "whether to use separate (sidecar) files for writing metadata. Default value is 0 (false).",
    "WRITE_MODE": "mode for writing subject's metadata (overwrite,add,remove). Default value is add.",
    "KEYWORDS_START_SYMBOL": "used for auto-tagging to process only text after ['start']. Default value is empty ''.",
    "TREE_OFFSET": "used for auto-tagging to determine if parent folder's name should be used instead of file name. Positive number indicate number of levels in file hierarchy. Default value is 0",
    "ALLOWED_SUBJECTS_PATH": "input whitelist file path with allowed subject tags (formatted 1 per line in .txt file). Default value: ./whitelist.txt",
    "IGNORED_SUBJECTS_PATH": "input blacklist file path with disallowed subject tags (formatted 1 per line in .txt file). Default value: ./blacklist.txt",
}
    
def changeExtension(path, newExt):
    words = path.split('.')
    path2 = words[0]
    for i in range(1, len(words)-1):
        path2 = path2 + '.' + words[i]
    path2 = path2 + newExt
    return path2

def rstrip(txt, remove_txt):
    """Remove text fragment from the end (if exists)

    Args:
        txt (str): input text to be processed
        remove_txt (str): input text to be removed

    Returns:
        str: text without ending of "remove_txt"
    """

    word2 = txt
    n = len(remove_txt)
    if((n <= len(word2)) and (n > 0)):
        if(word2[len(word2)-n:] == remove_txt):
            word2 = word2[:len(word2)-n]
    return word2

def split_path_filename(path):
    values = path.split('/')
    path2 = ""
    file = values[-1]
    for i in range(len(values)-1):
        path2 = path2 + values[i] + "/"
    return path2, file

def clean_tags(tags, matchCase=MatchCase.keep):
    cleaned_tags = []
    for i in range(len(tags)):     
        value = tags[i].strip(' ')
        value = value.strip('_')
        value = value.replace('  ', ' ')
        if(matchCase == MatchCase.lower):
            value = value.lower()
        elif(matchCase == MatchCase.upper):
            value = value.upper()
        if(len(value) > 0):
            cleaned_tags.append(value)
    return cleaned_tags

def split_tags(tags_text, splitter=','):
    raw_tags = tags_text.split(splitter)
    separated_tags = clean_tags(raw_tags)
    return separated_tags

def file2keywords(file, keywords_start_symbol=_KEYWORDS_START_SYMBOL, tree_offset=_TREE_OFFSET):
    """Find keywords in file name.

    Args:
        file (_type_): path of file which will be used for keywords
        keywords_start_symbol (str, optional): symbol that precedes the beginning of substring with keywords. Defaults to _KEYWORDS_START_SYMBOL.
        tree_offset (int, optional): determines if parent folder's name (or any folder above) should be used instead of file name. Defaults to _TREE_OFFSET.

    Returns:
        list[str]: list of keywords
    """
    raw_name = file
    for i in range(tree_offset):
        raw_name = os.path.dirname(raw_name)
    sidecar_extension = '.xmp'
    raw_name = rstrip(raw_name, sidecar_extension)
    raw_name = os.path.basename(raw_name)
    ind = raw_name.find('.')
    if(ind >= 0):
        raw_name = '.'.join(raw_name.split('.')[:-1])
    indices = []
    ind = 0
    if(len(keywords_start_symbol)>0):
        while True:
            ind = raw_name.find(keywords_start_symbol, ind)
            if(ind < 0):
                break
            indices.append(ind)
            ind += len(keywords_start_symbol)
    else:
        indices = [-1]
    raw_keywords = ""
    if(len(indices)>0):
        raw_keywords = raw_name[indices[-1]+1:]
    else:
        return None
    
    separated_keywords = split_tags(raw_keywords)
    return separated_keywords

def filterKeywords(keywords, matchCase=MatchCase.keep, remove_texts=[], allowed_subjects=[], ignored_subjects=[]):
    keywords2 = keywords.copy()
    for i in range(len(keywords2)):
        if keywords2[i] is None:
            continue
        keywords2[i] = keywords2[i].strip(' ')
        if(matchCase == MatchCase.lower):
            keywords2[i] = keywords2[i].lower()
        elif(matchCase == MatchCase.upper):
            keywords2[i] = keywords2[i].upper()
        for txt in remove_texts:
            keywords2[i] = keywords2[i].replace(txt, '')
        if(len(ignored_subjects) > 0):
            if keywords2[i] in ignored_subjects:
                keywords2[i] = None
        if(len(allowed_subjects) > 0):
            matched = False
            if not keywords2[i] in allowed_subjects:
                #check for partial match
                words = split_tags(keywords2[i], ' ')
                if len(words) > 1:
                    keyword1 = words[0] + " " + words[1]
                    keyword2 = words[-2] + " " + words[-1]
                    if keyword1 in allowed_subjects:
                        keywords2[i] = keyword1
                        matched = True
                    elif keyword2 in allowed_subjects:
                        keywords2[i] = keyword2
                        matched = True
            else:
                matched = True
            if not matched:
                keywords2[i] = None
    dt = StringDType(na_object=None)
    keywords2 = np.array(keywords2, dtype=dt)
    keywords2 = keywords2[keywords2 != None]
    return keywords2.tolist()   
                
def init(  INPUT_PATH=_INPUT_PATH, 
            TEMP_PATH=_TEMP_PATH, 
            tags=_tags, 
            USE_SIDECAR_FILE=_USE_SIDECAR_FILE,
            TASK = _TASK,
            WRITE_MODE=_WRITE_MODE,
            KEYWORDS_START_SYMBOL=_KEYWORDS_START_SYMBOL,
            TREE_OFFSET=_TREE_OFFSET,
            ALLOWED_SUBJECTS_PATH=_ALLOWED_SUBJECTS_PATH,
            IGNORED_SUBJECTS_PATH=_IGNORED_SUBJECTS_PATH    ):

    global _INPUT_PATH 
    global _TEMP_PATH 
    global _tags
    global _USE_SIDECAR_FILE
    global _TASK
    global _WRITE_MODE
    global _KEYWORDS_START_SYMBOL
    global _TREE_OFFSET
    global _ALLOWED_SUBJECTS_PATH
    global _IGNORED_SUBJECTS_PATH

    INPUT_PATH = INPUT_PATH.replace("//", "/")
    TEMP_PATH = TEMP_PATH + str("/")
    TEMP_PATH = TEMP_PATH.replace("//", "/")
    ALLOWED_SUBJECTS_PATH = ALLOWED_SUBJECTS_PATH.replace("//", "/")
    IGNORED_SUBJECTS_PATH = IGNORED_SUBJECTS_PATH.replace("//", "/")
    USE_SIDECAR_FILE=bool(int(USE_SIDECAR_FILE))
    if isinstance(WRITE_MODE, str):
        WRITE_MODE = WRITE_MODE.lower()
        if(WRITE_MODE == "overwrite"):
            WRITE_MODE = WriteMode.overwrite
        elif(WRITE_MODE == "add"):
            WRITE_MODE = WriteMode.add
        elif(WRITE_MODE == "remove"):
            WRITE_MODE = WriteMode.remove
    if KEYWORDS_START_SYMBOL is None:
        KEYWORDS_START_SYMBOL = ""
    TREE_OFFSET = int(TREE_OFFSET)
    TREE_OFFSET = max(TREE_OFFSET, 0)
    if not isinstance(tags, list):
        tags = split_tags(str(tags))
    else:
        tags = clean_tags(tags)
    if(len(tags) > 0):
        TASK = Task.manual
        
    #scan media file paths
    MEDIA_PATH = ""
    num_files = 0
    num_images = 0
    num_videos = 0
    files = []
    if(os.path.isdir(INPUT_PATH)):
        MEDIA_PATH = INPUT_PATH + str("/")
        MEDIA_PATH = MEDIA_PATH.replace("//", "/")
        files = os.listdir(MEDIA_PATH)
        num_files = len(files)
        print("Input directory has "+str(num_files)+" files")
    else:
        MEDIA_PATH = os.path.dirname(INPUT_PATH) + str("/")
        MEDIA_PATH = MEDIA_PATH.replace("//", "/")
        files = [os.path.basename(INPUT_PATH)]
    media_files = []
    for file in files:
        if (file.endswith(".png") or file.endswith(".jpg")):
            num_images = num_images+1
            media_files.append(file)
        if(file.endswith(".mp4")):
            num_videos = num_videos+1
            media_files.append(file)
        if(file.endswith(".xmp")):
            media_files.append(file)
            
    if(os.path.isdir(INPUT_PATH)):
        print("Input directory has "+str(num_images+num_videos)+" media files for processing")
    #update global variables
    _INPUT_PATH = INPUT_PATH 
    _TEMP_PATH = TEMP_PATH
    _tags = tags
    _USE_SIDECAR_FILE = USE_SIDECAR_FILE
    _TASK = TASK
    _WRITE_MODE = WRITE_MODE
    _KEYWORDS_START_SYMBOL = KEYWORDS_START_SYMBOL
    _TREE_OFFSET = TREE_OFFSET
    _ALLOWED_SUBJECTS_PATH = ALLOWED_SUBJECTS_PATH
    _IGNORED_SUBJECTS_PATH = IGNORED_SUBJECTS_PATH
    return MEDIA_PATH, media_files, num_images, num_videos
    
def preview( INPUT_PATH=_INPUT_PATH ):
    MEDIA_PATH, files, num_images, num_videos  = init( INPUT_PATH=INPUT_PATH )        
    for i in range(len(files)):
        files[i] = MEDIA_PATH+files[i]
    results = []
    for file in files:
        #read metadata
        command = ["exiftool", file]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            text=True
        )
        res, err = process.communicate()  
        results.append(res)
    return results, files

def main(   INPUT_PATH=_INPUT_PATH, 
            TEMP_PATH=_TEMP_PATH, 
            tags=_tags,
            USE_SIDECAR_FILE=_USE_SIDECAR_FILE,
            TASK=_TASK,
            WRITE_MODE = _WRITE_MODE,
            KEYWORDS_START_SYMBOL=_KEYWORDS_START_SYMBOL,
            TREE_OFFSET=_TREE_OFFSET,
            ALLOWED_SUBJECTS_PATH=_ALLOWED_SUBJECTS_PATH,
            IGNORED_SUBJECTS_PATH=_IGNORED_SUBJECTS_PATH  ):
    
    parser = argparse.ArgumentParser(description="Metadata editor. Program can read and add image/video subject tags.")
    parser.add_argument("--input", help=arg_descriptions["INPUT_PATH"])
    parser.add_argument("--temp", help=arg_descriptions["TEMP_PATH"])
    parser.add_argument("--tags", help=arg_descriptions["tags"])
    parser.add_argument("--sidecar", help=arg_descriptions["USE_SIDECAR_FILE"], action='store_const', const=True)
    parser.add_argument("--mode", help=arg_descriptions["WRITE_MODE"])
    parser.add_argument("--start", help=arg_descriptions["KEYWORDS_START_SYMBOL"])
    parser.add_argument("--folder_offset", help=arg_descriptions["TREE_OFFSET"])
    parser.add_argument("--whitelist", help=arg_descriptions["ALLOWED_SUBJECTS_PATH"])
    parser.add_argument("--blacklist", help=arg_descriptions["IGNORED_SUBJECTS_PATH"])

    args = parser.parse_args()

    if args.input is not None:
        INPUT_PATH = args.input
    if args.temp is not None:
        TEMP_PATH = args.temp
    if args.tags is not None:
        tags = args.tags
    if args.sidecar is not None:
        USE_SIDECAR_FILE = args.sidecar
    if args.mode is not None:
        WRITE_MODE = args.mode
    if args.start is not None:
        KEYWORDS_START_SYMBOL = args.start
    if args.folder_offset is not None:
        TREE_OFFSET = args.folder_offset
    if args.whitelist is not None:
        ALLOWED_SUBJECTS_PATH = args.whitelist
    if args.blacklist is not None:
        IGNORED_SUBJECTS_PATH = args.blacklist
        
    start = datetime.now()    
    MEDIA_PATH, files, num_images, num_videos  = init(  INPUT_PATH=INPUT_PATH, 
                                                        TEMP_PATH=TEMP_PATH, 
                                                        tags=tags,
                                                        USE_SIDECAR_FILE=USE_SIDECAR_FILE,
                                                        TASK=TASK,
                                                        WRITE_MODE=WRITE_MODE,
                                                        KEYWORDS_START_SYMBOL=KEYWORDS_START_SYMBOL,
                                                        TREE_OFFSET=TREE_OFFSET,
                                                        ALLOWED_SUBJECTS_PATH=ALLOWED_SUBJECTS_PATH,
                                                        IGNORED_SUBJECTS_PATH=IGNORED_SUBJECTS_PATH  )        
    
    for i in range(len(files)):
        files[i] = MEDIA_PATH+files[i]

    allowed_subjects = []
    ignored_subjects = []
    with open(_ALLOWED_SUBJECTS_PATH, 'r') as buffer:
        allowed_subjects = buffer.read().splitlines()
        allowed_subjects = clean_tags(allowed_subjects, MatchCase.lower)
    with open(_IGNORED_SUBJECTS_PATH, 'r') as buffer:
        ignored_subjects = buffer.read().splitlines()
        ignored_subjects = clean_tags(ignored_subjects, MatchCase.lower)

    for file in files:
        #get the keywords
        keywords = []
        if(_TASK == Task.name2keywords):
            keywords = file2keywords(file, _KEYWORDS_START_SYMBOL, _TREE_OFFSET)
        else:
            keywords = _tags.copy()
            
        if not keywords is None:
            keywords = filterKeywords(  keywords=keywords, 
                                        matchCase=MatchCase.lower, 
                                        allowed_subjects=allowed_subjects, 
                                        ignored_subjects=ignored_subjects  )
        if( (keywords is None) or (len(keywords) == 0) or ((len(keywords) == 1) and (len(keywords[0]) == 0)) ):
            print("WARNING:No keywords detected, skipping file="+file)
            continue
        
        #apply metadata
        params = ["exiftool"]
        writeModeTxt = None
        if(_WRITE_MODE == WriteMode.overwrite):
            writeModeTxt = "="
        elif(_WRITE_MODE == WriteMode.add):
            writeModeTxt = "+="
        elif(_WRITE_MODE == WriteMode.remove):
            writeModeTxt = "-="
        if(not _USE_SIDECAR_FILE):
            if(_WRITE_MODE == WriteMode.overwrite):
                for word in keywords:
                    params.append(str("-Subject" + writeModeTxt + word))
                # params.append("-overwrite_original")
            elif(_WRITE_MODE == WriteMode.add):
                for word in keywords:
                    params.append(str("-Subject" + "-=" + word))
                    params.append(str("-Subject" + writeModeTxt + word))
            elif(_WRITE_MODE == WriteMode.remove):
                for word in keywords:
                    params.append(str("-Subject" + writeModeTxt + word))
            params.append(file)
            process = subprocess.Popen(
                params,
                stdout=subprocess.PIPE,
                text=True
            )
            res, err = process.communicate()
            if(err):
                print("PROCESSING FILE="+file+" RESULTED IN ERROR=", err)
        else:
            #check if sidecar file already exists
            sidecarFile = file
            if(not file.endswith(".xmp")):
                sidecarFile = file + ".xmp"
                if(sidecarFile in files):
                    #skip the loop to read/modify only the sidecar
                    print("...skipping original file because sidecar already exists")
                    continue
                elif(os.path.isfile(sidecarFile)):
                    # read/modify only the sidecar
                    file = sidecarFile    
            # copy current metadata
            params.append("-tagsfromfile")
            params.append("@")
            params.append(file)
            params.append("-srcfile")
            tempFile = TEMP_PATH + os.path.basename(file) 
            if(not tempFile.endswith(".xmp")):
                tempFile = tempFile + ".xmp"
            params.append(tempFile)
            process = subprocess.Popen(
                params,
                stdout=subprocess.PIPE,
                text=True
            )
            res, err = process.communicate()
            # apply changes to metadata
            params = [params[0]]
            if(_WRITE_MODE == WriteMode.overwrite):
                for word in keywords:
                    params.append(str("-Subject" + writeModeTxt + word))
            elif(_WRITE_MODE == WriteMode.add):
                for word in keywords:
                    params.append(str("-Subject" + "-=" + word))
                    params.append(str("-Subject" + writeModeTxt + word))
            elif(_WRITE_MODE == WriteMode.remove):
                for word in keywords:
                    params.append(str("-Subject" + writeModeTxt + word))
            params.append("-overwrite_original")
            params.append(tempFile)
            params.append("-srcfile") #TODO: test if needed
            sidecarFile = file #changeExtension(file,".xmp")
            if(not sidecarFile.endswith(".xmp")):
                sidecarFile = sidecarFile + ".xmp"
            process = subprocess.Popen(
                params,
                stdout=subprocess.PIPE,
                text=True
            )
            res, err = process.communicate()
            #write final file
            shutil.copyfile(tempFile, sidecarFile)
            #remove temp file
            if os.path.exists(tempFile):
                os.remove(tempFile)
                
    collected = gc.collect()
    stop = datetime.now()
    print("Processed "+str(num_images)+" images")
    print("Processed "+str(num_videos)+" videos")
    print("Elapsed time = "+str(stop-start)+" [h][m][s]")


if __name__ == "__main__":
    main()
