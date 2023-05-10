set PYTHONIOENCODING=UTF-8
set PYTHONLEGACYWINDOWSSTDIO=UTF-8
set PHONEMIZER_ESPEAK_PATH=C:/Program Files/eSpeak NG/espeak-ng.exe

python "utils_sanso\train_vits_win_sanso.py" --restore_path "C:\Users\sanso\AppData\Local\tts\tts_models--es--css10--vits\model_file.pth.tar" --output_path "C:\Users\sanso\AppData\Local\tts\SALIDAS_MODELOS"
