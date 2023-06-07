import json


class Project:
    @staticmethod
    def fromJSON(json_str):
        return json.loads(json_str, object_hook=lambda args: Project(**args))

    def __init__(self, project_name, directory, audios=None):
        self._project_name = project_name
        self._directory = directory
        self._audios = audios if audios else list()

    def add_audio(self, audio):
        self._audios.append(audio)
    
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)
    
    @property
    def project_name(self):
        return self._project_name

    @property
    def directory(self):
        return self._directory
    
    @property
    def audios(self):
        return self._audios
