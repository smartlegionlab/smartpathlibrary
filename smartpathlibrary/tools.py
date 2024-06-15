# --------------------------------------------------------
# Licensed under the terms of the BSD 3-Clause License
# (see LICENSE for details).
# Copyright (c) 2018-2024, A.A. Suvorov
# All rights reserved.
# --------------------------------------------------------
import inspect
import os
import shlex
from itertools import chain
from pathlib import Path
from typing import Iterable


class Counter:
    @classmethod
    def get_count(cls, iter_obj):
        if not isinstance(iter_obj, Iterable):
            raise TypeError
        count = 0
        for _ in iter_obj:
            count += 1
        return count


def get_root_path(file_name):
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    folder = os.path.dirname(os.path.abspath(filename))
    abs_path = os.path.join(folder, file_name)
    return abs_path


class PathNormalizer:
    @classmethod
    def normalize(cls, path: str) -> str:
        return shlex.quote(path) if os.name == 'posix' else path


class PathBase:
    """Abstract path."""
    def __init__(self, name):
        """
        :param name: - the full path to the file or folder.
        """
        self._name = name

    def exists(self):
        """Check for existence."""
        return os.path.exists(self._name)

    @property
    def name(self):
        return self._name

    def __str__(self):
        return f'{self._name}'


class File(PathBase):
    def __init__(self, name):
        super().__init__(name)


class Folder(PathBase):
    def __init__(self, name):
        super().__init__(name)


class Dir(PathBase):

    counter = Counter()

    def __init__(self, name):
        super().__init__(name)

    def get_files(self, recursive=True):
        """
        Generates a generator of files attached to a folder.
        :param recursive: - True = consider all attached files recursively,
        False = only files inside the folder.
        :return: - iterator with file paths.
        """
        if recursive:
            return self._files_walk_gen()
        else:
            return self._files_listdir_gen()

    def _files_listdir_gen(self):
        """
        Generates a generator from file paths, only inside the folder.
        :return: - Generates a generator from file paths.
        """
        return (File(Path(self._name).joinpath(file))
                for file in Path(self._name).iterdir() if Path(file).is_file())

    def _files_walk_gen(self):
        """
        Generates a generator from the paths to files,
        including those nested recursively in all subfolders.
        :return: - Generates a generator from file paths.
        """
        return (File(os.path.join(p, file))
                for p, _, files in os.walk(self._name) for file in files)

    def get_dirs(self, recursive=True):
        """
        Generates a generator of folders attached to a folder.
        :param recursive: - True = consider all attached folders recursively,
        False = only folders inside the folder.
        :return: - iterator with folder paths.
        """
        if recursive:
            return self._dirs_walk_gen()
        else:
            return self._dirs_listdir_gen()

    def _dirs_walk_gen(self):
        """
        Generates a generator from the paths to folder,
        including those nested recursively in all subfolders.
        :return: - Generates a generator from folder paths.
        """
        return (Folder(os.path.join(p, dir_))
                for p, dirs, _ in os.walk(self._name) for dir_ in dirs)

    def _dirs_listdir_gen(self):
        """
        Generates a generator from folder paths, only inside the folder.
        :return: - Generates a generator from folder paths, only inside the folder.
        """
        return (Folder(Path(self._name).joinpath(dir_))
                for dir_ in Path(self._name).iterdir() if Path(dir_).is_dir())

    def get_count_files(self, recursive=True):
        """
        The counter of attached files.
        :param recursive: - True = consider all attached files recursively,
        False = only files inside the folder.
        :return: - number of files.
        """
        return self.counter.get_count(self.get_files(recursive=recursive))

    def get_count_dirs(self, recursive=True):
        """
        The counter of attached folders.
        :param recursive: - True = consider all attached folders recursively,
        False = only folders inside the folder.
        :return: - number of folders.
        """
        return self.counter.get_count(self.get_dirs(recursive=recursive))


class PathManager:
    counter = Counter()

    """File and Folder Path Manager."""
    def __init__(self):
        self._files = {}
        self._dirs = {}

    @property
    def paths(self):
        return {**self._files, **self._dirs}

    def add_path(self, path: str):
        """
        Adding a path.
        :param path: - the path to the file or folder as a string.
        :return: - None.
        """
        if os.path.isdir(str(path)):
            self._dirs[path] = Dir(path)
        elif os.path.isfile(path):
            self._files[path] = File(path)

    def remove_path(self, path: str):
        """
        Deleting a path.
        :param path: - the path to the file or folder as a string.
        :return: - None.
        """
        if str(path) in self._files:
            del self._files[path]

        if str(path) in self._dirs:
            del self._dirs[path]

    def add_paths(self, paths):
        """
        Adding a paths.
        :param paths: - an iterable object with paths.
        :return: - None.
        """
        for path in paths:
            self.add_path(path)

    def remove_paths(self, paths):
        """
        Deleting a paths.
        :param paths: - an iterable object with paths.
        :return: - None.
        """
        for path in paths:
            self.remove_path(path)

    def get_files(self, recursive=True):
        """
        Getting file paths.
        :param recursive: - True = consider all attached folders recursively,
        False = only folders inside the folder.
        :return: - Iterable object with file paths.
        """
        file_gen = (str(file) for file in self._files.values()
                    if os.path.isfile(str(file)))
        if recursive:
            files = (str(file) for gen in self._dirs.values()
                     for file in gen.get_files())
        else:
            files = (str(file) for gen in self._dirs.values()
                     for file in gen.get_files(recursive=False))
        return chain(file_gen, files)

    def get_dirs(self, recursive=True):
        """
        Getting folder paths.
        :param recursive: - True = consider all attached folders recursively,
        False = only folders inside the folder.
        :return: - Iterable object with folder paths.
        """

        return (str(dir_) for gen in self._dirs.values() for dir_ in gen.get_dirs(recursive=recursive))

    @property
    def count(self):
        """
        The total number of paths added.
        :return: - <int> - the total number of paths added.
        """
        return sum([len(self._files), len(self._dirs)])

    def get_count_files(self, recursive=True):
        """
        Number of files.
        :param recursive: - True = consider all attached folders recursively,
        False = only folders inside the folder.
        :return: - the total number of files added.
        """
        return self.counter.get_count(self.get_files(recursive=recursive))

    def get_count_dirs(self, recursive=True):
        """
        Number of folders.
        :param recursive: - True = consider all attached folders recursively,
        False = only folders inside the folder.
        :return: - the total number of folders added.
        """
        return self.counter.get_count(self.get_dirs(recursive=recursive))

    def __str__(self):
        return f'Paths({self.count})'
