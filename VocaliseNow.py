from TTS.api import TTS
from tkinter import *  
from tkinter import filedialog
from os.path import exists
import pyaudio
import wave
import customtkinter
import os
import json
import FairseqLangs

import asyncio
import concurrent.futures
from async_tkinter_loop import async_handler, async_mainloop


########## Json handling ##########
def CreateSettings():
        # Data to be written
        dictionary = {
            "previewsGenerated": "False",
            "recSaveDirectory": str(os.getcwd()),
            "recSelectDirectory": str(os.getcwd()),
            "saveDirectory": str(os.getcwd()),
            "modelDirectory": str(os.getcwd()),
            "genMeta": "True",
            "lastLang": ""
        }
        
        # Serializing json
        json_object = json.dumps(dictionary, indent=4)
        
        # Writing to settings.json
        with open("settings.json", "w") as outfile:
            outfile.write(json_object)

def CreateMeta(directory, name, text, model):
    # Data to be written
    l = []

    dictionary = {
        "bubble": l,
        "model": model,
        "count": 0
    }

    i = 0
    para = ""
    for char in text:
        if char == "$":
            dictionary2 = {
                "speech": para,
                "audio": name + str(i) + ".wav"
            }
            dictionary["bubble"].append(dictionary2)
            dictionary["count"] += 1
            para = ""
            i += 1
        else:
            para += char
    
    # Serializing json
    json_object = json.dumps(dictionary, indent=4)
    # Writing to sample.json
    with open(directory+"/meta_"+name+".json", "w") as outfile:
        outfile.write(json_object)

def GetSettingBool(switch: customtkinter.CTkSwitch = None, id: str = "genMeta"):
    global genMetaBool
    value = GetSetting(str(id))

    if switch != None:
        if value == "True":
            switch.select()
        elif value == "False":
            switch.deselect()
    
    if id == "genMeta":
        genMetaBool = bool(value)

def UpdateSetting(id, value):
    with open("settings.json", "r") as settingsJson:
        settings = json.load(settingsJson)

    settings[str(id)] = str(value)

    with open("settings.json", "w") as outfile:
        json.dump(settings, outfile, indent=4)

def UpdateLang(e):
    UpdateSetting("lastLang", convLang.get())

def GetSetting(id: str = "lastLang"):
    with open("settings.json", "r") as settingsJson:
        settings = json.load(settingsJson)

    value = settings[str(id)]

    return value

def GetDirectory(entry, id, file: bool = False):
    #Get a directory path by user
    if file:
        print("file")
        filepath = filedialog.askopenfilename(parent=entry.master, title="Dialog box", filetypes=((".wav files", "*.wav"), ("All files", "*.*")))
    else:
        filepath = filedialog.askdirectory(parent=entry.master, title="Dialog box")
    # Load data from the json file
    with open("settings.json", "r") as settingsJson:
        settings = json.load(settingsJson)

    # Change Directory in settings
    if filepath != "":
        settings[str(id)] = str(filepath)
    else:
        settings[str(id)] = str(os.getcwd())

    # Save changes
    with open("settings.json", "w") as outfile:
        json.dump(settings, outfile, indent=4)

    LoadDirectory(entry, id)

def LoadDirectory(entry, id):
    entry.delete(0,END)
    entry.insert(0,GetSetting(id))

########## Json handling ##########

########## TTS ##########

def PickModel(mod, path):
    #Define voice model
    global tts
    tts = TTS(mod, output_path=path)
    
#Generate TTS voice
async def GenTTS(dir, txt, mod, lang, speak, name, text, convTF, cLang):
    loop = asyncio.get_event_loop()
    path = GetSetting("modelDirectory")
    if not convTF:
        for model in TTS.list_models():
            modelType, lang, dataset, modelName = model.split("/")
            if lang == lang and dataset == speak and modelName == mod:
                fullModelName = modelType+"/"+lang+"/"+dataset+"/"+modelName
    else:
        fullModelName = "tts_models/"+FairseqLangs.langs[cLang]+"/fairseq/vits"

    global TTSPool
    await loop.run_in_executor(TTSPool, func= lambda: PickModel(fullModelName, path))
    TTSPool.shutdown()

    if genMetaBool:
        CreateMeta(dir, name, txt, fullModelName)

def CreateAudio(lang, speak, text, directory, name, id, convTF):
    if not convTF:
        if tts.is_multi_speaker:
            if tts.is_multi_lingual:
                tts.tts_to_file(text=text, speaker=speak, language=lang, file_path=directory + "/"+name + str(id) +".wav")
            else:
                tts.tts_to_file(text=text, speaker=speak, file_path=directory + "/"+name + str(id) +".wav")
        elif tts.is_multi_lingual:
            tts.tts_to_file(text=text, language=lang, file_path=directory + "/"+name + str(id) +".wav")
        else:
            tts.tts_to_file(text=text, file_path=directory + "/"+name + str(id) +".wav")
    else:
        fileType = os.path.splitext(GetSetting("recSelectDirectory"))[1]
        if fileType == ".wav":
            tts.tts_with_vc_to_file(text=text, speaker_wav=GetSetting("recSelectDirectory"), file_path=directory + "/"+name + str(id) +".wav", output_path=GetSetting("modelDirectory"))
        else:
            print("please select .wav file")
    
def ParseText(text):
    out = ""
    for char in text:
        if char != "\n":
            out += char
    return out

async def CreateAudioAsync(lang, speak, para, directory, name, i, conv):
    loop = asyncio.get_event_loop()
    global TTSPool
    await loop.run_in_executor(TTSPool, func= lambda: CreateAudio(lang, speak, para, directory, name, i, conv))
    TTSPool.shutdown()

async def Finish():
    global conv

    text = textEntry.get('1.0', END)
    name = nameEntry.get()
    cLang = convLang.get()
    speak = dropSpeakers.get()
    lang = dropLangs.get()
    mod = dropModels.get()
    newText = ParseText(text) + "$"
    directory = GetSetting("saveDirectory") + "/" + name
    if not os.path.exists(directory):
        os.mkdir(directory)
    await GenTTS(directory, newText, mod, lang, speak, name, text, conv, cLang)

    i = 0
    para = ""
    for char in newText:
        if char == "$":
            await CreateAudioAsync(lang, speak, para, directory, name, i, conv)
            para = ""
            i += 1
        else:
            para += char
    print("done")
    
########## TTS ##########

########## Dropdown handling ##########

def UpdateDrops(dropIndx: int = None):
    global allModels
    global allLangName
    global allVoiceName
    global allModelName
    global defaultValues
    global previewsGenerated
    global conv

    optionChanged = dropsList[dropIndx]
    temp = []
    for drop in dropsList:
        if drop != optionChanged:
            temp.append(drop)
    #For each non selected options
    for notSelected in temp:
        newValues = []
        #Check all models
        for model in allModels:
            #If all selected options math the model
            if model[dropsList.index(optionChanged)] == optionChanged.get():
                #Add the value of the non selected option in that model to array
                val = model[dropsList.index(notSelected)]
                if val not in newValues:
                    newValues.append(val)
        #Set array of options to the available options
        notSelected.configure(values = newValues)

        if notSelected.get() not in notSelected.cget("values"):
            notSelected.set(dropsDefaults[dropsList.index(notSelected)])

def ResetDrops():
    for drop in dropsList:
        drop.configure(values = defaultValues[dropsList.index(drop)])
        drop.set(dropsDefaults[dropsList.index(drop)])

def GetModelData():
    global allModels
    global allLangName
    global allVoiceName
    global allModelName
    global defaultValues

    allModels = []
    allLangName = []
    allVoiceName = []
    allModelName = []
    for model in TTS.list_models():
        modelType, lang, dataset, modelName = model.split("/")
        if lang != "multilingual" and modelType == "tts_models": #dataset != "multi-dataset" and dataset != "vctk":
            modelDict = [lang, dataset, modelName]
            allModels.append(modelDict)

    for model in allModels:
        if model[0] not in allLangName:
            allLangName.append(model[0])
        if model[1] not in allVoiceName:
            allVoiceName.append(model[1])
        if model[2] not in allModelName:
            allModelName.append(model[2])

    defaultValues = [allLangName, allVoiceName, allModelName]

########## Dropdown handling ##########

########## Voice Previews ##########

def CreatePreviews():
    global tts
    global previewsGenerated
    previewsGenerated = False
    for model in TTS.list_models():
        modelType, lang, dataset, modelName = model.split("/")
        fullModelName = modelType+"/"+lang+"/"+dataset+"/"+modelName
        if modelName != "your_tts" and lang == "en" and dataset != "vctk" and dataset != "multi-dataset":
            tts = TTS(fullModelName, output_path=str(GetSetting("modelDirectory")))
            dir1 = GetSetting("saveDirectory") + "/" + modelType
            dir2 = dir1 + "/" + lang
            dir3 = dir2 + "/" + dataset
            dir4 = dir3 + "/" + modelName
            if not os.path.exists(dir1):
                os.mkdir(dir1)
            if not os.path.exists(dir2):
                os.mkdir(dir2)
            if not os.path.exists(dir3):
                os.mkdir(dir3)
            if not os.path.exists(dir4):
                os.mkdir(dir4)
            directory = GetSetting("saveDirectory") + "/" + modelType + "/" + lang + "/" + dataset + "/" + modelName
            saveName = lang + "-" + dataset + "-" + modelName
            if tts.is_multi_speaker:
                if tts.is_multi_lingual:
                    tts.tts_to_file(text="This is a preview of this voice.", speaker=dataset, language=lang, file_path=directory + "/"+saveName +".wav")
                else:
                    tts.tts_to_file(text="This is a preview of this voice.", speaker=dropSpeakers.get(), file_path=directory + "/"+saveName +".wav")
            elif tts.is_multi_lingual:
                tts.tts_to_file(text="This is a preview of this voice.", language=dropLangs.get(), file_path=directory + "/"+saveName +".wav")
            else:
                tts.tts_to_file(text="This is a preview of this voice.", file_path=directory + "/"+saveName +".wav")
    previewsGenerated = True
    UpdateSetting("previewsGenerated", "True")

async def CreatePreviewsAsync():
    loop = asyncio.get_event_loop()
    global previewPool
    await loop.run_in_executor(previewPool, CreatePreviews)
    previewPool.shutdown()

async def GenPreviews():
    await CreatePreviewsAsync()
    print("done")

def PlayAudio(wf):
    chunk = 1024
    waveFile = wf
    port = pyaudio.PyAudio()
    stream = port.open(format = port.get_format_from_width(waveFile.getsampwidth()),
                channels = waveFile.getnchannels(),
                rate = waveFile.getframerate(),
                output = True)
    data = waveFile.readframes(chunk)
    while len(data := waveFile.readframes(chunk)):
        stream.write(data)
    stream.close()
    port.terminate()

async def PlayAudioAsync():
    sn = dropLangs.get() + "-" + dropSpeakers.get() + "-" + dropModels.get() + ".wav"
    sp = "./tts_models/" + dropLangs.get() + "/" + dropSpeakers.get() + "/" + dropModels.get() + "/" + sn
    wf = wave.open(sp, 'rb')
    frames = wf.getnframes()
    rate = wf.getframerate()

    length = round(frames/float(rate), 3)
    previewBar.configure(determinate_speed= 50/((length*1000)/20)+0.2)
    previewBar.start()

    loop = asyncio.get_event_loop()
    global audioPool
    await loop.run_in_executor(audioPool, func= lambda: PlayAudio(wf))
    audioPool.shutdown()

async def PlayPreview():
    await PlayAudioAsync()
    print("playback complete")
    previewBar.stop()
    previewBar.set(0)

########## Voice Previews ##########

########## Record Audio ##########

def RecordWav(length, name):
    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 2
    fps = 44100  # Record at 44100 samples per second
    seconds = length*60
    filename = GetSetting("recSaveDirectory") + name + ".wav"

    port = pyaudio.PyAudio()  # Create an interface to PortAudio

    print('Recording')

    stream = port.open(format=sample_format,
                    channels=channels,
                    rate=fps,
                    frames_per_buffer=chunk,
                    input=True)

    frames = []  # Initialize array to store frames

    # Store data in chunks for 3 seconds
    for i in range(0, int(fps / chunk * seconds)):
        data = stream.read(chunk)
        frames.append(data)

    # Stop and close the stream 
    stream.stop_stream()
    stream.close()
    # Terminate the PortAudio interface
    port.terminate()

    print('Finished recording')

    # Save the recorded data as a WAV file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(port.get_sample_size(sample_format))
    wf.setframerate(fps)
    wf.writeframes(b''.join(frames))
    wf.close()

async def RecordWavAsync(length, name):
    loop = asyncio.get_event_loop()

    recBar.configure(determinate_speed= 1/(length*60))
    recBar.start()

    global audioPool
    await loop.run_in_executor(audioPool, func= lambda: RecordWav(length, name))
    audioPool.shutdown()

async def RecordAudio():
    length = int(recordLength.get())
    name = convNameEntry.get()
    await RecordWavAsync(length, name)
    recBar.stop()
    recBar.set(0)

########## Record Audio ##########
    
########## Experimental ###########

#tts = TTS("tts_models/en/multi-dataset/tortoise-v2")
#tts.tts_to_file(text="Hello, my name is Manmay , how are you?", speaker= tts.speakers[0],file_path="output.wav")
#tts = TTS(model_name="voice_conversion_models/multilingual/vctk/freevc24", progress_bar=False, output_path=str(GetSetting("modelDirectory")))
##tts.voice_conversion_to_file(source_wav="source.wav", target_wav="target.wav", file_path="output.wav")
#tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", output_path=str(GetSetting("modelDirectory")))
#tts.tts_to_file("this is a test of some voice cloning with the pride and predjudice thing.", speaker_wav="pp.wav", language="en", file_path="output.wav")

########## Experimental ###########

########## Settings Window ###########

def OnSettClose():
    root.attributes("-disabled", "false")
    sett.destroy()

def SettingsPopUp():
    global sett
    global modDirectEntry
    #Creating settings window
    sett = customtkinter.CTkToplevel(root)
    sett.grab_set()
    #sett.iconbitmap("./Lib/icons/Cog.ico")
    #sett.attributes("-topmost", "true")
    #root.attributes("-disabled", "true")

    #Column config
    sett.columnconfigure(0, weight=1)
    sett.columnconfigure(1, weight=5)
    sett.columnconfigure(2, weight=5)
    sett.columnconfigure(3, weight=5)

    #Window config
    sett.geometry("650x200")
    sett.title("Settings")

    #Models directory
    customtkinter.CTkLabel(sett, text="Language model directory:").grid(row=0, column=0)
    modDirectEntry = customtkinter.CTkEntry(sett)
    LoadDirectory(modDirectEntry, "modelDirectory")
    modDirectEntry.grid(row=0, column=1, columnspan=2, sticky=EW, pady=5, padx=5)

    #Browse Button
    modDirectButton = customtkinter.CTkButton(sett, text='Browse...', command = lambda: GetDirectory(modDirectEntry, "modelDirectory"))
    modDirectButton.grid(row=0, column=3, columnspan=1, sticky=W)

    customtkinter.CTkLabel(sett, text="Generate meta data for Unity:").grid(row=1, column=0)
    genMetaSwitch = customtkinter.CTkSwitch(sett, text="", onvalue="True", offvalue="False", command= lambda: UpdateSetting("genMeta", genMetaSwitch.get()))
    GetSettingBool(genMetaSwitch, "genMeta")
    genMetaSwitch.grid(row=1, column=1, sticky=W)

    customtkinter.CTkLabel(sett, text="Download previews of voices:").grid(row=2, column=0)
    previews = customtkinter.CTkButton(sett, text='Gen Previews', command = async_handler(GenPreviews))
    previews.grid(row=2, column=1, sticky=W, pady=5, padx=5)

    #Finishing window
    sett.protocol("WM_DELETE_WINDOW", OnSettClose)

########## Settings Window ###########

def init():
    global dropsList
    global dropsDefaults
    global dropLangsDefault
    global dropSpeakersDefault
    global dropModelsDefault
    global previewsGenerated

    global TTSPool
    global audioPool
    global previewPool

    TTSPool = concurrent.futures.ThreadPoolExecutor()
    audioPool = concurrent.futures.ThreadPoolExecutor()
    previewPool = concurrent.futures.ThreadPoolExecutor()

    dropSpeakersDefault = "Select Voice"
    dropLangsDefault = "Select Language"
    dropModelsDefault = "Select Model"
    dropsDefaults = [dropLangsDefault, dropSpeakersDefault, dropModelsDefault]

    #Making settings file 
    fileExists = exists("settings.json")
    if not fileExists:
        CreateSettings()
    GetSettingBool()
    GetModelData()
    previewsGenerated = GetSetting("previewsGenerated")

    customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"
    #GenPreviews()

def OnRootClose():
    audioPool.shutdown(wait=False, cancel_futures=True)
    previewPool.shutdown(wait=False, cancel_futures=True)
    TTSPool.shutdown(wait=False, cancel_futures=True)
    root.destroy()

def main():
    global dropsList
    global dropLangsDefault
    global dropSpeakersDefault
    global dropModelsDefault

    global root
    global dropLangs
    global dropSpeakers
    global dropModels
    global textEntry
    global nameEntry
    global previewButton
    global finishButton
    global tabFrame
    global convLang
    global previewBar
    global recBar
    global recordLength
    global convNameEntry
    
    init()
    ########## Main Window ###########

    #Make main window
    root = customtkinter.CTk()
    #root.iconbitmap("./Lib/icons/LogoS.ico")
    root.title("CoquiTTS Generator")
    root.geometry("1300x700")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)
    #root.columnconfigure(1, weight=1)

    leftFrame = customtkinter.CTkFrame(root)
    leftFrame.grid(row=0, column=0, rowspan=2 , padx=10, pady=10, sticky=NSEW)
    leftFrame.columnconfigure(0, weight=1)
    leftFrame.rowconfigure(1, weight=1)

    rightFrame = customtkinter.CTkFrame(root)
    rightFrame.grid(row=1, column=1, padx=(0, 10), pady=(0, 10), sticky=NS)
    rightFrame.columnconfigure(0, weight=1)
    rightFrame.rowconfigure(0, weight=1)
    rightFrame.rowconfigure(1, weight=1)

    #Settings and info buttons
    settingsButton = customtkinter.CTkButton(root, text="Settings", command=SettingsPopUp)
    settingsButton.grid(row=0, column=1, sticky=NE, pady=5, padx=5)

    #Make text input field for text wanted
    customtkinter.CTkLabel(leftFrame, text="Text:").grid(row=0, column=0)
    textEntry = customtkinter.CTkTextbox(leftFrame, width=40, height=100, wrap=WORD)
    textEntry.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    voicePreview = customtkinter.CTkFrame(rightFrame)
    voicePreview.columnconfigure(0, weight=1)
    voicePreview.rowconfigure(0, weight=1)
    voicePreview.columnconfigure(1, weight=1)
    voicePreview.rowconfigure(1, weight=1)
    previewLabel = customtkinter.CTkLabel(voicePreview, text="Selected Voice Preview:", pady=5, padx=10)
    previewButton = customtkinter.CTkButton(voicePreview, text='Play', state="disabled", command = async_handler(PlayPreview), width=80)
    previewBar = customtkinter.CTkProgressBar(voicePreview, orientation="horizontal", width=200)
    previewBar.set(0)

    recordSelect = customtkinter.CTkFrame(rightFrame)
    recordSelect.columnconfigure(0, weight=1)
    recordSelect.rowconfigure(0, weight=1)
    recordSelect.columnconfigure(1, weight=1)
    recordSelect.rowconfigure(1, weight=1)
    recordSelectLabel = customtkinter.CTkLabel(recordSelect, text="Selected Recording:", pady=5, padx=10)
    recSelectEntry = customtkinter.CTkEntry(recordSelect, width=200)
    recBrowseButton = customtkinter.CTkButton(recordSelect, text='Browse...', command = lambda: GetDirectory(recSelectEntry, "recSelectDirectory", file=True), width=80)
    LoadDirectory(recSelectEntry, "recSelectDirectory")

    global conv
    conv = False

    def PreviewAdd():
        voicePreview.grid(row=1, column=0, padx=10, pady=10, sticky=EW)
        previewLabel.grid(row=0, column=0, columnspan=2)
        previewButton.grid(row=1, column=0, sticky=W)
        previewBar.grid(row=1, column=1, sticky=EW, pady=5, padx=10)

        recordSelect.grid_remove()
        recordSelectLabel.grid_remove()
        recBrowseButton.grid_remove()
        recSelectEntry.grid_remove()

    PreviewAdd()

    def PreviewRemove():
        voicePreview.grid_remove()
        previewLabel.grid_remove()
        previewButton.grid_remove()

        recordSelect.grid(row=1, column=0, padx=10, pady=10, sticky=EW)
        recordSelectLabel.grid(row=0, column=0, columnspan=3)
        recBrowseButton.grid(row=1, column=0, sticky=W)
        recSelectEntry.grid(row=1, column=1, sticky=EW)

    def FrameSwitch():
        global conv
        if conv == False:
            PreviewRemove()
            conv = True
        else:
            PreviewAdd()
            conv = False

    tabFrame = customtkinter.CTkTabview(rightFrame, command=FrameSwitch)
    tabFrame.grid(row=0, column=0, padx=10, pady=10, sticky=N)
    tabFrame.add("Voices")
    tabFrame.add("Record")

    modelSelection = tabFrame.tab("Voices")
    modelSelection.columnconfigure(0, weight=1)
    modelSelection.rowconfigure(0, weight=1)
    modelSelection.columnconfigure(1, weight=1)
    modelSelection.rowconfigure(1, weight=1)
    modelSelection.rowconfigure(2, weight=1)
    modelSelection.rowconfigure(3, weight=1)

    customtkinter.CTkLabel(modelSelection, text="Lang:", width=5, pady=5, padx=10).grid(row=1, column=0)
    dropLangs = customtkinter.CTkOptionMenu(modelSelection, values = allLangName, command= lambda e: UpdateDrops(0))
    dropLangs.set(dropLangsDefault)
    dropLangs.grid(row=1, column=1, sticky=EW, pady=5, padx=5)

    customtkinter.CTkLabel(modelSelection, text="Voice:", width=5, pady=5, padx=10).grid(row=2, column=0)
    dropSpeakers = customtkinter.CTkOptionMenu(modelSelection, values = allVoiceName, command= lambda e: UpdateDrops(1))
    dropSpeakers.set(dropSpeakersDefault)
    dropSpeakers.grid(row=2, column=1, sticky=EW, pady=5, padx=5)

    #Make dropdown of all voice model options
    customtkinter.CTkLabel(modelSelection, text="Model:", width=5, pady=5, padx=10).grid(row=3, column=0, columnspan=2)
    dropModels = customtkinter.CTkOptionMenu(modelSelection, width=250, values = allModelName, command= lambda e: UpdateDrops(2))
    dropModels.set(dropModelsDefault)
    dropModels.grid(row=4, column=0, columnspan=2, sticky=EW, pady=5, padx=5)

    dropsList = [dropLangs, dropSpeakers, dropModels]

    resetButton = customtkinter.CTkButton(modelSelection, text='Reset', command = lambda: ResetDrops())
    resetButton.grid(row=5, column=0, pady=5, padx=5, columnspan=2)

    voiceConvRecord = tabFrame.tab("Record")
    voiceConvRecord.columnconfigure(0, weight=1)
    voiceConvRecord.columnconfigure(1, weight=1)
    voiceConvRecord.columnconfigure(2, weight=1)
    voiceConvRecord.columnconfigure(3, weight=1)
    voiceConvRecord.rowconfigure(0, weight=1)
    voiceConvRecord.rowconfigure(1, weight=1)
    voiceConvRecord.rowconfigure(2, weight=1)
    voiceConvRecord.rowconfigure(3, weight=1)
    voiceConvRecord.rowconfigure(4, weight=1)
    voiceConvRecord.rowconfigure(5, weight=1)

    customtkinter.CTkLabel(voiceConvRecord, text="Lang:", width=5, pady=5, padx=10).grid(row=0, column=0)
    convLang = customtkinter.CTkOptionMenu(voiceConvRecord, width=200, values = list(FairseqLangs.langs.keys()), command=UpdateLang)
    if GetSetting("lastLang") == "":
        convLang.set("Please Select")
    else:
        convLang.set(GetSetting("lastLang"))
    convLang.grid(row=0, column=1, columnspan=2, sticky=EW, pady=5, padx=5)

    customtkinter.CTkLabel(voiceConvRecord, text="Recording Length:", width=5, pady=5, padx=10).grid(row=1, column=0, columnspan=2, sticky=W)
    recordLength = customtkinter.CTkOptionMenu(voiceConvRecord, width=50, values=["1","2","3","4","5","6","7","8","9","10"])
    recordLength.grid(row=1, column=2, sticky=W)
    customtkinter.CTkLabel(voiceConvRecord, text="mins", width=5, pady=5, padx=10).grid(row=1, column=2)

    customtkinter.CTkLabel(voiceConvRecord, text="Name:", width=5, pady=5, padx=10).grid(row=3, column=0)
    convNameEntry = customtkinter.CTkEntry(voiceConvRecord)
    convNameEntry.grid(row=2, column=1, pady=5, padx=5, columnspan=2)

    #Save Directory
    convDirectEntry = customtkinter.CTkEntry(voiceConvRecord)
    LoadDirectory(convDirectEntry, "recSaveDirectory")
    convDirectEntry.grid(row=3, column=0, columnspan=3, sticky=EW, pady=5, padx=5)

    customtkinter.CTkLabel(voiceConvRecord, text="Dir:", pady=5, padx=10).grid(row=4, column=0)
    convDirectButton = customtkinter.CTkButton(voiceConvRecord, text='Browse...', command = lambda: GetDirectory(convDirectEntry, "recSaveDirectory"))
    convDirectButton.grid(row=4, column=2)
    
    recordButton= customtkinter.CTkButton(voiceConvRecord, text='Record', command= async_handler(RecordAudio))
    recordButton.grid(row=5, column=0, columnspan=3, pady=5, padx=10)

    recBar = customtkinter.CTkProgressBar(voiceConvRecord, orientation="horizontal", width=200)
    recBar.set(0)
    recBar.grid(row=6, column=0, columnspan=3, pady=5, padx=10)

    saveSelection = customtkinter.CTkFrame(rightFrame)
    saveSelection.grid(row=2, column=0, padx=10, pady=10, sticky=EW+S)
    saveSelection.columnconfigure(0, weight=1)
    saveSelection.rowconfigure(0, weight=1)
    saveSelection.columnconfigure(1, weight=1)
    saveSelection.rowconfigure(1, weight=1)
    saveSelection.rowconfigure(2, weight=1)
    saveSelection.rowconfigure(3, weight=1)

    #Save Name
    customtkinter.CTkLabel(saveSelection, text="Name:", width=5, pady=5, padx=10).grid(row=0, column=0)
    nameEntry = customtkinter.CTkEntry(saveSelection)
    nameEntry.grid(row=0, column=1, sticky=EW, pady=5, padx=5)

    #Browse button
    directButton = customtkinter.CTkButton(saveSelection, text='Browse...', command = lambda: GetDirectory(directEntry, "saveDirectory"))
    directButton.grid(row=1, column=1, sticky=E)

    #Save Directory
    customtkinter.CTkLabel(saveSelection, text="Dir:", pady=5, padx=10).grid(row=1, column=0, sticky=W)
    directEntry = customtkinter.CTkEntry(saveSelection)
    LoadDirectory(directEntry, "saveDirectory")
    directEntry.grid(row=2, column=0, columnspan=2, sticky=EW, pady=5, padx=5)

    #Finish button
    finishButton = customtkinter.CTkButton(saveSelection, text="Finish", command=async_handler(Finish), height=40, state="disabled")
    finishButton.grid(row=3, column=0, columnspan=2)

    def ConstUpdate():
        root.after(1000, ConstUpdate)
        if (dropLangs.get() != dropLangsDefault and dropSpeakers.get() != dropSpeakersDefault and dropModels.get() != dropModelsDefault) or conv:
            if textEntry.get('1.0', END) != "":
                finishButton.configure(state="normal")
            if previewsGenerated:
                previewButton.configure(state="normal")
        else:
            finishButton.configure(state="disabled")
            previewButton.configure(state="disabled")
    ConstUpdate()

    root.protocol("WM_DELETE_WINDOW", OnRootClose)

    #Define main loop
    async_mainloop(root)

    ########## Main Window ###########

if __name__ == "__main__":
    main()