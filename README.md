zfs-keyvault
======
A tool for securely and automatically unlocking [ZFS on Linux](http://zfsonlinux.org/) encrypted filesystems using [Azure Key Vault](https://azure.microsoft.com/en-us/services/key-vault/).

## How does it work?
In short, it's the `network-online.target` equivalent for ZFS encrypted filesystems:

1. ZFS filesystem encryption keys are placed into a local encrypted key repository, whose single encryption key is placed in Azure Key Vault.
2. Upon boot, a system service reaches out to a small Flask web application with a request for the encryption keys
3. The web service aquires authorization to release the repository encryption key stored in Key Vault via Twilio SMS. If the owner authorizes the request by replying to the SMS, keys are retrieved from Key Vault and sent back.

The system can now decrypt the local repository and mount the encrypted ZFS filesystems, without the filesystem encryption keys ever leaving the device.

## Features
- Mounts ZFS encrypted filesystems without the filesystem keys leaving the device
- Notifies owner via SMS for approval of any key requests
- Leverages Azure Key Vault for secure storage of the repository encryption key
- CLI tool to facilitate management of the secure local repository containing filesystem encryption keys
- Passes keys to ZFS via stdin

## Installation
Run as root:
```
python setup.py install
systemctl daemon-reload
systemctl enable zfs-keyvault
```
TODO: Write setup.py

## Configuration
1. Navigate to [portal.azure.com](https://portal.azure.com)
2. Open the *Azure Active Directory > App Registration* blade
3. Register a new *Web Application and/or Web API* type application (use `appname.yourtenant.onmicrosoft.com` as the URL if you do not have a valid domain associated to the account)
4. Copy your registered application's App ID and the AAD tenant ID into the `/etc/sysconfig/zfs-keyvault`
5. Create a new Key Vault and open its *Access Policies* blade
6. Under *Select principal*, select your newly created application and under *Secret Permissions* select *Get*, then press *OK*

TOOD: show app config