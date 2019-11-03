import adal
import datetime
import random
import requests
import sys
import time
from twilio.rest import Client as TwilioClient

from zkvgateway import app, db, limiter
from .models import KeyRequest
from flask import redirect, render_template, jsonify, request

@app.route('/incoming-message', methods=['POST'])
@limiter.limit("1 per second")
def incoming_message():
  """
  Handle and incoming SMS from Twilio.
  """
  # Cleanup old approvals
  expire_date = datetime.datetime.now() - datetime.timedelta(days=7)
  db.session.query(KeyRequest).filter(KeyRequest.created_at < expire_date).delete()

  pin = request.values.get('Body', None)
  if not pin:
    return '', 400
  kr = db.session.query(KeyRequest).filter(KeyRequest.pin == pin).first()
  if kr:
    kr.approved = True
    kr.approved_at = datetime.datetime.utcnow()
    db.session.add(kr)
    db.session.commit()
    return '', 204
  else:
    return '', 404

@app.route('/request-keys')
@limiter.limit("1 per second")
def request_keys():
  """
  Obtain approval to release repository encryption key from Key Vault via SMS
  """
  pin = random.randint(0, 10**app.config['PIN_LENGTH'] - 1)
  kr = KeyRequest(pin=pin, approved=False)
  db.session.add(kr)
  db.session.commit()

  client = TwilioClient(app.config['TWILIO_ACCOUNT_ID'], app.config['TWILIO_TOKEN'])
  sms = client.messages.create(to=app.config['SMS_TO'], from_=app.config['SMS_FROM'], body="Request received for repository encryption key, respond with this PIN to confirm: %s" % str(pin).zfill(app.config['PIN_LENGTH']))

  iteration = 0
  while not kr.approved and iteration < app.config['MAX_WAIT']:
    iteration += 1
    db.session.refresh(kr)
    time.sleep(1)

  if not kr.approved:
    return '', 401

  authority_url = "%(host)s/%(tenant)s" % {'host': app.config["AAD_AUTHORITY_HOST_URI"], 'tenant': app.config['AAD_TENANT_ID']}
  context = adal.AuthenticationContext(authority_url, validate_authority=app.config['AAD_TENANT_ID'] != 'adfs', api_version=None)
  token = context.acquire_token_with_client_credentials(app.config['AAD_RESOURCE'], app.config['AAD_CLIENT_ID'], app.config['AAD_CLIENT_SECRET'])

  uri = "%(kv_uri)s/secrets/%(secret_name)s?api-version=2016-10-01" % {'kv_uri': app.config['KEY_VAULT_URI'], 'secret_name': app.config['KEY_VAULT_SECRET']}
  headers = {
    'Authorization': '%s %s' % (token['tokenType'], token['accessToken'])
  }
  r = requests.get(uri, headers=headers)
  if r.status_code == 200:
    result = r.json()
    encryption_key = result['value']
    return encryption_key

  sys.stderr.write("Error: Failed to obtain blob key due to invalid HTTP response %(status_code)d\n" % {'status_code': r.status_code})
  return '', 500
