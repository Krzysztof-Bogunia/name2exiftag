import FreeSimpleGUI as sg
import gc
import name2exiftag as tagger

_INPUT_PATH = tagger._INPUT_PATH
_TEMP_PATH = tagger._TEMP_PATH
_tags = tagger._tags
_USE_SIDECAR_FILE = True #tagger._USE_SIDECAR_FILE
_TASK = tagger._TASK
_WRITE_MODE = tagger._WRITE_MODE.name
_KEYWORDS_START_SYMBOL = tagger._KEYWORDS_START_SYMBOL
_TREE_OFFSET = tagger._TREE_OFFSET
_ALLOWED_SUBJECTS_PATH = tagger._ALLOWED_SUBJECTS_PATH
_IGNORED_SUBJECTS_PATH = tagger._IGNORED_SUBJECTS_PATH
ID_FILE = int(0)
                    
def removeEmptyFromDict(dict1):
    dict2 = {k: v for k, v in dict1.items() if v is not None}
    return dict2

def checkTextValue(val):
    if( (val is not None) and (len(val)>0) ):
        return True
    else:
        return False
    
def update_preview(window, metadata_txts, files):
    global ID_FILE
    ID_FILE = max(ID_FILE, 0)
    ID_FILE = min(ID_FILE, len(files)-1)
    window['-ID_FILE-'].update(str(ID_FILE))
    if(ID_FILE >= 0):
        window['-METADATA-'].update(str(metadata_txts[ID_FILE]))
    else:
        window['-METADATA-'].update("")
        
def main():
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
    global ID_FILE

    writemodes_txt = []
    for member in tagger.WriteMode:
        writemodes_txt.append(member.name)
    metadata_txts = []
    files = []
    
    # TOP BAR
    topbutton_row = [    sg.Push(), 
                sg.Button('Run', font='Helvetica 18', button_color=('green','limegreen'), key="-RUN-"), 
                sg.Push()   ]
    warning_row = [    sg.Push(), 
                        sg.Text('* BACKUP IMPORTANT DATA BEFORE USING THE PROGRAM *', font='Helvetica 18'), 
                        sg.Push()   ]
    
    # SETUP TAB
    button_media_file = sg.Button('Media file', font='Helvetica 14', tooltip=tagger.arg_descriptions["INPUT_PATH"], key="-MEDIA-FILE-")
    button_media_folder = sg.Button('Media folder', font='Helvetica 14', tooltip=tagger.arg_descriptions["INPUT_PATH"], key="-MEDIA-FOLDER-")
    button_temp_folder = sg.Button('Temp folder', font='Helvetica 14', tooltip=tagger.arg_descriptions["TEMP_PATH"], key="-TEMP-FOLDER-")
    button_whitelist_file = sg.Button('Whitelist file', font='Helvetica 14', tooltip=tagger.arg_descriptions["ALLOWED_SUBJECTS_PATH"], key="-ALLOWED_SUBJECTS_PATH-")
    button_blacklist_file = sg.Button('Blacklist file', font='Helvetica 14', tooltip=tagger.arg_descriptions["IGNORED_SUBJECTS_PATH"], key="-IGNORED_SUBJECTS_PATH-")
    
    input_column = [  [sg.Text('INPUT PATH SELECTION', justification='center', size=(30, 1), font='Helvetica 18')],                        
                        [button_media_file],
                        [button_media_folder],
                        [sg.Input(default_text=str(_INPUT_PATH), tooltip=tagger.arg_descriptions["INPUT_PATH"], enable_events=True, key="-_INPUT_PATH-")],
                        [button_whitelist_file],
                        [sg.Input(default_text=str(_ALLOWED_SUBJECTS_PATH), tooltip=tagger.arg_descriptions["ALLOWED_SUBJECTS_PATH"], enable_events=True, key="-_ALLOWED_SUBJECTS_PATH-")],
                        [button_blacklist_file],
                        [sg.Input(default_text=str(_IGNORED_SUBJECTS_PATH), tooltip=tagger.arg_descriptions["IGNORED_SUBJECTS_PATH"], enable_events=True, key="-_IGNORED_SUBJECTS_PATH-")]  ]
    output_column = [  [sg.Text('OUTPUT PATH SELECTION', justification='center', size=(30, 1), font='Helvetica 18')],                        
                        [button_temp_folder],
                        [sg.Input(default_text=str(_TEMP_PATH), tooltip=tagger.arg_descriptions["TEMP_PATH"], key="-_TEMP_PATH-")] ]
    processing_column = [  [sg.Text('PROCESSING SETTINGS', justification='center', size=(30, 1), font='Helvetica 18')],                        
                            [sg.Text('tags'), 
                            sg.Input(default_text=str(','.join(_tags)), enable_events=True, tooltip=tagger.arg_descriptions["tags"], key="-_tags-", size=[50,1])],
                            [sg.Checkbox('USE_SIDECAR_FILE', default=int(_USE_SIDECAR_FILE), enable_events=True, tooltip=tagger.arg_descriptions["USE_SIDECAR_FILE"], key="-USE_SIDECAR_FILE-"), 
                            sg.Text(str(bool(int(_USE_SIDECAR_FILE))), enable_events=True, visible=False, key="-_USE_SIDECAR_FILE-")], 
                            [sg.Text('WRITE_MODE'),
                             sg.Combo(writemodes_txt, default_value=str(_WRITE_MODE), enable_events=True, tooltip=tagger.arg_descriptions["WRITE_MODE"], key="-WRITE_MODE-", size=(20, 1))],
                            [sg.Text('TREE_OFFSET'), 
                            sg.Slider((0,3), resolution=1, default_value=int(_TREE_OFFSET), enable_events=True, orientation='h', tooltip=tagger.arg_descriptions["TREE_OFFSET"], key="-TREE_OFFSET_SLIDER-"),
                            sg.Input(default_text=str(int(_TREE_OFFSET)), enable_events=True, tooltip=tagger.arg_descriptions["TREE_OFFSET"], key="-_TREE_OFFSET-", size=[5,1])],
                            [sg.Text('KEYWORDS_START_SYMBOL'), 
                            sg.Input(default_text=str(_KEYWORDS_START_SYMBOL), enable_events=True, tooltip=tagger.arg_descriptions["KEYWORDS_START_SYMBOL"], key="-_KEYWORDS_START_SYMBOL-")]  ]
    setupTab = [    [sg.Frame(layout=input_column, element_justification='center', vertical_alignment="top", title=''), 
                    sg.Frame(layout=output_column, element_justification='center', vertical_alignment="top", title=''),
                    sg.Frame(layout=processing_column, element_justification='center', vertical_alignment="top", title='')] ]
    
    # PREVIEW TAB
    button_prev_file = sg.Button('<', font='Helvetica 14', key="-BTN_PREV_FILE-")
    button_next_file = sg.Button('>', font='Helvetica 14', key="-BTN_NEXT_FILE-")
    selection_row = [   sg.Text('SELECTION NUMBER'), 
                        sg.Input(default_text=str(ID_FILE), size=(5, 1), tooltip="selected file's number", enable_events=True, key="-ID_FILE-"), 
                        button_prev_file, 
                        button_next_file, 
                        sg.Push() ]
    metadata_column = sg.Column(
        [ [sg.Multiline('', key='-METADATA-', expand_x=True, expand_y=True, no_scrollbar=False, disabled=True, autoscroll=True, autoscroll_only_at_bottom=True)] ],
        expand_x=True, expand_y=True) 
    file_row = [  sg.Frame(title='file', layout=[[metadata_column]], expand_x=True, expand_y=True)   ]
    previewTab = [  [sg.Push(), sg.Button('Preview', font='Helvetica 16', button_color=('MediumSpringGreen','MediumSeaGreen'), key="-PREVIEW-"), sg.Push()], 
                    selection_row, 
                    file_row ]
    
    layout = [  topbutton_row,
                warning_row,
                [sg.TabGroup([[sg.Tab('setup', setupTab), sg.Tab('previews', previewTab)]], expand_x=True, expand_y=True)],
                [sg.Output(size=(100, 5))]    ]
    window = sg.Window('Image-Video-Tagger', layout, no_titlebar=False, location=(0, 0), resizable=True)
    
    #UI loop
    while True:
        event, values = window.read(timeout=1000)
        if event in ('Exit', sg.WINDOW_CLOSED):
            break
        
        # load variables from UI
        if(checkTextValue( window['-_INPUT_PATH-'].get())):
            _INPUT_PATH = window['-_INPUT_PATH-'].get()
        else:
            _INPUT_PATH = None
        if(checkTextValue( window['-_TEMP_PATH-'].get())):
            _TEMP_PATH = window['-_TEMP_PATH-'].get()
        else:
            _TEMP_PATH = None
        if(checkTextValue( window['-_tags-'].get())):
            _tags = window['-_tags-'].get()
            _tags = _tags.split(',')
        else:
            _tags = None
        _USE_SIDECAR_FILE = values["-USE_SIDECAR_FILE-"]
        if(checkTextValue( window['-WRITE_MODE-'].get())):
            value = window['-WRITE_MODE-'].get().lower()
            for member in tagger.WriteMode:
                if(value == member.name.lower()):
                    _WRITE_MODE = value
                    break
        else:
            _WRITE_MODE = None
        if(checkTextValue( window['-_TREE_OFFSET-'].get())):
            _TREE_OFFSET = window['-_TREE_OFFSET-'].get()
        else:
            _TREE_OFFSET = None
        if(checkTextValue( window['-_KEYWORDS_START_SYMBOL-'].get())):
            _KEYWORDS_START_SYMBOL = window['-_KEYWORDS_START_SYMBOL-'].get()
        else:
            _KEYWORDS_START_SYMBOL = None
        if(checkTextValue( window['-ID_FILE-'].get())):
            ID_FILE = int(window['-ID_FILE-'].get())
            
        # load variables from UI events
        if event in ("-MEDIA-FILE-"):
            _INPUT_PATH = sg.popup_get_file('Select input file')
            if not checkTextValue(_INPUT_PATH):
                _INPUT_PATH = None
            else:
                window['-_INPUT_PATH-'].update(_INPUT_PATH)
            
        if event in ("-MEDIA-FOLDER-"):
            _INPUT_PATH = sg.popup_get_folder('Select input folder')
            if not checkTextValue(_INPUT_PATH):
                _INPUT_PATH = None
            else:
                window['-_INPUT_PATH-'].update(_INPUT_PATH)

        if event in ("-TEMP-FOLDER-"):
            _TEMP_PATH = sg.popup_get_folder('Select temp folder')
            if not checkTextValue(_TEMP_PATH):
                _TEMP_PATH = None
            else:
                window['-_TEMP_PATH-'].update(_TEMP_PATH)
        
        if event in ("-ALLOWED_SUBJECTS_PATH-"):
            _ALLOWED_SUBJECTS_PATH = sg.popup_get_file('Select whitelist file')
            if not checkTextValue(_ALLOWED_SUBJECTS_PATH):
                _ALLOWED_SUBJECTS_PATH = None
            else:
                window['-_ALLOWED_SUBJECTS_PATH-'].update(_ALLOWED_SUBJECTS_PATH)
        
        if event in ("-IGNORED_SUBJECTS_PATH-"):
            _IGNORED_SUBJECTS_PATH = sg.popup_get_file('Select blacklist file')
            if not checkTextValue(_IGNORED_SUBJECTS_PATH):
                _IGNORED_SUBJECTS_PATH = None
            else:
                window['-_IGNORED_SUBJECTS_PATH-'].update(_IGNORED_SUBJECTS_PATH)
        
        if event in ("-USE_SIDECAR_FILE-"):
            _USE_SIDECAR_FILE = values["-USE_SIDECAR_FILE-"]
            if _USE_SIDECAR_FILE is None:
                _USE_SIDECAR_FILE = False
            else:
                _USE_SIDECAR_FILE = bool(int(_USE_SIDECAR_FILE))
            window['-_USE_SIDECAR_FILE-'].update(str(int(_USE_SIDECAR_FILE)))
        
        if event in ("-WRITE_MODE-"):
            value = values["-WRITE_MODE-"].lower()
            for member in tagger.WriteMode:
                if(value == member.name.lower()):
                    _WRITE_MODE = value
                    break
            window['-WRITE_MODE-'].update(str(_WRITE_MODE))
        
        if event in ("-_TREE_OFFSET-"):
            _TREE_OFFSET = window['-_TREE_OFFSET-'].get()
            if not checkTextValue(_TREE_OFFSET):
                _TREE_OFFSET = None
            else:
                _TREE_OFFSET = int(_TREE_OFFSET)
                window['-TREE_OFFSET_SLIDER-'].update(_TREE_OFFSET)
        if event in ("-TREE_OFFSET_SLIDER-"):
            _TREE_OFFSET = values["-TREE_OFFSET_SLIDER-"]
            if _TREE_OFFSET is None:
                _TREE_OFFSET = None
            else:
                _TREE_OFFSET = int(_TREE_OFFSET)
                window['-_TREE_OFFSET-'].update(str(_TREE_OFFSET))
        
        if event in ("-ID_FILE-"):
            temp = window['-ID_FILE-'].get()
            if checkTextValue(temp):
                ID_FILE = int(temp)
                window['-ID_FILE-'].update(str(ID_FILE))
                update_preview(window, metadata_txts, files)
        if event in ("-BTN_NEXT_FILE-"):
            ID_FILE = ID_FILE+1
            update_preview(window, metadata_txts, files)
        if event in ("-BTN_PREV_FILE-"):
            ID_FILE = ID_FILE-1
            update_preview(window, metadata_txts, files)

            
        # handle tasks
        if event in ("-RUN-"):
            args = {  "INPUT_PATH": _INPUT_PATH, 
                        "TEMP_PATH": _TEMP_PATH, 
                        "tags": _tags, 
                        "USE_SIDECAR_FILE": _USE_SIDECAR_FILE, 
                        "WRITE_MODE": _WRITE_MODE, 
                        "KEYWORDS_START_SYMBOL": _KEYWORDS_START_SYMBOL,
                        "TREE_OFFSET": _TREE_OFFSET,
                        "ALLOWED_SUBJECTS_PATH": _ALLOWED_SUBJECTS_PATH, 
                        "IGNORED_SUBJECTS_PATH": _IGNORED_SUBJECTS_PATH }
            args = removeEmptyFromDict(args)
            print("\nRunning tagger with input arguments:\n"+str(args))
            tagger.main(**args)
            collected = gc.collect()
            
        if event in ("-PREVIEW-"):
            args = { "INPUT_PATH": _INPUT_PATH }
            args = removeEmptyFromDict(args)
            print("\nReading metadata from path: "+str(_INPUT_PATH))
            metadata_txts, files = tagger.preview(**args)
            print("Preview returned "+str(len(files))+" files")
            update_preview(window, metadata_txts, files)
            collected = gc.collect()
            
    window.close()


    
if __name__ == "__main__":
    main()
