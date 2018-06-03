zfs-keyvault
======
A tool for securely and automatically unlocking [ZFS on Linux](http://zfsonlinux.org/) encrypted filesystems using [Azure Key Vault](https://azure.microsoft.com/en-us/services/key-vault/).

## How does it work?
In short, it's the `network-online.target` equivalent for ZFS encrypted filesystems:

1. ZFS filesystem encryption keys are placed into a locally encrypted key repository, whose own encryption key is placed in Azure Key Vault.
2. Upon boot, a system service reaches out to a small Flask web application called the ZFS key gateway with a request for the repository encryption keys.
3. The ZFS key gateway web service acquires authorization from a human to release the key repository's encryption key stored in Key Vault via Twilio SMS. If the owner authorizes the request by replying to the SMS, keys are retrieved from Key Vault and sent back.

The system can now decrypt the local repository and mount the encrypted ZFS filesystems, without the filesystem encryption keys ever leaving the device.

## Features
- Mounts ZFS encrypted filesystems without the filesystem keys leaving the device
- Notifies owner via SMS for approval of any key requests
- Leverages Azure Key Vault for secure storage of the repository encryption key
- CLI tool to facilitate management of the secure local repository containing filesystem encryption keys
- Passes keys to ZFS securely via pexpect (stdin)
- Gateway limits key requests to one per second to avoid brute-forcing of request PIN

## Setup
### Azure AD application registration
We will setup an Azure AD application to credential the gateway service (Flask server) that will talk to Key Vault and release the key repository's encryption key down to your server:
1. Navigate to [portal.azure.com](https://portal.azure.com)
2. Open the *Azure Active Directory > App Registration* blade
3. Register a new *Web Application and/or Web API* type application (use `appname.yourtenant.onmicrosoft.com` as the URL if you do not have a valid domain associated to the account). Note the displayed Application ID for use later.
4. Navigate to the app's *Settings > Keys* blade and create a new key. After saving, note down the key (aka client secret) for use later.
5. Back out to the *Azure Active Directory > Properties* and note the Tenant ID for later.
5. Create a new Key Vault resource and open its *Access Policies* blade
6. Under *Select principal*, select your newly created application from step 3 and under *Secret Permissions* select *Get*, then press *OK*

### Installation of the client (systemd service)
1. Install the systemd service:
    ```
    cp {,/}etc/systemd/system/zfs-keyvault.service
    cp {,/}etc/sysconfig/zfs-keyvault
    systemctl daemon-reload
    systemctl enable zfs-keyvault
    ```
2. Copy zkv utility:
    ```
    cp zkv.py /usr/local/bin/zkv
    chmod +x /usr/local/bin/zkv
    ```
3. Ensure the dependencies in `client/requirements.txt` are available in system python. Ideally, you would do so via your OS package manager. As a last resort, run `pip -r client/requirements.txt` as root.
4. Modify `/etc/sysconfig/zfs-keyvault` to point the correct gateway URL setup in step 3 of the server above *(if you don't know this yet, skip this and return to this step after finishing the server installation)*.

### Key repository
1. Create a filesystem key repository on your local system:
    ```
    zkv fs init
    ```
    Note the encryption key for subsequent steps as it cannot be retrieved later.
2. Add one or more filesystems:
    ```
    zkv fs add -k 'key_from_step_1' pool1/encfsname1 'zfs_enc_key'
    zkv fs add -k 'key_from_step_1' pool1/encfsname2 'zfs_enc_key'
    zkv fs add -k 'key_from_step_1' pool2/other_encfs 'zfs_enc_key'
    ...
    ```
3. Upload the key from step 1 as a secret to Key Vault, taking note of the name you used for use later.

### Installation of the server (ZFS Key Gateway)
1. Pull the docker image:
    ```
    docker pull stewartadam/zkvgateway
    ```
2. Run the image in your favorite environment (e.g. [App Service for Linux with Containers](https://docs.microsoft.com/en-us/azure/app-service/containers/tutorial-custom-docker-image))
    * If you skipped configuration of the public URL during the client, do so now.
    * Your container needs information about your Azure AD application and Twilio account passed to it. The easiest way is to override config values at runtime with environment variables:

        ```
        ZKV_SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/db.sqlite'
        ZKV_AAD_CLIENT_ID = 'guid-here'
        ZKV_AAD_CLIENT_SECRET = 'secret-here'
        ZKV_AAD_TENANT_ID = 'guid-here'
        ZKV_KEY_VAULT_URI = 'https://YOUR_KV_NAME.vault.azure.net'
        ZKV_KEY_VAULT_SECRET = 'KV_SECRET_NAME'
        ZKV_TWILIO_ACCOUNT_ID = 'id-here'
        ZKV_TWILIO_TOKEN = 'token-here'
        ZKV_SMS_TO = '+15551234567'
        ZKV_SMS_FROM = '+15551234567'
        ```

        Any of the other Flask parameters (e.g. look at `server/zkvgateway/config.py`) can also be overridden by passing the config keys prefixed by `ZKV_`.

        Alternatively, you can map a volume with a config file in it, and then pass a `CONFIG_FILE` environment variable pointing to the location of the configuration file inside the container. The configuration keys written in the config file should match those in `config.py`, i.e. as above *less* the `ZKV_` prefix.

### Twilio
Twilio is used to approve key requests over SMS.
1. Create an account at [twilio.com](https://www.twilio.com/)
2. [Add a phone number](https://www.twilio.com/console/phone-numbers/search) to your account
3. [Configure a messaging webhook](https://support.twilio.com/hc/en-us/articles/223135027-Configuring-phone-numbers-to-receive-calls-or-SMS-messages) for your number with endpoint  `https://YOUR_GATEWAY_HOSTNAME.TLD/incoming-message`

## Todo
I'm not committed to any of these at this time, but ideas for improvement (or PRs):
* Implement one-time password mechanism instead of random PIN
* Consider additional security protections (e.g. dead-man switch, remote wipe, key rotation)
* Generalize pattern for other encryption providers (e.g. LUKS or dm-crypt)

## Known issues
* SMS is insecure
