#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import base64
from cryptography.fernet import Fernet
import json
import requests
import pexpect
import os, os.path
import sys

class KeyRepository():
    repository = {}

    def __init__(self, repository_path, repository_key, init=False):
        self.repository_key = repository_key
        self.repository_path = repository_path
        if init:
            self.write()
        # try a read so we throw an exception if key is wrong
        self.read()

    def init(repository_path, repository_key=None):
        if not repository_key:
            repository_key = Fernet.generate_key()
        zkv = __class__(repository_path, repository_key, init=True)
        return zkv

    def read(self):
        with open(self.repository_path, 'rb') as key_store:
            f = Fernet(self.repository_key)
            data = f.decrypt(key_store.read())
            self.repository = json.loads(data)
        return self.repository.copy()

    def write(self):
        with open(self.repository_path, 'wb') as key_store:
            f = Fernet(self.repository_key)
            data = f.encrypt(json.dumps(self.repository).encode())
            key_store.write(data)

    def get_key(self):
        return self.repository_key

    def set_fs_key(self, fs_name, fs_key):
        self.repository[fs_name] = fs_key

    def remove_fs_key(self, fs_name):
        self.repository.pop(fs_name)

    def has_fs_key(self, fs_name):
        return fs_name in self.repository

class Program:
    def __init__(self, repository_path):
        self.repository_path = repository_path

        root_parser = argparse.ArgumentParser(description="ZFS integration with Azure Key Vault")

        # Create the parsers for top-level commands
        subparser = root_parser.add_subparsers(help='commands', dest='action')
        fs_action_p = subparser.add_parser('fs', help='Configure a local, encrypted repository of ZFS filesystem encryption keys')
        fetch_action_p = subparser.add_parser('fetch', help="Fetch repository's encryption key and print it")
        mount_action_p = subparser.add_parser('mount', help="Fetch repository's encryption key and mount all configured ZFS filesystems")

        # Creat options for top-level commands
        for cmd in [fetch_action_p, mount_action_p]:
            cmd.add_argument("gateway_uri", help="URI to the ZFS Key Vault Gateway providing the keys")

        # Create the parsers for fs commands
        fs_action_sp = fs_action_p.add_subparsers(help='fs commands', dest='fs_action')
        fs_action_init_p = fs_action_sp.add_parser('init', help='Initialize a local, encrypted repository')
        fs_action_list_p = fs_action_sp.add_parser('list', help='List configured filesystems in the repository')
        fs_action_add_p = fs_action_sp.add_parser('add', help="Add a filesystem encryption key to the repository")
        fs_action_remove_p = fs_action_sp.add_parser('remove', help="Remove a filesystem encryption key from the repository")

        # Create options for fs commands
        fs_action_init_p.add_argument("-m", "--machine-readable", action='store_true', help="Machine-readable output (prints only the encryption key)")
        fs_action_init_p.add_argument("-f", "--force", action='store_true', help="Overwrite existing repository, if one exists")
        fs_action_init_p.add_argument("-k", "--repository-key", help="Supply the base64-encoded Fernet key used to encrypt the repository")

        for cmd in [fs_action_list_p, fs_action_add_p, fs_action_remove_p]:
            cmd.add_argument("repository_key", help="Base64-encoded Fernet encryption key for the repository")

        for cmd in [fs_action_add_p, fs_action_remove_p]:
            cmd.add_argument("filesystem", help="Name of ZFS filesystem including pool (e.g. tank/myfs)")
        fs_action_add_p.add_argument("fs_key", help="Encryption key for the ZFS filesystem")
        fs_action_add_p.add_argument("-f", "--force", action='store_true', help="Overwrite existing encryption key for provided filesystem, if one exists")
        fs_action_remove_p.add_argument("-f", "--force", action='store_true', help="Proceed normally if filesystem does not exist in repository")
        fs_action_list_p.add_argument("-p", "--plaintext", action='store_true', help="Print configured encryption key in plaintext")

        self.options = root_parser.parse_args()

    def __fetch_repo_key(self):
        r = requests.get(self.options.gateway_uri)
        if r.status_code == 200:
            return r.text
        else:
            sys.stderr.write("Error: attempt to obtain encryption keys failed due to invalid HTTP status code %d\n" % r.status_code)
            sys.exit(1)

    def __load_key_pexpect(self):
        child = pexpect.spawn("zfs", ["load-key", filesystem])
        child.expect(":", timeout=10)
        child.sendline(encryption_key)
        child.wait()
        child.close()
        if child.exitstatus != 0:
            sys.stderr.write("Error: loading encryption keys for filesystem %(filesystem)s failed due to zfs exit status %(exit_status)d\n" % {'filesystem': filesystem, 'exit_status': child.exitstatus})

    def __read_repo(self, repository_key):
        try:
            zkv = KeyRepository(self.repository_path, repository_key)
            return zkv
        except:
            raise
            sys.stderr.write("Could not decrypt key repository; please verify repository key\n")
            sys.exit(1)

    def fetch(self):
        repository_key = self.__fetch_repo_key()
        print(repository_key)

    def mount(self):
        repository_key = self.__fetch_repo_key()
        zkv = self.__read_repo(repository_key)
        fs = zkv.read()
        for filesystem, encryption_key in fs.items():
            self.__load_key_pexpect(filesystem, encryption_key)

    def fs_add(self):
        zkv = self.__read_repo(self.options.repository_key)
        fs = zkv.read()
        if not self.options.force and zkv.has_fs_key(self.options.filesystem):
            sys.stderr.write("An existing filesystem key for '%s' was found in the keystore\n" % self.options.filesystem)
            sys.exit(1)
        zkv.set_fs_key(self.options.filesystem, self.options.fs_key)
        zkv.write()

    def fs_init(self):
        if not self.options.force and os.path.exists(repository_path):
            if not self.options.machine_readable:
                sys.stderr.write("An existing keystore was found at '%s', use -f to overwrite\n" % repository_path)
            sys.exit(1)
        repository_key = self.options.repository_key.encode() if self.options.repository_key else None
        zkv = KeyRepository.init(repository_path, repository_key=repository_key)
        repository_key = zkv.get_key().decode('ascii')
        if self.options.machine_readable:
            print(repository_key)
        else:
            print("New repository created at '%s'. Take note of its encryption key, it will not be displayed again:" % repository_path)
            print("%s\n" % repository_key)
            print("[!] Loss of this key requires re-creation of the entire repository.")

    def fs_list(self):
        zkv = self.__read_repo(self.options.repository_key)
        fs = zkv.read()
        for filesystem, fs_key in fs.items():
            if self.options.plaintext:
                print("%s: %s" % (filesystem, fs_key))
            else:
                print("%s" % filesystem)

    def fs_remove(self):
        zkv = self.__read_repo(self.options.repository_key)
        fs = zkv.read()
        if not zkv.has_fs_key(self.options.filesystem):
            if self.options.force:
                sys.exit(0)
            else:
                sys.stderr.write("No key for filesystem '%s' was found in the keystore\n" % self.options.filesystem)
                sys.exit(1)
        zkv.remove_fs_key(self.options.filesystem)
        zkv.write()

    def run(self):
        if self.options.action == "fetch":
            p.fetch()
        elif self.options.action == "mount":
            p.mount()
        elif self.options.action == "fs":
            if self.options.fs_action == "init":
                p.fs_init()
            elif self.options.fs_action == "list":
                p.fs_list()
            elif self.options.fs_action == "add":
                p.fs_add()
            elif self.options.fs_action == "remove":
                p.fs_remove()
            else:
                fs_action_p.print_usage()
                sys.exit(1)
        else:
            root_parser.print_usage()
            sys.exit(1)

if __name__ == "__main__":
    repository_path = os.path.expanduser('~/.zkv-repository')
    p = Program(repository_path)
    p.run()
