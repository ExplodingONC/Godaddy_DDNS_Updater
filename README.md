# DDNS Updater for Cloudflare / Godaddy DNS

Monitors local IP address changes (both IPv4 and IPV6), and updates them to Cloudflare (recommended) / Godaddy (if you are rich enough to use their paid API).

I don't like it when Godaddy just starts charging money for their basic API service with absolutely no pre-warning. So I don't recommend it to anyone. 😠

The whole structure is re-written to support both Cloudflare and Godaddy DNS, and improve (hopefully) the config process at the same time.

Written for **Debian / Ubuntu** systems.  
Some tinkering is likely needed for this to work on other Linux distributions.

## Usage

1. Register your domain and API keys or tokens at Cloudflare / Godaddy (refer to their sites for details).

2. Clone this repository to local.

3. Install requirements according to `requirements.txt`.  
If you intend to run it as a systemd service, you might need to use `sudo pip install ...`, or dig around with your specific python environment setup.

    1. You might need to install `python3-dev` and  `libsystemd-dev` with the following command, for `cysystemd` to work.
        
        ```
        sudo apt-get install python3-dev
        sudo apt-get install libsystemd-dev
        ```

    2. You can also ignore `cysystemd` if you don't need to keep its log in systemd journald. Just comment out these lines in `logger.py` accordingly.

        ```
        # from systemd import journal
        ...
        # journal_handler = journal.JournalHandler()
        # journal_handler.setFormatter(formatter)
        # DDNS_logger.addHandler(journal_handler)
        ```

4. Modify file `configs sample.py` under the root directory, and `router_cfg sample.py` under `local_utils` of this repository. Instructions are included in the files.

    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Never share them with other people!** Or you might get hacked / lose your domain forever!

5. You can goofing / digging around to change other things, like if you do not use an Asus router and want to implement something else, or remove this function which gets IP info from the router.

6. Run `ddns_updater.py` to test it out.

    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Note that only public IP address will be updated.

7. If things are going fine for you, register this script as a systemd service.

    1. Create a file named `/etc/systemd/system/ddns-updater.service`

    2. Edit the file as below, with your own username and path:
        ```
        [Unit]
        Description=DDNS updater for Godaddy DNS
        After=network.target
        # Or after your proxy service if you are using one
        StartLimitBurst=5
        StartLimitIntervalSec=30

        [Service]
        Type=simple
        Restart=on-failure
        RestartSec=5
        User=<your user name>
        ExecStart=/bin/python3 /home/<user>/services/ddns_updater/ddns_updater.py

        [Install]
        WantedBy=multi-user.target
        ```

    3. Register and start your service.
        ```
        sudo systemctl daemon-reload
        sudo systemctl start ddns-updater.service
        ```
        
    4. Optionally get it to start on boot:
        ```
        sudo systemctl enable ddns-updater.service
        ```

8. Et Voila!
