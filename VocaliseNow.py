from TTS.api import TTS
from tkinter import *
from tkinter import ttk  
from tkinter import filedialog
from tkinter import scrolledtext
from os.path import exists
import customtkinter
import threading
import asyncio
import json

#Def global variables
global tts
global sett
global modDirectEntry
global genMetaBool
global allModels
global allLangName
global allVoiceName
global allModelName
global defaultValues
global dropsList
global dropsDefaults

def main():
    global dropsList
    global dropsDefaults
    dropSpeakersDefault = "Select Voice"
    dropLangsDefault = "Select Language"
    dropModelsDefault = "Select Model"
    dropsDefaults = [dropLangsDefault, dropSpeakersDefault, dropModelsDefault]

    def CreateSettings():
        # Data to be written
        dictionary = {
            "saveDirectory": "",
            "modelDirectory": "",
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
            "model": model
        }

        i = 0
        para = ""
        for char in text:
            if char == "$":
                dictionary2 = {
                    "speech": para
                }
                dictionary["bubble"].append(dictionary2)
                para = " "
                i += 1
            else:
                para += char
        
        # Serializing json
        json_object = json.dumps(dictionary, indent=4)
        
        # Writing to sample.json
        with open(directory+"/meta_"+name+".json", "w") as outfile:
            outfile.write(json_object)

    def PickModel():
        #Define voice model
        global tts
        for model in TTS.list_models():
            modelType, lang, dataset, modelName = model.split("/")
            if lang == dropLangs.get() and dataset == dropSpeakers.get() and modelName == dropModels.get():
                fullModelName = modelType+"/"+lang+"/"+dataset+"/"+modelName
        path = str(PullDirectory("modelDirectory"))
        tts = TTS(fullModelName, output_path=path)
        return fullModelName

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

    #Generate TTS voice
    def GenTTS():
        fullModelName = PickModel()
        newText = ParseText(textEntry.get('1.0', END))

        if genMetaBool:
            CreateMeta(directEntry.get(), nameEntry.get(), newText + "$", fullModelName)

        if tts.is_multi_speaker:
            if tts.is_multi_lingual:
                tts.tts_to_file(text=newText, speaker=dropSpeakers.get(), language=dropLangs.get(), file_path=PullDirectory("saveDirectory") + "/"+nameEntry.get()+".wav")
            else:
                tts.tts_to_file(text=newText, speaker=dropSpeakers.get(), file_path=PullDirectory("saveDirectory") + "/"+nameEntry.get()+".wav")
        elif tts.is_multi_lingual:
            tts.tts_to_file(text=newText, language=dropLangs.get(), file_path=PullDirectory("saveDirectory") + "/"+nameEntry.get()+".wav")
        else:
            tts.tts_to_file(text=newText, file_path=PullDirectory("saveDirectory") + "/"+nameEntry.get()+".wav")


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
        settings[str(id)] = str(filepath)

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

    def OnSettClose():
        root.attributes("-disabled", "false")
        sett.destroy()

    def ParseText(text):
        out = ""
        for char in text:
            if char != "\n":
                out += char
        return out
        

    #Making settings file 
    fileExists = exists("settings.json")
    if not fileExists:
        CreateSettings()
    GetSettingBool()
    GetModelData()

    ########## Settings Window ###########

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

    customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

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

    saveSelection = customtkinter.CTkFrame(rightFrame)
    saveSelection.grid(row=1, column=0, padx=10, pady=10, sticky=EW+S)
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
    finishButton = customtkinter.CTkButton(saveSelection, text="Finish", command=GenTTS, height=40)
    finishButton.grid(row=3, column=0, columnspan=2)

    #Define main loop
    root.mainloop()

    ########## Main Window ###########

if __name__ == "__main__":
    main()