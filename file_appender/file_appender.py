from __future__ import annotations

import abc
import atexit
import io
import json
import logging
import os
from datetime import datetime
from json import JSONDecodeError
from typing import Iterable, Tuple, TypeVar

from decorators import recursion_detector
from py_utils import exception_to_string


class IFileAppender(abc.ABC):
    
    @abc.abstractmethod
    def openStream(self) -> IFileAppender:
        pass
    
    @abc.abstractmethod
    def closeStream(self) -> None:
        pass
    
    @abc.abstractmethod
    def write(self, string:str):
        pass
    
    def __enter__(self):
        return self

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        self.closeStream()
        
    @abc.abstractmethod
    def containsData(self):
        pass
    
    @abc.abstractmethod
    def loadData(self):
        pass
    
            
class FileReader(abc.ABC):
    
    def __init__(self, fileName:str, extension:str) -> None:
        parent_dir = os.getcwd()
        if os.path.basename(parent_dir) == 'notebooks':
            parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
            
        nameIt = f'data/url_pioneer_{fileName}.{extension}'
        if bool(extension) and (fileName.endswith(f'.{extension}') or (fileName.endswith(f'{extension}') and extension.startswith('.'))):
            nameIt = f'data/url_pioneer_{fileName}'
            
        
        self._fileName = os.path.join(parent_dir, nameIt)
        if not os.path.exists(self._fileName):
            with open(self._fileName, 'w') as f:
                pass
        self._file:io.TextIOWrapper|None = None
        atexit.register(self.closeStream)
        
        
    def openStream(self) -> FileReader:
        self._file = open(self._fileName, 'r')
        return self
    
    def closeStream(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
    
    @abc.abstractmethod
    def read(self):
        if self._file is not None and self._file.readable:
            return self._file.read()
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.closeStream()
        
    def containsData(self):
        data = self.read()
        return bool(data)
    

class DummyFileAppender(IFileAppender):
    def __init__(self, logname:str) -> None:
        self._fileName = f'../data/url_pioneer_{logname}.txt'
        atexit.register(self.closeStream)
    
    def openStream(self):
        timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        print(f'FileOpenEvent: ({timestamp})')
        print(f'DummyFileNamedEvent: ({self._fileName})')
        return self
        

    def closeStream(self):
        timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        print(f'FileCloseEvent: ({timestamp})')
        
    def write(self, string:str):
        print(f'DummyFileWriteEvent: {string}')
        
    def containsData(self):
        return False
    
    def loadData(self):
        return ''
            
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.closeStream()

class FileAppender(IFileAppender, abc.ABC):
    def __init__(self, logname:str, extension:str) -> None:
        parent_dir = os.getcwd()
        if os.path.basename(parent_dir) == 'notebooks':
            parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
        
        nameIt = f'data/url_pioneer_{logname}.{extension}'
        if logname.endswith(extension) and bool(extension):
            nameIt = f'data/url_pioneer_{logname}'
        
        self._fileName = os.path.join(parent_dir, nameIt)
        if not os.path.exists(self._fileName):
            os.makedirs(os.path.dirname(self._fileName), exist_ok=True)
            with open(self._fileName, 'w') as f:
                pass
        self._file:io.TextIOWrapper|None = None
        atexit.register(self.closeStream)
    
    def openStream(self) -> IFileAppender:
        self._file = open(self._fileName, 'a+')
        return self
    
    def closeStream(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None
    
    def write(self, string: str):
        if self._file is not None and self._file.writable:
            self._file.write(string)
            
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._file:
            self.closeStream()
            
            # Line below to delete the file:
            # os.unlink(self._file)

    def containsData(self):
        if self._file is not None:
            data = self._file.read()
            return bool(data)
        else:
            return False
    
    def loadData(self):
        return self._file.read() if self._file is not None else None
            
class TxtFileAppender(FileAppender):
    def __init__(self, logname:str) -> None:
        super().__init__(logname, 'txt')
        
        
    def openStream(self):
        self._file = open(self._fileName, 'a+')
        timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        self._file.write(f'\nFileOpenEvent: ({timestamp})\n')
        return self
    
    def write(self, string:str):
        super().write(string)
    
    def closeStream(self):
        if self._file is not None:
            try:
                timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
                self._file.write(f'\nFileCloseEvent: ({timestamp})\n')
            except Exception as e:
                logging.error(e)
            self._file.close()
            self._file = None
            
    def containsData(self):
        if self._file is not None:
            data = self._file.read()
            return bool(data)
        else:
            return False

    def loadData(self):
        return self._file.read() if self._file is not None else None
            
TX = TypeVar("TX", str, int, float, None, list, dict, Iterable, bool)

class JsonFileReader(FileReader):
    def __init__(self, fileName: str) -> None:
        super().__init__(fileName, 'json')
        
    def read(self):
        try:
            if self._file is not None:
                self._file.seek(0)
                return json.load(self._file)
            else:
                return None
        except JSONDecodeError as jsonE:
            logging.error(jsonE)
            raise jsonE
        except Exception as e:
            logging.error(e)
            raise e
            
class JsonFileAppender(FileAppender):
    
    def __init__(self, logname:str) -> None:
        super().__init__(logname, 'json')
        with open(self._fileName, 'r+') as file:
            if not file.read():
                json.dump({}, file, indent=4)
    
    def asEmptyDictionary(self):
        with open(self._fileName, 'w') as file:
            file.seek(0)
            json.dump({}, file, indent = 4)
            
    def asEmptyList(self):
        with open(self._fileName, 'w') as file:
            file.seek(0)
            json.dump([], file, indent = 4)
        
        
    def openStream(self):
        '''Open the json file for reads only'''
        self._file = open(self._fileName, 'r')
        return self
        
    def openWriteAppendStream(self):
        '''Open a file stream that is unable to truncate (delete / update any of) the target file'''
        self._file = open(self._fileName, 'w+')
        return self
    
    def openOverWriteStream(self):
        '''Open a file stream to overwrite the target file'''
        self._file = open(self._fileName, 'w')
        return self
    
    @recursion_detector()
    def flagOpenWriteStream(self):
        '''Creates the file at path if doesnt exist and writes over it, not updates it'''
        self.write({"FileOpenEvent": datetime.strftime(datetime.now(), '"%Y-%m-%d %H:%M:%S"')})
        return self
    
    @staticmethod
    def _mergeDicts(x:list[dict]) -> dict:
        if not x:
            return {}
        if len(x) == 1:
            return x[0]
        res = x[0]
        return [{**res, **sx} for sx in x[1:]][-1]
    
    @recursion_detector()
    def write(self, jsonObj:dict|list):
        
        file_data = type(jsonObj)()
        try:
            self._file = open(self._fileName, 'r')
            self._file.seek(0)
            file_data = json.load(self._file)
        except JSONDecodeError as jsonE:
            logging.error(jsonE)
            file_data = type(jsonObj)()
        except Exception as e:
            logging.error(e)
            file_data = type(jsonObj)()
        finally:
            self.closeStream()
            
        
        # Merge jsonObj with file_data
        def _updateDict(existingObj:TX, newObj:TX):
            keys:Tuple[str]
            merge_result:TX|list|dict = existingObj
            if isinstance(merge_result, dict) and isinstance(newObj, dict):
                for key in newObj.keys():
                    if key in merge_result.keys():
                        merge_result[key] = _updateDict(merge_result[key], newObj[key])
                    else:
                        merge_result[key] = newObj[key]
            elif isinstance(merge_result, dict) and isinstance(newObj, list):
                merge_result = [merge_result, *newObj]
            elif isinstance(merge_result, dict):
                merge_result = [merge_result, newObj]
            elif isinstance(merge_result, list) and isinstance(newObj, list):
                merge_result += newObj
            elif isinstance(merge_result, list):
                merge_result += [newObj]
            else:
                return merge_result
            return merge_result
        file_data = _updateDict(file_data, jsonObj)
        
        # Sets file's current position at offset.
        # self._file.seek(0)
        # Overwrite the entire file with the updated obj
        self._file = open(self._fileName, 'w')
        # convert back to json.
        try:
            json.dump(file_data, self._file, indent = 4)
        except Exception as e:
            logging.warning('Unable to write json to file as ' + exception_to_string(e))
        finally:
            self.closeStream()
        
    def containsData(self):
        if self._file is not None:
            data = self._file.read()
            return bool(data)
        else:
            return False
    
    def loadData(self):
        return json.load(self._file) if self._file is not None and str(self._file.read()) != '' else None
    
    @recursion_detector()
    def writeCloseStreamFlag(self):
        if self._file is not None:
            try:
                self.write({"FileCloseEvent": datetime.strftime(datetime.now(), '"%Y-%m-%d %H:%M:%S"')})
            except Exception as e:
                logging.error(e)
    
    @recursion_detector()
    def closeStream(self):
        if self._file is not None:
            self._file.close()
            self._file = None

