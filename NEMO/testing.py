import os
import subprocess
from subprocess import Popen, PIPE
import sys
try:
    sox_path = "C:/Program Files (x86)\sox-14-4-2\sox.exe"
    mp3_file = os.path.join(os.getcwd(),"clips","common_voice_ca_34927018.mp3")
    wav_file = os.path.join(os.getcwd(),"wavs","validated","common_voice_ca_34927018.wav")
    command1 = [f'"{sox_path}"', mp3_file, "-c", "1", "-r", "16000", wav_file]
    string_command = " ".join(command1)
    print(string_command)
    subprocess.run(string_command, shell=True)

    command2 = [f'"{sox_path}"', "--i", "-D", wav_file]
    string_command = " ".join(command2)
    print(string_command)
    duration = subprocess.run(string_command, shell=True, stdout=PIPE).stdout.decode('utf-8').strip()
    print("output: ", duration)

except:
    #Print the raised error
    print("Unexpected error:", sys.exc_info()[0])
    raise