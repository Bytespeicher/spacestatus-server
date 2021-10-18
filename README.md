# Spacestatus Server
Flask/Connexion based web application providing a hackspace status website and JSON frontend for [spaceAPI](http://spaceapi.net).

## Plugins (to post status change)
* Twitter
* Matrix

## Known limitations
* Application not usable in multiprocess environment
(gunicorn will work in threading mode)

## Provided endpoints
### GET
| Endpoint | Description |
| --- | --- |
| **/** | rendered template from templates/home.html |
| **/status.json** | Hackspace API JSON file |
| **/status-minimal.json** | JSON file with state and state icon |
| **/static/{images,js,css}/{filename}** | Files from static folder |

### PUT
<table>
  <tr>
    <th>Endpoint</th>
    <th>Description</th>
    <th>Example</th>
  </tr>
  <tr>
    <td><b>/api/v1/status</b></td>
    <td>Set status<br /><br />Temperature Sensor could also be added.</td>
    <td>
      <pre>{
  "sensors": {
    "people_now_present": [{
      "value": 0,
      "names": []
    }]
  },
  "state": {
    "open": false,
    "lastchange": 1612387891,
    "message": "No devices connected"
  }
}</pre>
    </td>
  </tr>
  <tr>
    <td><b>/api/v1/sensors/temperature</b></td>
    <td>Set temperature sensors</td>
    <td>
      <pre>{
  "sensors": {
    "temperature": [
      { "value": 12.81, "unit": "°C", "location": "Hackspace" },
      { "value": -6.44, "unit": "°C", "location": "Outside" }
    ]
  }
}</pre>
    </td>
  </tr>
</table>

## Dependencies
### System (Debian-related)
* git
* python3 (>=3.7)
* python3-venv

### Python modules
* see [requirements.txt](requirements.txt)
* wheel

## Installation

You should install this application using a dedicated user.

After your installation spacestatus-server serves on port 5000 on all interfaces. Configure your preferred http proxy (apache, nginx, traefik, ...) to allow access via http/https.

### System requirements on Debian

1. Install system requirements
    ```shell
    sudo apt-get update
    sudo apt-get install python3-venv git
    ```

2. Create spacestatus user
    ```shell
    sudo useradd --comment "Spacestatus" --create-home  --user-group spacestatus
    ```

### Spacestatus server

1. Change to spacestatus user
    ```shell
    sudo su - spacestatus
    ```

2. Clone repository
    ```shell
    git clone https://github.com/Bytespeicher/spacestatus-server
    ```
3. Initialize virtual environment
    ```shell
    python3 -m venv virtualenv3
    ```
4. Install python requirements in virtual environment
    ```shell
    . virtualenv3/bin/activate
    pip3 install wheel
    pip3 install -r spacestatus-server/requirements.txt
    pip3 install gunicorn
    deactivate
    ```
5. Copy example configuration files
    ```shell
    cd ~/spacestatus-server
    cp config/config.example.yaml config/config.yaml
    cp config/apidata/status.example.org.json config/apidata/status.your-domain.org.json
    ```

6. Adjust configuration file config/config.yaml

8. Adjust space api json file config/apidata/status.your-domain.org.json

### Install systemd unit

1. Copy systemd unit file
    ```shell
    sudo cp /home/spacestatus/spacestatus-server/contrib/spacestatus-server.service /etc/systemd/system/spacestatus-server.service
    ```

2. Adapt /etc/systemd/system/spacestatus-server.service if service should not listen on all interfaces

3. Reload systemd daemon to reload unit file and start and enable service
    ```shell
    sudo systemctl daemon-reload
    sudo systemctl enable spacestatus-server.service --now
    ```
## Update

### Spacestatus server

1. Change to spacestatus user
    ```shell
    sudo su - spacestatus
    ```

2. Update repository
    ```shell
    cd spacestatus-server
    git pull
    ```

3. Update virtual environment
    ```shell
    cd
    python3 -m venv --upgrade virtualenv3
    ```

4. Update python requirements in virtual environment
    ```shell
    cd
    . virtualenv3/bin/activate
    pip3 install --upgrade wheel
    pip3 install --upgrade -r spacestatus-server/requirements.txt
    pip3 install --upgrade gunicorn
    deactivate
    ```

5. Adjust configuration file config/config.yaml

6. Restart systemd daemon
    ```shell
    sudo systemctl restart spacestatus-server.service
    ```
