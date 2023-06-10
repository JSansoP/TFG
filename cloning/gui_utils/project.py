import json
import os


class Project:
    @staticmethod
    def fromJSON(json_str):
        return json.loads(json_str, object_hook=lambda args: Project(**args))

    def __init__(self, project_name, directory, audios=None):
        self.project_name = project_name
        self.directory = directory
        self.audios = audios if audios else list()

    def add_audio(self, sentence):
        audio = {"sentence": sentence,
                 "path": os.path.join(self.directory, "wavs", str(self.next_audio_index()) + ".wav")}
        self.audios.append(audio)

    def next_audio_index(self):
        if len(self.audios) == 0:
            return 0
        else:
            return int(self.audios[-1]["path"].split("\\")[-1].split(".")[0]) + 1

    def current_audio_index(self):
        if len(self.audios) == 0:
            return 0
        else:
            return int(self.audios[-1]["path"].split("\\")[-1].split(".")[0])

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4, ensure_ascii=False)
