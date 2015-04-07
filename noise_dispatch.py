import argparse
import smtplib
from email import charset
from email.MIMEText import MIMEText
import sys
import socks
import random
from twitter import *

def base64_char(i):
  if 0 <= i <= 25:  # A-Z
    return chr(i + ord('A'))
  elif 26 <= i <= 51:  # a-z
    return chr(i + ord('a') - 26)
  elif 52 <= i <= 61:  # 0-9
    return chr(i + ord('0') - 52)
  elif i == 62:
    return '+'
  else:
    return '/'

def fake_pgp_msg():
  body = """\
-----BEGIN PGP MESSAGE-----
Version: GnuPG v1.4.12 (GNU/Linux)

"""
  for i in xrange(random.randrange(2000,5000)):
    body += base64_char(random.randrange(64))
    if (i + 1) % 64 == 0:
      body += '\n'
  body += "==\n="
  for i in xrange(0,4):
    body += base64_char(random.randrange(64))
  body +="\n-----END PGP MESSAGE-----"
  return body

class noise_dispatcher(object):
  def __init__(self,argv):
    self.config_parser(argv)
    
  def config_parser(self,argv):
    if type(argv) == dict:
      argd = argv
      argv = []
      for k,v in argd.iteritems():
	argv.append('--' + k)
	argv.append(v)
    return argv
    
  def dispatch(self,noise):
    pass

class twitter_dispatcher(noise_dispatcher):
  def config_parser(self,argv):
    argv = super(twitter_dispatcher,self).config_parser(argv)
    parser = argparse.ArgumentParser(description='This is the NOISE Twitter dispatch program.',prog='noise_tweet.py')
    parser.add_argument('-a','--app-name',type=str,required=True,help="Name of the application used to tweet")
    parser.add_argument('-k','--consumer-key',type=str,required=True,help="Consumer key specific to the application used to tweet")
    parser.add_argument('-c','--consumer-secret',type=str,required=True,help="Consumer secret specific to the application used to tweet")
    parser.add_argument('-t','--oauth-token',type=str,help="OAuth token authorizing the user to the application. If missing, you will be promted to generate one.")
    parser.add_argument('-s','--oauth-secret',type=str,help="OAuth secret authorizing the user to the application. If missing, you will be promted to generate one.")
    parser.add_argument('-b','--status',type=str,help="Status/text to tweet")
    parser.add_argument('--proxy',type=int,const=9050,nargs='?',help="Require the use of a proxy, optionally specifying the port. Default port: %(const)s.")
    self.args = parser.parse_args(argv)
    
    if not self.args.oauth_token and not self.args.oauth_secret:
      self.oauth_token, self.oauth_secret = oauth_dance(self.args.app_name,self.args.consumer_key,self.args.consumer_secret)
      print """Add the following lines to your NOISE configuration file 
(e.g. noise.conf) under the [TwitterDispatch] section:
      
oauth-token = %s
oauth-secret = %s

""" % (self.oauth_token, self.oauth_secret)
    else:
      self.oauth_token, self.oauth_secret = self.args.oauth_token, self.args.oauth_secret
    
  def dispatch(self,noise=None):
    if noise and len(noise) > 140:
      return
    if self.args.proxy:
      # Let's use a Tor SOCKS proxy, if available. Obviously, start Tor before running this program
      socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS4, 'localhost', self.args.proxy)
      s = socks.socksocket()
      s.connect(('example.com', 80))
      s.close()
      socks.wrapmodule(twitter)
    t = Twitter(
		auth=OAuth(self.oauth_token, self.oauth_secret,
			   self.args.consumer_key, self.args.consumer_secret)
    		)
    t.statuses.update(status = noise if noise else self.args.status)
    return "Successfully tweeted"
    
class email_dispatcher(noise_dispatcher):
  def config_parser(self,argv):
    argv = super(email_dispatcher,self).config_parser(argv)
    
    parser = argparse.ArgumentParser(description='This is the NOISE Email dispatch program.',prog='noise_dispatch.py')
    parser.add_argument('-f','--from',dest='sender',type=str,help="Sender (doubles as username), e.g. myemail@gmail.com", required=True)
    parser.add_argument('-t','--to',type=str,help="Recipient email address, e.g. foo@hotmail.com", required=True)
    parser.add_argument('-r','--server',type=str,help="Remote SMTP server, e.g. smtp.gmail.com", required=True)
    parser.add_argument('-p','--pass',dest='passwd',type=str,help="Account passphrase on remote server", required=True)
    parser.add_argument('-s','--subject',type=str,help="Email subject field", required=True)
    parser.add_argument('-b','--body',type=str,help="Email body text")
    parser.add_argument('-e','--encrypted',const=True,default=False,nargs='?',help="Generate fake encrypted emails instead of generating plaintext")
    parser.add_argument('--proxy',type=int,const=9050,nargs='?',help="Require the use of a proxy, optionally specifying the port. Default port: %(const)s.")
    self.args = parser.parse_args(argv)
  
  def dispatch(self,noise=None):
      charset.add_charset('utf-8', charset.SHORTEST)
      if self.args.encrypted and self.args.encrypted.lower() not in ['false','no','0']:
	msg = MIMEText(fake_pgp_msg(), _charset='utf-8')
      else:
        msg = MIMEText(noise if noise else self.args.body, _charset='utf-8')
      msg['Subject'] = self.args.subject
      msg['From'] = self.args.sender
      if ',' in self.args.to:
	random.seed()
	msg['To'] = random.choice(self.args.to.split(', '))
      else:
        msg['To'] = self.args.to
    
      if self.args.proxy:
          # Let's use a Tor SOCKS proxy, if available. Obviously, start Tor before running this program
          socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS4, 'localhost', self.args.proxy)
          s = socks.socksocket()
          s.connect(('example.com', 80))
          s.close()
          socks.wrapmodule(smtplib)
    
      # Use STARTTLS for added security
      smtpserver = smtplib.SMTP(self.args.server)
      smtpserver.starttls()
      smtpserver.set_debuglevel(True)
      smtpserver.login(self.args.sender,self.args.passwd)
      try:
        smtpserver.sendmail(self.args.sender, [self.args.to], msg.as_string())
      finally:
        smtpserver.close()
  
      return "Successfully sent mail"

if __name__ == '__main__':
  d = email_dispatcher(sys.argv[1:])
  print d.dispatch()