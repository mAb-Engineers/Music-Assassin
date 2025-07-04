""" GUI - With logger - FFMPEG with pipes - Snipping ending audios - Closes without error -
    Uses lesser Memory - No Spawning - Maintains proper queue - Reduced imports - 
    Corrected audio output - Functions reshuffled - onclose updated - Handles subs  """

# For GUI
import os # For Admin Permissions
from tkinter import Tk, Button, filedialog, messagebox, Label

# For Logger
import sys  # For Logger
from tkinter.scrolledtext import ScrolledText
    
class PrintLogger(object):  # create file like object
    def __init__(self, textbox):  # pass reference to text widget
        self.textbox = textbox  # keep ref
    def write(self, text):
        self.textbox.configure(state="normal")  # make field editable
        self.textbox.insert("end", text)  # write text to textbox
        self.textbox.see("end")  # scroll to end
        self.textbox.configure(state="disabled")  # make field readonly
    def flush(self):  # needed for file like object
        pass
    
def Logger():
    log_widget = ScrolledText(root, height=20, font=("consolas", "8", "normal"))
    log_widget.pack(fill="x", padx=(20,20))
    logger = PrintLogger(log_widget)
    sys.stdout = logger
    sys.stderr = logger
    
def Labels(): #Label Functions
    title = Label(root, text = "Music Assassin", font = "Verdana 18 bold", bg='white')  
    title.pack(side="top", expand=None, fill="x", padx=(10,10), pady=(20, 0)) 
    
    credits = Label(root, text = "—A project of mAb Engineers",font = "Verdana 6", bg='white')  
    credits.pack(side="top", expand=None, fill="x", padx=(10, 10), pady=(0, 0))
    
    prompt = Label(root, text = "Choose the video to de-music:",font = "Verdana 13 bold", bg='white')  
    prompt.pack(side="top", expand=None, fill="x", padx=(10, 10), pady=(7, 10))
    
    
#Setting up GUI
root = Tk()
root.wm_title("Music Assassin")
root.geometry("400x500") #Window or Display Size
root.configure(background = 'white')
Labels() #Title Labels
files = []
process1 = 0
process2 = 0
separator = 0
pbar = 0
do = 0
sample_rate = 44100   
b1 = Button(text = "Browse",  bg="black", fg="white",font = "Verdana 10 bold")
b1.pack(side="top", expand=None, fill="x", padx=(20,20))
f1 = Button(text = "Demusic", bg="black", fg="white",font = "Verdana 10 bold")
f1.pack(side="top", expand=None, fill="x", padx=(20,20))
a1 = Button(text = "Remove Audio", bg="black", fg="white",font = "Verdana 10 bold")
a1.pack(side="top", expand=None, fill="x", padx=(20,20))
Logger()

if __name__ == '__main__':
    root.update_idletasks()
    root.update()
    
    
# For GUI
from tkinter.ttk import Progressbar

# For Demusic
from spleeter.audio.adapter import AudioAdapter
from spleeter.separator import Separator
from numpy import frombuffer, shape, zeros, swapaxes, newaxis, ceil
from ffmpeg import input, probe


def on_closing():
    global files
    global process1
    global process
    global separator
    global pbar
    if do == 0:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        root.destroy()
    else:
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            if process1:
                process1.kill()
            if process2:
                process2.kill()
            if separator:  
                separator.join()
                separator.close_pool()
            if pbar:
                pbar = 0
            root.destroy()

class MySeparator(Separator): # Solution from: https://github.com/deezer/spleeter/issues/725
    def close_pool(self):
        if self._pool:
            self._pool.close()
            self._pool.terminate()
    
def get_file_path():
    global files
    # Open and return file path
    file_path = ""
    browse = [""]
    browse = filedialog.askopenfilename(title = "Select A File", filetypes = (("mp4", "*.mp4"), (".mp3","*.mp3"), (".wav","*.wav"), ("wmv", "*.wmv"), ("avi", "*.avi"), (".pcm","*.pcm"), (".aiff","*.aiff"), (".aac","*.aac"), (".ogg","*.ogg"), (".wma","*.wma"), (".flac","*.flac"), (".alac","*.alac"),("All files", "*.*")), multiple=True)
    for i in browse:
        file_path = i
        if file_path not in files and file_path != "":
            print(file_path)
            root.update()
            files.append(file_path)
    browse = [""]
    

def check_streams(file_path): # Solution from: https://github.com/kkroening/ffmpeg-python/issues/204 (ingles98 commented on Mar 2, 2020)
    video = None
    audio = None
    subs  = None
    streams = probe(file_path)["streams"]
    for stream in streams:
        if stream["codec_type"] == "audio":
            audio = True
        if stream["codec_type"] == "video":
            video = True
        if stream["codec_type"] == "subtitle":
            subs = True
    return (video, audio, subs)
    
    
def demusic(file_path):
    """ testffmpeg """
    global root
    
    global process1
    global process2
    global process3
    global separator
    global pbar
    global sample_rate
                                             
    # Making names of files
    file_path = file_path.replace("\\", "/")
    name = (((file_path.split("/"))[-1]).split("."))[0]
    extension = (((file_path.split("/"))[-1]).split("."))[-1]
    path = "/".join(file_path.split("/")[:-1])
    output_path = path + '/' + name + "-no-music." + extension

    # Separating audio and video by ffmpeg
    print("-> Loading file")
    root.update()
    input_ = input(file_path,  noaccurate_seek=None)
    (video, audio, subs) = check_streams(file_path)
    if audio == None:
        print("Audio track not detected")
        return
    if video:
        video = input_.video
    if subs:
        subs = input_['2']
    
    process1 = ( #     pipe:0 is for stdin and pipe:1 is for stdout
        input_
        .output('pipe:1', format='f32le', ac=1, ar=sample_rate)
        .overwrite_output()
        .run_async(pipe_stdin=False, pipe_stdout=True, pipe_stderr=True, quiet=False))
    out,_ = process1.communicate(input=input_)
    process1.kill()
    
    waveform = frombuffer(out, dtype='<f4') # Buffer to Numpy
    waveform_shape = waveform.shape
    waveform = waveform[:,newaxis] 
    t = sample_rate*30 # number of samples
    no_split = int(ceil(waveform.shape[0]/t))
    
    # Perform the separation :
    print("-> Seperating music")
    root.update()
    no_music = zeros(waveform_shape)
    overlap = sample_rate*3
    start = 0
    
    separator = MySeparator('spleeter:2stems') 
    pbar = Progressbar(root, orient="horizontal", length=300, mode='determinate')
    pbar.pack(side="top", expand=None, fill="x", padx=(20,20))
    s = 100/no_split
    for i in range(no_split):
        if i == 0:
            pred = separator.separate(waveform[start:start+t+overlap])
            no_music[start:start+t]= swapaxes(pred['vocals'],0,1)[0][0:t]
    
        else:
            pred = separator.separate(waveform[start-overlap:start+t+overlap])
            no_music[start:start+t]= swapaxes(pred['vocals'],0,1)[0][overlap:t+overlap]
            
        start += t
        if pbar:
            pbar.step(s)
            root.update_idletasks()
            root.update()
        else:
            return 
        separator.join()
        separator.close_pool()
    pbar.pack_forget()
    separator = 0
    
    print("-> Exporting")
    root.update()
    no_music = no_music.astype('<f4').tobytes() # Numpy to Buffer
    
    if video == None:
        process2 = (
            input('pipe:0', format='f32le', ar=sample_rate)
            .output(output_path, format=extension, strict='experimental')
            .overwrite_output()
            .run_async(pipe_stdin=True, pipe_stderr=True, quiet=True))
    elif subs == None:
        process2 = (
            input('pipe:0', format='f32le', ar=sample_rate)
            .output(video, filename=output_path, format=extension,  vcodec='copy', acodec='aac', strict='experimental')
            .overwrite_output()
            .run_async(pipe_stdin=True, pipe_stderr=True, quiet=True))
    else:
        process2 = (
            input('pipe:0', format='f32le', ar=sample_rate)
            .output(video, subs, filename=output_path, vcodec='copy', acodec='aac')
            .overwrite_output()
            .run_async(pipe_stdin=True, pipe_stderr=True, quiet=True))
        
    err = process2.communicate(input=no_music)
    process2.kill()
        
    print("Done")
    process1 = 0
    process2 = 0
    
def demusic_list():
    global files
    global pbar
    global do
    
    if do:
        root.after(1000, demusic_list)
    else:
        to_do = [i for i in files]
        j = len(to_do)
        for i in range(j):
            do = 1
            print(f"File {i+1}/{j}")
            files.remove(to_do[i])
            demusic(to_do[i])
            if pbar == 0:
                return
        do = 0
        print("\nReady to demusic...")
        
def deAudio_list():
    global files
    
    j = len(files)
    for i in range(j):
        print(f"File {i+1}/{j}")
        deAudio(files[i])
    files = []
    print("\nReady to demusic...")
    
def deAudio(file_path):
    
    # Making names of files
    print("-> Deciding Names")
    root.update()
    file_path = file_path.replace("\\", "/")
    name = (((file_path.split("/"))[-1]).split("."))[0]
    extension = (((file_path.split("/"))[-1]).split("."))[-1]
    path = "/".join(file_path.split("/")[:-1])
    no_audio_path = path + '/' + name + "-no-audio." + extension
    
    print("-> Importing File")
    root.update()
    input_ = ffmpeg.input(file_path)
    print("-> Removing Audio")
    root.update()
    input_video = input_.video
    
    print("-> Exporting File")
    root.update()
    input_video.output(no_audio_path).run()
    
    print("Done")


root.protocol("WM_DELETE_WINDOW", on_closing)
b1.configure(command = get_file_path)
f1.configure(command = demusic_list)
a1.configure(command = deAudio_list)

print("Ready to demusic...")

root.mainloop()
