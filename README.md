# DDNS Updater for Godaddy DNS

Monitors local IP address changes (both IPv4 and IPV6), and updates them to https://api.godaddy.com.

Written for **Debian / Ubuntu** systems.  
Some tinkering is likely needed for this to work on other Linux distributions.

## Usage

1. Register your domain and API keys at https://godaddy.com (refer to Godaddy site for details).

2. Clone this repository to local.

3. Install requirements according to `requirements.txt`.  
If you intend to run it as a systemd service, you might need to use `sudo pip install ...`.

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

4. Create a file named `configs.py` under the root directory of this repository, with contents below.  

    **Never share it with other people!** Or you might lost your domain forever!

    ```
    api_key = "your_api_key"
    api_secret = "your_api_secret"
    api_domain = "your.domain"
    ```

5. Edit other parameters as you need, i.e.,

    Porxy service:
    ```
    USE_PROXY = True or False  # if you need proxy
    def set_proxy(proxy: str = "socks5://your.proxy:serice"):
        ...
    ```

    Hostname list:
    ```
    www_updater = DDNSUpdater(name="your-hostname", type="CNAME")
    home_updater = DDNSUpdater(name="your-other-hostname", type="AAAA")
    ```

6. Run `ddns_updater.py` to test it out.

    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Note that only public IP address will be updated.

7. If things are going fine for you, register this script as a systemd service.

    1. Create a file named `/etc/systemd/system/ddns-updater.service`

    2. Edit the file as below, with your own username:
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
        ExecStart=/bin/python3 /home/explodingonc/services/ddns_updater/ddns_updater.py

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
