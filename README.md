zfs-keyvault
======
A small console application that uses the device OAuth2 flow with AAD to securely retrieve encryption keys from Azure Key Vault for [ZFS on Linux](http://zfsonlinux.org/).

It probably works on other supported OpenZFS platforms, but this is untested.

## How does it work?
In short, it's the `network-online.target` equivalent for ZFS encrypted filesystems:

A one-shot systemd service is run at boot to kick off the AAD device flow, and the resulting URL & auth code is sent to your mobile device.

After authentication, the service is able to talk to key vault to retreive the stored encryption keys and mount your ZFS filesystems.

You can then configure other services to depend on this service in order to ensure they start after your encrypted filesystems become available.

The service aborts after a timeout of your choice if you do not authenticate successfully.

## Features
- Securely retrieves keys from Azure Key Vault
- Passes keys to ZFS securely, either via stdin or by writing key to a file with `mktemp` that is later removed
- [WIP] SMS or e-mail notifications for authentication prompts
- [WIP] Configurable service timeouts

## Installation
Run as root:
```
mkdir /usr/share/zfs-keyvault
dotnet publish -o /usr/share/zfs-keyvault
cp {,/}etc/systemd/system/zfs-keyvault.service
cp {,/}etc/sysconfig/zfs-keyvault
systemctl daemon-reload
systemctl enable zfs-keyvault
```

## Configuration
1. Navigate to [portal.azure.com](https://portal.azure.com)
2. Open the *Azure Active Directory > App Registration* blade
3. Register a new *Native* type application (use `appname.yourtenant.onmicrosoft.com` as the URL if you do not have a valid domain associated to the account)
4. Under Required Permissions, add the *Azure Key Vault* and select all delegated permissions
5. Create a new Key Vault and grant the *Get Secret* permission to any users who you'd like to be able to retrieve ZFS encryption keys from Key Vault
6. Copy your registered application's App ID and the AAD tenant ID into the `/etc/sysconfig/zfs-keyvault`
