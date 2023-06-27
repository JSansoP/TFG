import json
import os


class Project:

    def __init__(self, project_name, directory, audios=None, index=0):
        self.project_name = project_name
        self.directory = directory
        self.audios = audios if audios else list()
        self.index = index

    def add_audio(self, sentence):
        audio = Audio(sentence, os.path.join(self.directory, "wavs", str(self.index) + ".wav"))
        self.index += 1
        self.audios.append(audio)


    @staticmethod
    def from_json(json_str):
        decoder = CustomDecoder()
        return json.loads(json_str, object_hook=lambda args: decoder.decode(args))

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4, ensure_ascii=False)


class CustomDecoder(json.JSONDecoder):
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.decode)
        self.audios = []
    def decode(self, object):
        if "sentence" in object:
            self.audios.append(Audio(object["sentence"], object["path"]))
        else:
            return Project(object["project_name"], object["directory"], self.audios, object["index"])


class Audio:

    def __init__(self, sentence, path):
        self.sentence = sentence
        self.path = path

    @staticmethod
    def from_json(json_str):
        return json.loads(json_str, object_hook=lambda args: Audio(**args))

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4, ensure_ascii=False)