import logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',filename="iselog.log", encoding='utf-8', level=logging.DEBUG)
import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
import json
import os
from os import path
import base64
from dotenv import load_dotenv
import time
import shutil
import tranz as tz



execution_path = os.getcwd()
load_dotenv(path.join(execution_path, '.env'))

VERIFY_HTTPS = os.getenv("VERIFY_HTTPS")
    
if not VERIFY_HTTPS:
    disable_warnings(InsecureRequestWarning)

console = logging.StreamHandler()
console.setLevel(logging.INFO)

# Hinzufügen des Handlers zum Root-Logger
logging.getLogger().addHandler(console)
logging.info("\nParameters:")

class ISE(object):
    def __init__(self):
        self.ise_user = os.getenv('USER')
        self.ise_pass = os.getenv('PASSWD')
        self.protocol = os.getenv('PROTOCOL')
        self.ise_node = os.getenv("ISENODE")
        self.foldername = os.getenv("FOLDERNAME")
        self.destfolder = os.getenv("DESTFOLDER")
        self.read_back_log = os.getenv("BACKLOG")
        self.url_base = "{0}://{1}:9060/ers/config/endpoint".format(self.protocol, self.ise_node)

        app_path = os.getcwd()
        self.destpath = path.join(app_path, self.destfolder)
        self.isdir = os.path.isdir(self.destpath)

        userpass = self.ise_user + ':' + self.ise_pass
        self.encoded_userpass = base64.b64encode(userpass.encode()).decode()


    def request(self,method="GET", payload={}, extrapath=""):
        try:
            url = self.url_base + extrapath
            headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'ERS-Media-Type': 'identity.endpoint.1.2',
            'Authorization': 'Basic ' + self.encoded_userpass,
            }
            response = requests.request(method, url, headers=headers, verify = False, data=payload)
            return { "status":response.status_code, "text": response.text}
        except Exception as ex:
            print(str(ex))
            logging.exception(str(ex))

    '''
    prüft, ob der als Parameter übergebene Wert ein bestimmtes Kriterium erfüllt, 
    Ist dies der Fall, wird der Wert durch eine bestimmte Variable ersetzt.
    '''
    def validate_value(value):
        if value == "-" or value == "." or value == "_" or value == "'" or value == ":" or value == "*" or value == "!" or value == "&" or value == "=":
            new_value = "Unbekannt"
            return new_value


    def get_all_endpoints(self):
        """"
        Ruft alle verfügbaren Endpunkte ab 
        und speichert die Mac-Adressen 
        und IDs in einem Array von Objekten, 
        das als Variable zurückgegeben wird.
        """
        try:
            mac_address_bank = []
            response = ISE.request(self)
            if response["status"] == 200:
                response = json.loads(response["text"])
                resources = response["SearchResult"]["resources"]
                if len(resources) > 0:
                    for obj in resources:
                        mac_address_bank.append({ "mac": obj["name"], "id": obj["id"]})
                    logging.info("Endpoint found. Array with Mac and Id returned")
                    return mac_address_bank
                else:
                    logging.info("No Endpoint found. Returned empty array")
                    return mac_address_bank
        except Exception as ex:
            print("[INFO] Exception Detected: " + str(ex))
            logging.exception(str(ex))


    def read_logs(self, available_endpoints, data):
        """"
        nimmt die verfügbaren Endpunkte in der ISE als Parameter 
        und auch jedes einzelne Objekt innerhalb des json. 
        Diese Werte werden verglichen und auf der Grundlage des 
        Ergebnisses wird ein Aktualisierungs- oder Erstellungsvorgang durchgeführt
        """

        for i in data:
            update_counter = 0
            json_data = {
                "ERSEndPoint": {
                    "mac": i["macadresse"],
                    "customAttributes": {
                        "customAttributes": {
                            "admingruppe": ISE.validate_value(i.get("admingruppe","")),
                            "adresse": ISE.validate_value(i.get("adresse","")),
                            "betriebsmodell": ISE.validate_value(i.get("betriebsmodell","")),
                            "computername": ISE.validate_value(i.get("computername","")),
                            "erstellt": ISE.validate_value(i.get("erstellt","")),
                            "feldgruppe": ISE.validate_value(i.get("feldgruppe","")),
                            "geaendert": ISE.validate_value(i.get("geaendert","")),
                            "komponentenklasse": ISE.validate_value(i.get("komponentenklasse","")),
                            "komponentennr": ISE.validate_value(i.get("komponentennr","")),
                            "komponententyp": ISE.validate_value(i.get("komponententyp","")),
                            "komponentestatus": ISE.validate_value(i.get("komponentestatus","")),
                            "kunde": ISE.validate_value(i.get("kunde","")),
                            "orgeinheit_beschreibung": ISE.validate_value(i.get("orgeinheit_beschreibung","")),
                            "orgeinheit_nr": ISE.validate_value(i.get("orgeinheit_nr","")),
                            "raum": ISE.validate_value(i.get("raum", "")),
                            "raumadresse": ISE.validate_value(i.get("raumadresse","")),
                            "seriennr": ISE.validate_value(i.get("seriennr","")),
                            "systemart": ISE.validate_value(i.get("systemart","")),
                            "systemklasse": ISE.validate_value(i.get("systemklasse","")),
                            "systemname": ISE.validate_value(i.get("systemname","")),
                            "systemnr": ISE.validate_value(i.get("systemnr","")),
                            "systemstatus": ISE.validate_value(i.get("systemstatus",""))
                        }
                    }
                }
            }
            try:
                if len(available_endpoints) > 0:
                    for x in available_endpoints:
                        if x["mac"] == i["macadresse"]:
                            single_object = json.dumps(json_data)
                            single_object = single_object.replace("'","")
                            extra_path = "/" + x["id"]
                            response = ISE.request(self,"PUT", single_object, extra_path)
                            update_counter = 1
                            if response["status"] == 200:
                                if response["text"] == "" or response["text"] == None:
                                    logging.debug("Status code: " + str(response["status"]) + " for " + str(i["macadresse"]))
                                else:
                                    logging.debug("Status code: " + str(response["status"]) + " and Response_text: " + str(response["text"]) + " for " + str(i["macadresse"]))
                            else:
                                if response["text"] == "" or response["text"] == None:
                                    logging.error("Status code: " + str(response["status"]) + " for " + str(i["macadresse"]))
                                else:
                                    logging.error("Status code: " + str(response["status"]) + " and Response_text: " + str(response["text"]) + " for " + str(i["macadresse"]))
                            break
                            
                    
                if update_counter == 0:
                    single_object = json.dumps(json_data)
                    single_object = single_object.replace("'","")
                    response = ISE.request(self,"POST", single_object)
                    if response["status"] == 201:
                        if response["text"] == "" or response["text"] == None:
                            logging.debug("Status code: " + str(response["status"]) + " for " + str(i["macadresse"]))
                        else:
                            logging.debug("Status code: " + str(response["status"]) + " and Response_text: " + str(response["text"]) + " for " + str(i["macadresse"]))

                    else:
                        if response["text"] == "" or response["text"] == None:
                            logging.error("Status code: " + str(response["status"]) + " for " + str(i["macadresse"]))
                        else:
                            logging.error("Status code: " + str(response["status"]) + " and Response_text: " + str(response["text"]) + " for " + str(i["macadresse"]))
                continue
            except Exception as ex:
                print(print("[INFO] Exception Detected: " + str(ex)))
                logging.exception(str(ex))
                continue
            


    def main(self):
        """"
        Wenn die Variable BACKLOG auf True gesetzt ist, 
        werden alle Dateien im Transaktionsordner gelesen und ihre Werte als Endpunkte exportiert. 
        Wenn die Variable BACKLOG jedoch auf False gesetzt ist, 
        werden nur die aktuellen Daten des Tages mit der Funktion load_cache gelesen.
        """
        try:
            available_endpoints = ISE.get_all_endpoints(self)
            
            if self.read_back_log == "true" or self.read_back_log == "True":
                if self.isdir == False:
                    os.mkdir(self.destpath)
                logging.info("Reading backlogs....")
                foldername = self.foldername
                for filename in os.listdir(foldername):
                    if filename.endswith(".json"): 
                        filepath = path.join(foldername, filename)
                        f = open(filepath)

                        data = json.load(f)
                        ISE.read_back_logs(self,available_endpoints, data)
                        f.close()
                    shutil.move(filepath, self.destfolder)
            else:
                logging.info("Reading recent data....")
                obj = tz.load_cache()
                ISE.read_logs(self,available_endpoints, obj)

        except Exception as ex:
            logging.exception(str(ex))


if __name__ == '__main__':
    start_time = time.time()
    ISE().main()
    logging.info("This programm took {}".format(str(time.time() - start_time)) + " seconds to execute")
