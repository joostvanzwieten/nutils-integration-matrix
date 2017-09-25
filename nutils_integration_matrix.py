# Copyright (c) 2017 Evalf
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__version__ = '1.dev0'

import os, pathlib, urllib.request, urllib.parse, urllib.error, html, json, hmac, hashlib

def _matrix_request(*url_parts, home_server, method, access_token=None, query=None, body=None):
  url_parts = '_matrix', 'client', 'r0', *url_parts
  query = dict(query or {})
  if access_token is not None:
    query['access_token'] = access_token
  url = urllib.parse.urlunsplit(('https', home_server, '/'+'/'.join(map(urllib.parse.quote_plus, url_parts)), urllib.parse.urlencode(query), ''))
  # Create request.
  headers = {}
  if body:
    headers['Content-Type'] = 'application/json; charset=utf-8'
    data = json.dumps(body).encode()
  else:
    data = None
  request = urllib.request.Request(url, method=method, data=data, headers=headers)
  # Send request and process response.
  try:
    with urllib.request.urlopen(request) as response:
      return json.loads(response.read().decode())
  except urllib.error.HTTPError as error:
    if error.headers.get('Content-Type', None).lower().split(';', 1)[0] in {'application/json', 'text/json'}:
      body = json.loads(error.read().decode())
      raise MatrixError(body['errcode'], body['error']) from error
    else:
      raise

class MatrixError(Exception):

  def __init__(self, code, msg):
    self.code = code
    self.msg = msg
    super().__init__()

  def __str__(self):
    return self.msg

class InvalidRoomId(Exception):
  pass

def _get_config_path():
  if 'XDG_CONFIG_HOME' in os.environ:
    config_path = pathlib.Path(os.environ['XDG_CONFIG_HOME'])
  else:
    config_path = pathlib.Path.home() / '.config'
  return config_path / 'nutils-integration-matrix'

def _get_account():
  with (_get_config_path() / 'account.json').open() as f:
    return json.load(f)

def _get_room():
  with (_get_config_path() / 'room').open() as f:
    return f.read().strip()

def _write_account(account):
  config_path = _get_config_path()
  config_path.mkdir(parents=True, exist_ok=True)
  account_path = config_path / 'account.json'
  if not account_path.exists():
    account_path.touch(mode=0o600)
  with account_path.open('w') as f:
    return json.dump(account, f)

def _write_room(room):
  config_path = _get_config_path()
  config_path.mkdir(parents=True, exist_ok=True)
  with (config_path / 'room').open('w') as f:
    f.write(room)

def nutils_send_status(scriptname, log_url, status):
  account = _get_account()
  room = _get_room()
  if log_url:
    msg = '[{}]({}) {}'.format(scriptname, log_url, status)
    formatted_msg = '<a href="{}">{}</a> {}'.format(log_url, html.escape(scriptname), html.escape(status))
  else:
    msg = '{} {}'.format(scriptname, status)
    formatted_msg = '{} {}'.format(html.escape(scriptname), html.escape(status))
  body = dict(msgtype='m.text', body=msg, formatted_body=formatted_msg, format='org.matrix.custom.html')
  _matrix_request('rooms', room, 'send', 'm.room.message', method='POST', home_server=account['home_server'], access_token=account['access_token'], body=body)

def clear_config():
  config_path = _get_config_path()
  for f in 'account.json', 'room':
    if (config_path / f).exists():
      (config_path / f).remove()

def login(home_server, user, password):
  _write_account(_matrix_request('login', body=dict(type='m.login.password', user=user, password=password), method='POST', home_server=home_server))

def register(home_server, username, shared_secret):
  mac = hmac.new(key=shared_secret, digestmod=hashlib.sha1, msg=username.encode()).hexdigest()
  account = cls._full_request('register', mac=mac, username=username, home_server=home_server)
  _write_account(account)
  return account['user_id']

def set_room(room):
  if not room.startswith('!'):
    raise InvalidRoomId(room)
  account = _get_account()
  sync = _matrix_request('sync', method='GET', home_server=account['home_server'], access_token=account['access_token'])
  if room not in sync['rooms']['join']:
    _matrix_request('rooms', room, 'join', method='POST', home_server=account['home_server'], access_token=account['access_token'])
  _write_room(room)
  return room

def create_room(name='nutils notifications', preset='private_chat'):
  account = _get_account()
  body = {}
  if name is not None:
    body['name'] = name
  if preset is not None:
    body['preset'] = preset
  room = _matrix_request('createRoom', body=body, method='POST', home_server=account['home_server'], access_token=account['access_token'])['room_id']
  _write_room(room)
  return room

def invite(user):
  account = _get_account()
  room = _get_room()
  _matrix_request('rooms', room, 'invite', body=dict(user_id=user), method='POST', home_server=account['home_server'], access_token=account['access_token'])
  # Set power level of `user` to `100`.
  power_levels = _matrix_request('rooms', room, 'state', 'm.room.power_levels', method='GET', home_server=account['home_server'], access_token=account['access_token'])
  power_levels['users'][user] = 100
  _matrix_request('rooms', room, 'state', 'm.room.power_levels', body=power_levels, method='PUT', home_server=account['home_server'], access_token=account['access_token'])

def kick(user):
  account = _get_account()
  room = _get_room()
  _matrix_request('rooms', room, 'kick', body=dict(user_id=user), method='POST', home_server=account['home_server'], access_token=account['access_token'])

if __name__ == '__main__':
  import argparse, getpass, sys

  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(dest='cmd')

  parer_clear_config = subparsers.add_parser('clear-config')

  parser_status = subparsers.add_parser('status')

  parser_login = subparsers.add_parser('login')
  parser_login.add_argument('user_id', metavar='@<username>:<homeserver>')

  parser_register = subparsers.add_parser('register')
  parser_register.add_argument('user_id', metavar='@<username>:<homeserver>')

  parser_set_room = subparsers.add_parser('set-room')
  parser_set_room.add_argument('room', metavar='<room>')

  parser_create_room = subparsers.add_parser('create-room')
  parser_create_room.add_argument('--name', nargs=1, metavar='<name>')
  parser_create_room.add_argument('--preset', nargs=1, metavar='<preset>')
  parser_create_room.set_defaults(name='nutils notifications', preset='private_chat')

  parser_invite = subparsers.add_parser('invite')
  parser_invite.add_argument('user_id', metavar='@<username>:<homeserver>')

  parser_kick = subparsers.add_parser('kick')
  parser_kick.add_argument('user_id', metavar='@<username>:<homeserver>')

  ns = parser.parse_args()
  if ns.cmd == None:
    parser.print_usage()
    raise SystemExit

  try:
    if ns.cmd == 'clear-config':
      clear_config()
    elif ns.cmd == 'status':
      account_path = _get_config_path() / 'account.json'
      if account_path.exists():
        account = _get_account()
        print('account: {user_id}'.format(**account))
      else:
        account = None
        print('account: not logged in')
      room_path = _get_config_path() / 'room'
      if room_path.exists():
        room = _get_room()
        print('room: {}'.format(room))
      else:
        print('room: no room set')
      import nutils.core
      enabled = 'matrix' in (nutils.core.getprop('send_status_integrations', None) or ())
      print('nutils matrix integration: {}'.format({True: 'enabled', False: 'disabled'}[enabled]))
    elif ns.cmd == 'login':
      if not ns.user_id.startswith('@') or ':' not in ns.user_id:
        print("ERROR: {!r} is not a valid user id (should be '@username:homeserver', e.g. '@alice:example.com')", file=sys.stderr)
      user, home_server = ns.user_id[1:].split(':', 1)
      login(home_server=home_server, user=user, password=getpass.getpass())
    elif ns.cmd == 'register':
      if not ns.user_id.startswith('@') or ':' not in ns.user_id:
        print("ERROR: {!r} is not a valid user id (should be '@username:homeserver', e.g. '@alice:example.com')", file=sys.stderr)
      user, home_server = ns.user_id[1:].split(':', 1)
      register(home_server=home_server, user=user, shared_secret=getpass.getpass('Shared secret for {}: '.format(home_server)).encode())
    elif ns.cmd == 'set-room':
      set_room(ns.room)
    elif ns.cmd == 'create-room':
      create_room(name=ns.name, preset=ns.preset)
    elif ns.cmd == 'invite':
      invite(ns.user_id)
    elif ns.cmd == 'kick':
      kick(ns.user)
  except (MatrixError, InvalidRoomId) as e:
    print('ERROR: {}'.format(e), file=sys.stderr)
    raise SystemExit(1)
  except OSError as e:
    print('ERROR: {}'.format(e), file=sys.stderr)
    raise SystemExit(1)

  account_path = _get_config_path() / 'account.json'
  if account_path.exists() and account_path.stat().st_mode & 0o077:
    print('WARNING: {} is group or world accessible'.format(account_path), file=sys.stderr)

# vim: sts=2:sw=2:et
