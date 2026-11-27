import threading
from pathlib import Path
from lib import logger

class TimeoutPath():
    def __init__(self, strpath: str, timeout: float = 10):
        self._path = Path(strpath)
        self.timeout = timeout
        self.result = False
        
    def __check__(self):
        self.result = self._path.exists()

    def exists(self) -> bool:
        tr = threading.Thread(target=self.__check__) 
        tr.start()
        tr.join(self.timeout)
            
        return self.result

    def get_path(self) -> Path:
        return self._path

    def __str__(self) -> str:
        return str(self._path)
