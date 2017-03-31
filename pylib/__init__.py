#!/usr/bin/python
# -*- coding: utf-8 -*-

# Configuration to adapt to your environment

magentoServerRoot = '/var/local/httpd/magento/'
fromEmail         = 'root@arluison.com'
defaultToEmail    = 'root@arluison.com'
environments = {
                 'server'  : 
                  {
                    '1.1.1.1'    : 'TEST',
                    'pprdata.dh' : 'PROD',
                    'undefined'  : 'undefined'
                  } ,
                 'database':
                  {
                    'localhost' : 'TEST',
                    '2.2.2.2'   : 'PROD'
                  }
  }
slackHook = [ None ]

# End of configuration

import sys
import commands
import shlex, subprocess
import re
import urllib
from contextlib import closing
from os import getcwd, system
from os.path import isfile, basename, dirname, realpath
from socket import gethostname
import time
import calendar
from datetime import date, timedelta
import pickle

ttycolors = {
  'red': '31',
  'green': '32',
  'blue': '94',
  'yellow': '33',
}

def _stdPickleFile():
  '''hidden function not to be used directly, this will return the default naming to save
  the pickle file'''
  return dirname(realpath(__file__)) + '/../../var/tmp/' + basename(sys.argv[0]) + '.pck'

def loadPck(empty = {}, fileName = None):
  '''to load persistent data at the beginning of the script'''
  if not fileName:
    fileName = _stdPickleFile()
  try:
    return pickle.load(open(fileName))
  except IOError:
    return empty

def savePck(data = {}, fileName = None):
  '''to save persistent data at the end of the script'''
  if not fileName:
    fileName = _stdPickleFile()
  pickle.dump(data, open(fileName, 'w'))

def getEnvironment():
  '''utility to get a nice naming of the environment the script is executed : PROD, TEST etc...'''
  envs = environments['server'].keys()
  host = gethostname()
  for e in envs:
    if e in host:
      return environments['server'][e]
  return environments['server']['undefined']

def str2time(t):
  ''' in : struct_time
     out : string'''
  if type(t) is time.struct_time:
    return t
  if type(t) is str:
    return time.strptime(t, "%Y-%m-%d %H:%M:%S"[0:len(t)-2])

def time2str(t):
  '''opposite of str2time 
     in : string %Y-%m-%d %H:%M:%S
    out : struct_time'''
  return time.strftime("%Y-%m-%d %H:%M:%S", t)

def local2utc(t):
  '''Make sure that the dst flag is -1 -- this tells mktime to take daylight
  savings into account'''
  secs = time.mktime(str2time(t))
  return time.gmtime(secs)

def utc2local(t):
  secs = calendar.timegm(str2time(t))
  return time.localtime(secs)

def now():
  return time.localtime()

def today(rge = 0):
  return daySlip(0, rge)

def yesterday(rge = 0):
  return daySlip(1, rge)

def daySlip(decal = 1, rge = 0):
  '''will return a SQL standard %Y-%m-%d %H:%M:%S string of a day in the past
     decal is the number of days to remove to today
     rge is either :
       0     = default, returns only one string
       'sql' = returns sql statement BETWEEN with the period between 
               the two midnights of the selected day
       1     = (or anything else) will return 2 strings without the 
               sql BETWEEN statement.
  '''
  s = (date.today() - timedelta(days = decal)).strftime('%Y-%m-%d')
  if not rge:
    return s
  s2 = (date.today() - timedelta(days = decal-1)).strftime('%Y-%m-%d')
  d1 = time2str(local2utc(s))
  d2 = time2str(local2utc(s2))
  if rge == 'sql':
    return "BETWEEN '%s' AND '%s'" % (d1,d2)
  return d1, d2

def runSubProcess(command_line, shell = False):
  c_ = command_line
  if isinstance(command_line, str) and not shell:
  	command_line = shlex.split(command_line)
  #subprocess.check_call( command_line, shell, stderr = subprocess.STDOUT )
  proc = subprocess.Popen( command_line, shell, stdout = subprocess.PIPE, stderr = subprocess.PIPE )
  proc.wait()
  out, err = proc.communicate()
  exitcode = proc.returncode
  if exitcode:
    raise subprocess.CalledProcessError(exitcode, str(c_) + '\nout =\n' + str(out) + '\nerr =\n' + str(err) )
  return exitcode, out, err
  
def runProg(cmd):
  return runSubProcess(cmd, shell = False)

def runShell(cmd):
  return runSubProcess(cmd, shell = True)

def getUrlContent(url):
  '''get content of a page or document from url'''
  with closing(urllib.urlopen(url)) as f:
    c = f.read()
  return c

def isHuman():
  '''returns True if the script is executed by a tty therefore a human'''
  return sys.stdin.isatty()

def totty(chain, color, bold = 0):
  if not sys.stdout.isatty():
    return chain
  attr = []
  if ttycolors.has_key(color):
    attr.append( ttycolors[color] )
  if bold:
    attr.append( '1' )

  return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), chain)

def color(chain, color, bold = 0):
  if sys.stdout.isatty():
    attr = []
    if ttycolors.has_key(color):
      attr.append( ttycolors[color] )
    if bold:
      attr.append( '1' )
    return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), chain)
  else:
    if hasattr(sys.stdout, 'isweb') and sys.stdout.isweb() == True:
      return '<font color="' + color + '">' + ('<b>' if bold else '') + chain + ('</b>' if bold else '') + '</font>'
  # else
  return chain

def niceOK(chain):
  if chain == 'OK':
    return totty(chain, 'green')
  else:
    return totty(chain, 'red')

def ask(what, answers = None):
  if not answers:  answers = {'y': 'Yes', 'n': 'No'}
  print what, '?'
  for a in answers.keys():
    print a, 'for', answers[a]
  print 'q to quit'
  while True:
    c = raw_input ('Please Choose : ')
    if c == 'q':
      quit('Quitting...')
    for a in answers.keys():
      if c == a: return c
  return None

def sendSlack(text, icon = ':rocket:', username = None, channel = '#general'):
  if not slackHook[0]:
    try:
      slackHook[0] = MagentoConfig(silent = True).get('slack_hook')
    except:
      pass
  if not slackHook[0]:
    print 'Warning, sendSlack used but no hook found in config file or python script'
    return
  if not username:
    username = getEnvironment() + '-bot'
  cmd = '/usr/bin/curl -X POST --data-urlencode \'payload={"channel": "' + channel + '", "username": "' + username + '", "text": "' + text + '", "icon_emoji": "' + icon + '"}\' ' + slackHook[0] + ' -o /dev/null -s'
  system(cmd)

def sendMail(plaintext = None, html = None, emails = None, subject = 'Script failed ' + sys.argv[0].split('/')[-1], encoding = 'utf-8', attach = None):
  if emails == None:
    emails = defaultToEmail
  if emails == None:
    raise ValueError, 'trying to send a mail but no recipient is configured either in the function or at the top of the script'
  if type(emails) is not list and type(emails) is not tuple:
    emails = emails.split(',') # string
  if plaintext == None and html == None:
    raise ValueError, 'plaintext and html are null, cant send an empty message'

  from email.header import Header
  from email.mime.application import MIMEApplication
  from email.MIMEMultipart import MIMEMultipart
  from email.MIMEText import MIMEText
  from email.MIMEImage import MIMEImage
  import smtplib
  
  msg = MIMEMultipart('related')
  msg['Subject'] = Header(subject, encoding)
  msg['From'] = getEnvironment() + '<%s>' % fromEmail
  msg['To'] = 'this will be overriden anyway'
  msg.preamble = 'This is a multi-part message in MIME format.'
  
  msgAlternative = MIMEMultipart('alternative')
  msg.attach(msgAlternative)
  
  if plaintext:  msgAlternative.attach(MIMEText(plaintext, 'plain', encoding))
  if html:       msgAlternative.attach(MIMEText(html, 'html', encoding))
  if attach:     
    if type(attach) is not list and type(attach) is not tuple:
      files = [ attach ]
    else:
      files = attach
    
    for f in files or []:
      with open(f, "rb") as fil:
        msg.attach(MIMEApplication(
                fil.read(),
                Content_Disposition='attachment; filename="%s"' % basename(f),
                Name = basename(f)
            ))
  
  smtp = smtplib.SMTP()
  smtp.connect('localhost')
  
  for e in emails:
    # trick to have only one To without recomputing the email twice. To MUST be the last argument.
    del msg._headers[-1]
    msg['To'] = e
    chain = msg.as_string()
    try:
      smtp.sendmail(msg['From'], e, chain)
      pass
    except:
      print e, ' was in error'
      print totty('Error sending message :', 'red', 1), plaintext, html
  smtp.quit()

# use as slice(what, 100)
slice = lambda A, n=3: [A[i:i+n] for i in range(0, len(A), n)]

def inverseDict(d):
  return dict(map(reversed, d.iteritems()))

class MagentoConfig():
  '''Class to get magento configuration parameters'''
  __shared_state = {} # borg effect
   
  def __init__(self, localxml = None, silent = False):
    self.__dict__ = self.__shared_state
    if hasattr(self, 'content'):  return  # already loaded

    if not localxml:
      cwd = getcwd()
      if '/src' in cwd:
        localxml = cwd.split('/src')[0] + '/src/app/etc/local.xml'
        if not isfile(localxml):
          if not silent:
            print localxml, totty('not found', 'red', 1)
    if '/src' not in cwd or not isfile(localxml):
      localxml = magentoServerRoot + 'app/etc/local.xml'
      if not silent:
        print 'using', localxml, 'instead'
    
    if not isfile(localxml):
      quit('Didnt find any suitable local.xml file, please go to a Magento src directory') 
    self.content = open(localxml).read()
    
  def get(self, name):
    escaped = re.escape('<%s><![CDATA[' % name) + '(.*?)' + re.escape(']]></%s>' % name)
    try:
      return re.findall(escaped, self.content)[0]
    except:
      raise Exception, 'Didnt find %s in Magento local.xml' % name