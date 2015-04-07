import argparse
import ConfigParser
import sys
import sched
import time
import random
from noise_generate import noise_generator
from noise_dispatch import email_dispatcher, twitter_dispatcher

prog_desc = """This is the NOISE program. Turn up the noise!

NOISE was written in July of 2013 as a way to create "real-looking" text based 
upon a collection of reference texts, which can then be used in emails, web 
searches, IRC chats, or any other medium you can think of that makes it a bit 
too easy to profile an individual's communication habits. Currently, NOISE only 
has email and Twitter dispatchers for generated texts.

You give NOISE one or more texts to use as a reference. The more texts, and 
longer texts, the better. NOISE then uses this collection of reference texts, 
called a corpus, to generate new, "real-looking" text, using an algorithm 
called a "Markov Chain". If you provide an optional set of keywords you want 
used in the generated text, NOISE will then replace any proper nouns in the 
generated text with a random selection of keywords from your list. NOISE will 
then email or tweet these generated texts to recipients of your choice, on a 
periodic but somewhat random schedule.

Functioning of noise.py is controlled by a configuration file. See 
noise.default.conf for an example.
"""

class noise_machine(object):
  def __init__(self,argv):
    self.gen_ops = {}
    self.once = False
    self.scheduler = sched.scheduler(time.time, time.sleep)
    self.dispatcher = []
    self.config_parser(argv)
    self.generator = noise_generator(self.gen_ops)  # Initialize markov factory and keywords
    
  def bring_the_noise(self):
    if not self.once:
      for dispatcher in self.dispatcher:
        self.scheduler.enter(0, 1, self.make_noise, ([dispatcher]))
      self.scheduler.run()
    else:
      for dispatcher in self.dispatcher:
	self.make_noise(dispatcher)
  
  def make_noise(self,dispatcher):
    self.scheduler.enter(60*random.randint(int(self.config.get('General','min-time')),
                                        int(self.config.get('General','max-time'))),
		               1,
		               self.make_noise,
		               ([dispatcher]))
    
    # magic
    success = None
    while not success:
      gen_ops = self.gen_ops
      if dispatcher.special_ops:
	for k,v in dispatcher.special_ops.iteritems():
	  gen_ops[k] = v
      noise = self.generator.generate(gen_ops)  # use remaining options
      success = dispatcher.dispatch(noise)
    print success
  
  def config_parser(self,argv):
    if type(argv) == dict:
      argd = argv
      argv = []
      for k,v in argd.iteritems():
	argv.append('--' + k)
	argv.append(v)
    
    required_sections = ['Generate','General']
    
    parser = argparse.ArgumentParser(description=prog_desc,formatter_class=argparse.RawDescriptionHelpFormatter,prog='noise.py')
    parser.add_argument('-c','--config',type=str,default='noise.conf',help="Configuration file to use. Default: %(default)s")
    parser.add_argument('--once',action='store_true',help='Only run NOISE once, instead of on a schedule')
    args = parser.parse_args(argv)
    self.once = args.once
    
    self.config = ConfigParser.RawConfigParser()
    self.config.read(args.config)
    
    for sec in required_sections:
      if not self.config.has_section(sec):
	raise StandardError("Config file missing section %s" % sec)
    
    # Parse the config options before sending to the generate and dispatch programs
    self.gen_ops = dict(self.config.items('Generate'))
    if self.config.has_section('EmailDispatch'):
      self.dispatcher.append(email_dispatcher(dict(self.config.items('EmailDispatch'))))
      self.dispatcher[-1].special_ops = {}
    if self.config.has_section('TwitterDispatch'):
      self.dispatcher.append(twitter_dispatcher(dict(self.config.items('TwitterDispatch'))))
      self.dispatcher[-1].special_ops = {'sentences':'1'}
    #if self.config.has_section('IRCDispatch'):
      #self.dispatcher.append(irc_dispatcher(dict(self.config.items('IRCDispatch'))))
  
if __name__ == '__main__':
  nm = noise_machine(sys.argv[1:])
  nm.bring_the_noise()