__author__ = "Septima"
__date__ = "2019-12-02"
__copyright__ = "(C) 2019 by Septima"

import os
import json
import getpass
from pathlib import Path


class Settings:
    def __init__(self):
        RC_NAME = "fire_settings.json"

        if os.environ.get("HOME"):
            home = Path(os.environ["HOME"])
        else:
            home = Path("")

        self.search_files = [
            home / Path(RC_NAME),
            home / Path("." + RC_NAME),
            Path("/etc") / Path(RC_NAME),
            Path("C:\\Users") / Path(getpass.getuser()) / Path(RC_NAME),
            Path("C:\\Users\\Default\\AppData\\Local\\fire") / Path(RC_NAME),
        ]

    def value(self, setting):
        # This class mimics qgissettingmanager api
        if setting == "fire_connection_string":
            return self.get_fire_connection_string()
        elif setting == "fire_connection_file_path":
            return self.get_fire_connection_file_path()
        else:
            return None

    def get_fire_connection_file_path(self):
        # Find settings file and read database credentials
        for conf_file in self.search_files:
            if os.path.isfile(conf_file):
                return str(conf_file)
        return None

    def get_fire_connection_string(self):
        # Conf file is read at every call. This gives the user the ability to correct the file without reloading the plugin

        for conf_file in self.search_files:
            if os.path.isfile(conf_file):
                with open(conf_file) as conf:
                    settings = json.load(conf)
                    if "connection" in settings:
                        conf_db = settings["connection"]
                        if not (
                            "username" in conf_db
                            and "password" in conf_db
                            and "hostname" in conf_db
                            and "database" in conf_db
                            and "service" in conf_db
                        ):
                            return None
                break
        else:
            return None

        # Establish connection string to database
        _username = conf_db["username"]
        _password = conf_db["password"]
        _hostname = conf_db["hostname"]
        _database = conf_db["database"]
        _service = conf_db["service"]
        if "port" in conf_db:
            _port = conf_db["port"]
        else:
            _port = 1521

        return f"{_username}:{_password}@{_hostname}:{_port}/{_database}"

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)
