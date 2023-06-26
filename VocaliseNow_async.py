from TTS.api import TTS
from tkinter import *  
from tkinter import filedialog
from os.path import exists
from playsound import playsound
from mutagen import wave
import asyncio
import customtkinter
import os
import json

########## Json handling ##########
def CreateSettings():
        # Data to be written
        dictionary = {
            "saveDirectory": str(os.getcwd()),
            "modelDirectory": str(os.getcwd()),
            "genMeta": "True"
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
    with open("settings.json", "r") as settingsJson:
        settings = json.load(settingsJson)

    value = settings[str(id)]

    if switch != None:
        if value == "True":
            switch.select()
        elif value == "False":
            switch.deselect()
    
    if id == "genMeta":
        genMetaBool = bool(value)

def UpdateSettingBool(id, value):
    with open("settings.json", "r") as settingsJson:
        settings = json.load(settingsJson)

    settings[str(id)] = str(value)

    with open("settings.json", "w") as outfile:
        json.dump(settings, outfile, indent=4)

def GetDirectory(entry, id):
    #Get a directory path by user
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
    entry.insert(0,PullDirectory(id))

def PullDirectory(id):
    with open("settings.json", "r") as settingsJson:
        settings = json.load(settingsJson)
    return settings[str(id)]

########## Json handling ##########

########## TTS ##########

def PickModel(overide: str = ""):
    #Define voice model
    global tts
    path = str(PullDirectory("modelDirectory"))
    if overide == "":
        for model in TTS.list_models():
            modelType, lang, dataset, modelName = model.split("/")
            if lang == dropLangs.get() and dataset == dropSpeakers.get() and modelName == dropModels.get():
                fullModelName = modelType+"/"+lang+"/"+dataset+"/"+modelName
        tts = TTS(fullModelName, output_path=path)
        return fullModelName
    else:
        tts = TTS(overide, output_path=path)
        return overide
    
#Generate TTS voice
def GenTTS():
    fullModelName = PickModel()
    newText = ParseText(textEntry.get('1.0', END)) + "$"
    name = nameEntry.get()
    directory = PullDirectory("saveDirectory") + "/" + name
    if not os.path.exists(directory):
        os.mkdir(directory)

    if genMetaBool:
        CreateMeta(directory, name, newText, fullModelName)

    i = 0
    para = ""
    for char in newText:
        if char == "$":
            CreateAudio(para, directory, name, i)
            para = ""
            i += 1
        else:
            para += char

def CreateAudio(text, directory, name, id):
    if tts.is_multi_speaker:
        if tts.is_multi_lingual:
            tts.tts_to_file(text=text, speaker=dropSpeakers.get(), language=dropLangs.get(), file_path=directory + "/"+name + str(id) +".wav")
        else:
            tts.tts_to_file(text=text, speaker=dropSpeakers.get(), file_path=directory + "/"+name + str(id) +".wav")
    elif tts.is_multi_lingual:
        tts.tts_to_file(text=text, language=dropLangs.get(), file_path=directory + "/"+name + str(id) +".wav")
    else:
        tts.tts_to_file(text=text, file_path=directory + "/"+name + str(id) +".wav")
    

def ParseText(text):
    out = ""
    for char in text:
        if char != "\n":
            out += char
    return out

########## TTS ##########

########## Dropdown handling ##########

def UpdateDrops(dropIndx: int = None):
    global allModels
    global allLangName
    global allVoiceName
    global allModelName
    global defaultValues

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
    
    if dropLangs.get() != dropLangsDefault and dropSpeakers.get() != dropSpeakersDefault and dropModels.get() != dropModelsDefault:
        if textEntry.get('1.0', END) != "":
            finishButton.configure(state="normal")
        previewButton.configure(state="normal")
    else:
        finishButton.configure(state="disabled")
        previewButton.configure(state="disabled")

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
    
########## Experimental ###########

def GenPreviews():
    global tts
    for model in TTS.list_models():
        modelType, lang, dataset, modelName = model.split("/")
        fullModelName = modelType+"/"+lang+"/"+dataset+"/"+modelName
        if modelName != "your_tts" and lang == "en" and dataset != "vctk" and dataset != "multi-dataset":
            tts = TTS(fullModelName, output_path=str(PullDirectory("modelDirectory")))
            dir1 = PullDirectory("saveDirectory") + "/" + modelType
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
            directory = PullDirectory("saveDirectory") + "/" + modelType + "/" + lang + "/" + dataset + "/" + modelName
            saveName = lang + "-" + dataset + "-" + modelName
            if tts.is_multi_speaker:
                if tts.is_multi_lingual:
                    tts.tts_to_file(text="this is a preview of this voice", speaker=dataset, language=lang, file_path=directory + "/"+saveName +".wav")
                else:
                    tts.tts_to_file(text="this is a preview of this voice", speaker=dropSpeakers.get(), file_path=directory + "/"+saveName +".wav")
            elif tts.is_multi_lingual:
                tts.tts_to_file(text="this is a preview of this voice", language=dropLangs.get(), file_path=directory + "/"+saveName +".wav")
            else:
                tts.tts_to_file(text="this is a preview of this voice", file_path=directory + "/"+saveName +".wav")

def PlayPreview():
    soundName = dropLangs.get() + "-" + dropSpeakers.get() + "-" + dropModels.get() + ".wav"
    soundPath = "./tts_models/" + dropLangs.get() + "/" + dropSpeakers.get() + "/" + dropModels.get() + "/" + soundName
    #previewSound = wave(soundPath)
    playsound(soundPath)

def VoiceConv():
    tts = TTS(model_name="voice_conversion_models/multilingual/vctk/freevc24", progress_bar=False, output_path=str(PullDirectory("modelDirectory")))
    tts.voice_conversion_to_file(source_wav="source.wav", target_wav="target.wav", file_path="output.wav")

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
    #sett.iconbitmap("./Lib/icons/Cog.ico")
    sett.attributes("-topmost", "true")
    root.attributes("-disabled", "true")

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

    genMetaSwitch = customtkinter.CTkSwitch(sett, text="Generate meta data for Unity", onvalue="True", offvalue="False", command= lambda: UpdateSettingBool("genMeta", genMetaSwitch.get()))
    GetSettingBool(genMetaSwitch, "genMeta")
    genMetaSwitch.grid(row=1, column=0)

    #Finishing window
    sett.protocol("WM_DELETE_WINDOW", OnSettClose)
    sett.mainloop()

########## Settings Window ###########

def init():
    global dropsList
    global dropsDefaults
    global dropLangsDefault
    global dropSpeakersDefault
    global dropModelsDefault

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

    customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"
    #GenPreviews()

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
    global finishButton
    global previewButton
    
    init()
    ########## Main Window ###########

    #Make main window
    root = customtkinter.CTk()
    #root.iconbitmap("./Lib/icons/LogoS.ico")
    root.title("CoquiTTS Generator")
    root.geometry("1000x600")
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

    #previews = customtkinter.CTkButton(rightFrame, text='previews', command = lambda: GenPreviews())
    #previews.grid(row=2, column=0, pady=5, padx=5, columnspan=2)

    #convert = customtkinter.CTkButton(rightFrame, text='convert', command = lambda: VoiceConv())
    #convert.grid(row=2, column=0, pady=5, padx=5, columnspan=2)

    #Settings and info buttons
    settingsButton = customtkinter.CTkButton(root, text="Settings", command=SettingsPopUp)
    settingsButton.grid(row=0, column=1, sticky=NE, pady=5, padx=5)

    #Make text input field for text wanted
    customtkinter.CTkLabel(leftFrame, text="Text:").grid(row=0, column=0)
    textEntry = customtkinter.CTkTextbox(leftFrame, width=40, height=100)
    textEntry.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    tabFrame = customtkinter.CTkTabview(rightFrame)
    tabFrame.grid(row=0, column=0, padx=10, pady=10, sticky=N)
    tabFrame.add("Voices")
    tabFrame.add("Record")

    modelSelection = customtkinter.CTkFrame(tabFrame.tab("Voices"))
    modelSelection.grid(row=0, column=0, padx=10, pady=10, sticky=N)
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

    #dropModels.bind("<<ComboboxSelected>>", PickModel)

    voicePreview = customtkinter.CTkFrame(rightFrame)
    voicePreview.grid(row=1, column=0, padx=10, pady=10, sticky=EW)
    voicePreview.columnconfigure(0, weight=1)
    voicePreview.rowconfigure(0, weight=1)
    voicePreview.columnconfigure(1, weight=1)
    voicePreview.rowconfigure(1, weight=1)

    customtkinter.CTkLabel(voicePreview, text="Selected Voice Preview:", pady=5, padx=10).grid(row=0, column=0, columnspan=2)
    previewButton = customtkinter.CTkButton(voicePreview, text='Play', state="disabled", command = lambda: PlayPreview())
    previewButton.grid(row=1, column=0, sticky=W)

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
    finishButton = customtkinter.CTkButton(saveSelection, text="Finish", command=GenTTS, height=40, state="disabled")
    finishButton.grid(row=3, column=0, columnspan=2)
    

    #Define main loop
    root.mainloop()

    ########## Main Window ###########

if __name__ == "__main__":
    main()

class App(customtkinter.CTk):

    def __init__(self, loop, interval=1/120):
        super().__init__()
        self.loop = loop
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.tasks = []
        self.tasks.append(loop.create_task(self.rotator(1/60, 2)))
        self.tasks.append(loop.create_task(self.updater(interval)))

    async def rotator(self, interval, d_per_tick):
        canvas = tk.Canvas(self, height=600, width=600)
        canvas.pack()
        deg = 0
        color = 'black'
        arc = canvas.create_arc(100, 100, 500, 500, style=tk.CHORD,
                                start=0, extent=deg, fill=color)
        while await asyncio.sleep(interval, True):
            deg, color = deg_color(deg, d_per_tick, color)
            canvas.itemconfigure(arc, extent=deg, fill=color)

    async def updater(self, interval):
        while True:
            self.update()
            await asyncio.sleep(interval)

    def close(self):
        for task in self.tasks:
            task.cancel()
        self.loop.stop()
        self.destroy()


def deg_color(deg, d_per_tick, color):
    deg += d_per_tick
    if 360 <= deg:
        deg %= 360
        color = '#%02x%02x%02x' % (rr(0, 256), rr(0, 256), rr(0, 256))
    return deg, color

loop = asyncio.get_event_loop()
app = App(loop)
loop.run_forever()
loop.close()