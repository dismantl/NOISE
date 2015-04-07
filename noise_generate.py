import json
import asyncore
import socket
import sys
import nltk
import argparse
import os
from numpy import cumsum
from numpy.random import rand
from markov import *

prog_desc = """This is the NOISE generation program.

You give NOISE one or more texts to use as a reference. The more texts, and 
longer texts, the better. NOISE then uses this collection of reference texts, 
called a corpus, to generate new, "real-looking" text, using an algorithm 
called a "Markov Chain".

If you provide an optional set of keywords you want used in the generated text, 
NOISE will then replace any proper nouns in the generated text with a random 
selection of keywords from your list.
"""

class noise_generator(object):
  def __init__(self,argv):
    self.m = None
    self.keywords = None
    self.config_parser(argv)
    
  def config_parser(self,argv):
    if type(argv) == dict:
      argd = argv
      argv = []
      for k,v in argd.iteritems():
        argv.append('--' + k)
        argv.append(v)
    
    parser = argparse.ArgumentParser(description=prog_desc,formatter_class=argparse.RawDescriptionHelpFormatter,prog='noise_generate.py')
    parser.add_argument('-d','--corpus-dir',type=str,action='append',help='Directory of corpus text files to parse')
    parser.add_argument('-o','--output-tokens',type=str,help='Output file to write tagged tokens')
    parser.add_argument('-i','--input-tokens',type=str,action='append',help='Gzipped input file from which to read tagged tokens')
    parser.add_argument('-f','--input-corpus',type=file,action='append',help='Corpus text file')
    parser.add_argument('-k','--keywords-file',type=str,help='File containing keywords for replacement')
    parser.add_argument('-l','--markov-length',type=int,choices=xrange(1,5),metavar='MARKOV_LENGTH',default=2,help='Markov chain length, default=%(default)s')
    parser.add_argument('-m','--max-keywords',type=int,default=3,help="Maximum number of keywords to insert")
    parser.add_argument('-n','--min-keywords',type=int,default=0,help="Minimum number of keywords to insert")
    parser.add_argument('-w','--min-length',default=5,type=int,choices=xrange(1,20),help='Minimum number of words in output sentences, default=%(default)s',metavar='MIN_LENGTH')
    parser.add_argument('-s','--sentences',type=int,default=5,help='Number of sentences to output, default=%(default)s')
    parser.add_argument('--daemonize',action='store_true',help='Start noise_generate as a daemon, listening on a UNIX socket for requests')
    args = parser.parse_args(argv)
    
    if not self.m:
      if not args.corpus_dir and not args.input_corpus and not args.input_tokens:
        raise StandardError("No input corpus (-f), directory (-d), or tokens (-i) given!")
    
      self.m = MarkovGenerator(args.markov_length)
    
      if args.input_tokens:
        for input_tokens in args.input_tokens:
          self.m.load(input_tokens)
    
      if args.input_corpus:
        for corpus in args.input_corpus:
          self.m.learn(corpus.read())
          corpus.close()
    
      if args.corpus_dir:
        for corpus_dir in args.corpus_dir:
          for corpus_file in os.listdir(corpus_dir):
	    corpus = open(corpus_dir + corpus_file)
	    self.m.learn(corpus.read())
	    corpus.close()
    
      if args.output_tokens:
        self.m.save(args.output_tokens)
    
    if not self.keywords and args.keywords_file:
      with open(args.keywords_file) as keywords_file:
        self.keywords = self.ReadKeywords(keywords_file)
    
    if args.min_keywords and args.max_keywords and args.max_keywords < args.min_keywords:
      raise ValueError("Invalid min/max keywords options")
    
    if args.daemonize:
      self.server = SocketServer('noise_generate',self)
      asyncore.loop()
    
    return args
  
  def generate(self,argv):
    args = self.config_parser(argv)
    replacements = -1
    while replacements < args.min_keywords:
      # Generate the sentences
      sentence = []
      for x in xrange(1,args.sentences + 1):
        words = 0
        while words < args.min_length:
          (phrase, words) = self.m.say()
        sentence += phrase

      # Replace proper nouns with keywords, if needed
      replacements = 0
      if self.keywords and args.max_keywords > 0:
        factory = MarkovTokenFactory()
        tokens = [str(x) for x in sentence]
        tags = nltk.tag.pos_tag(tokens)
        pnouns = []
        for i in xrange(0,len(tags)):
	  if tags[i][1] == 'NNP' or tags[i][1] == 'NNPS':
	    pnouns.append(i)
	replacement_words = []
        for j in xrange(0,len(pnouns)):
	  i = random.choice(pnouns)
	  ret = self.add_keyword(i,tags,sentence,factory)
	  if ret:
	    replacement_words.append(ret)
	    pnouns.remove(i)
	    replacements = self.count_keywords(sentence,replacement_words)
	    if replacements >= args.max_keywords: break
      else:
	replacements = args.min_keywords
    
    # Reconstruct sentence and return it
    return ''.join([''.join(x.output()) for x in sentence]).strip()
  
  def ReadKeywords(self,fd):
    k = json.load(fd)
    total = 0
    weights = []
    categories = []
    for category in k:
      total += k[category]['weight']
      categories.append(category)
      weights.append(k[category]['weight'])
    if total != 1: 
      raise ArithmeticError("Invalid keyword weighting: " + str(total))
    return [weights, categories, k]

  def weightedChoice(self,weights, objects):
    """Return a random item from objects, with the weighting defined by weights 
    (which must sum to 1)."""
    cs = cumsum(weights) #An array of the weights, cumulatively summed.
    idx = sum(cs < rand()) #Find the index of the first weight over a random value.
    return objects[idx]

  def add_keyword(self,i,tags,sentence,factory):
    ret = None
    try:
      if (tags[i][1] == 'NNP' or tags[i][1] == 'NNPS') and len(str(sentence[i])) >= 2:
	category = self.weightedChoice(self.keywords[0],self.keywords[1])
	keyword = random.choice(self.keywords[2][category]['keywords'])
	print "Replacing " + str(sentence[i]) + " with " + keyword
	sentence[i] = factory(keyword)
	sentence[i].tag = tags[i][1]
	ret = keyword
	while (tags[i+1][1] == 'NNP' or tags[i+1][1] == 'NNPS') or (tags[i+2][1] == 'NNP' or tags[i+2][1] == 'NNPS'):
	  if tags[i+1][1] == 'NNP' or tags[i+1][1] == 'NNPS':
	    del sentence[i+1]
	    del tags[i+1]
	  else:
	    del sentence[i+2]
	    del tags[i+2]
	    del sentence[i+1]
	    del tags[i+1]
    except:
      pass
    return ret

  def count_keywords(self,sentence,words):
    count = 0;
    for tok in sentence:
      if tok.token in words:
	count += 1
    return count

class SocketHandler(asyncore.dispatcher_with_send):
    def __init__(self, sock, caller):
        asyncore.dispatcher.__init__(self, sock)
        self.out_buffer = ''
        self.caller = caller

    def handle_read(self):
        data = self.recv(1024)
        if data:
	  try:
            self.send(self.caller.generate(json.loads(data)))
	  except:
	    self.send('')

class SocketServer(asyncore.dispatcher):
    def __init__(self, sock_addr, caller):
        asyncore.dispatcher.__init__(self)
        #self.args = args
        self.caller = caller
        self.create_socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(sock_addr)
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            handler = SocketHandler(sock, self.caller)
    
if __name__ == '__main__':
  g = noise_generator(sys.argv[1:])
  print g.generate(sys.argv[1:])