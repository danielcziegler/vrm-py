import requests
import json
import logging

LOGGER = logging.getLogger(__name__)

class VrmClientException(Exception):
    def __init__(self, message):
        self.message = message
        super(VrmClientException, self).__init__(self.message)

class VrmClient():
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.bearer = None
        self.iduser = None
        self.installations = None
        self.battery_summary = None
        # automatically authenticate if details are provided at init
        if username is not None and password is not None:
            self.authenticate()

    def authenticate(self, username=None, password=None):
        try:
            if username is not None and password is not None:
                self.username = username
                self.password = password
            if self.username is None or self.password is None:
                self.username = input("Enter your VRM Username: ")
                self.password = input("Enter your VRM Password: ")
            if self.username is None or self.username == "" or self.password is None or self.password == "":
                raise VrmClientException(f"authenticate: Username and Password are required")
            payload = {'username': self.username, 'password': self.password}
            r = requests.post("https://vrmapi.victronenergy.com/v2/auth/login",
                            data=json.dumps(payload), headers={
                                'Content-Type': 'application/json'
                            })
            LOGGER.debug(f"authenticate: Status Code for login = {str(r.status_code)}")
            if r.status_code == 200:
                auth = r.json()
                self.bearer = auth['token']
                self.idUser = auth['idUser']
            else:
                raise VrmClientException(f"authenticate: Exception authenticating - {str(r.status_code)}")
        except Exception as ex:
            raise VrmClientException(f"authenticate: Unhandled exception - {ex}")

    def check_authenticated(self):
        try:
            if self.bearer is None or self.idUser is None:
                raise VrmClientException(f"check_authenticated: Not authenticated, cannot proceed")
        except Exception as ex:
            raise VrmClientException(f"check_authenticated: Unhandled exception - {ex}")
            raise VrmClientException(f"authenticate: Unhandled exception - {ex}")

    def check_installation_data_recieved(self, auto_run=False):
        try:
            if self.installations is None:
                if auto_run:
                    self.get_installations()
                else:
                    raise VrmClientException(f"check_installation_data_recieved: No installations data present")
        except Exception as ex:
            raise VrmClientException(f"check_authenticated: Unhandled exception - {ex}")

    def _get(self, endpoint=None, expected_status=200):
        try:
            self.check_authenticated()
            if endpoint is None:
                raise VrmClientException(f"_get: Endpoint is required")
            headers = {
                'Content-Type': 'application/json',
                'X-Authorization': f"Bearer {self.bearer}"
            }
            r = requests.get(url=endpoint, headers=headers)
            if r.status_code == expected_status:
                return r.json()
            raise VrmClientException(f"_get: Got {str(r.status_code)} instead of expected {str(expected_status)} for endpoint {endpoint}")
        except Exception as ex:
            raise VrmClientException(f"_get: Unhandled exception - {ex}")

    def get_installations(self):
        try:
            self.check_authenticated()
            # endpoint = f"https://vrmapi.victronenergy.com/v2/users/{self.idUser}/installations"
            endpoint = f"https://vrmapi.victronenergy.com/v2/users/{self.idUser}/installations?extended=1"
            response = self._get(endpoint=endpoint)
            if response['success']:
                self.installations = response['records']
                return self.installations
            raise VrmClientException(f"get_installations: Did not sucessfully get installations")
        except Exception as ex:
            raise VrmClientException(f"get_installations: Unhandled exception - {ex}")

    def summary(self):
        self.check_authenticated()
        self.check_installation_data_recieved(auto_run=True)
        output = []
        for installation in self.installations:
            lat = None
            long = None
            system_status = None
            battery_percent = None
            battery_voltage = None
            battery_current = None
            battery_state = None
            for extended in installation['extended']:
                if extended['code'] == "lt":
                    lat = extended['rawValue']
                if extended['code'] == "lg":
                    long = extended['rawValue']
                if extended['code'] == "S":
                    system_status = extended['formattedValue']
                if extended['code'] == "bv":
                    battery_voltage = extended['formattedValue']
                if extended['code'] == "bs":
                    battery_percent = extended['formattedValue']
                if extended['code'] == "bc":
                    battery_current = extended['formattedValue']
                if extended['code'] == "bst":
                    battery_current = extended['formattedValue']
            temp = {
                "name": installation['name'],
                "id": installation['idSite'],
                "local_datetime": installation['current_time'], 
                "timezone": installation['timezone'], 
                "status": system_status, 
                "battery_state": battery_state, 
                "battery_percent": battery_percent, 
                "battery_voltage": battery_voltage, 
                "battery_current": battery_current, 
                "latitude": lat, 
                "longitude": long, 
            }
            return json.dumps(temp, indent=4)
        