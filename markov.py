# This is a modified version of https://kartoffelsalad.googlecode.com/svn-history/r9/trunk/lib/markov.py
#
# A contextual markov chain sentence generator.
#
# The main class of the module, MarkovGenerator, takes sentences and
# exerpts of human conversation, and constructs a markov chain from
# that knowledge. It can then probabalistically construct new
# sentences based on its knowledge of what constitutes probably
# conversation.

import re
import random
import collections
import pickle
import gzip

PROPOSITION_SEPARATOR = r'[,:;]'
SENTENCE_TERMINATOR = r'[?!.]+'
SMILEY = r"[:;8=][o\-']?[()\[\]/\\\?pPdD*$]+"
URL = r"\b\w+://\S*\b"

PROPOSITION_SEPARATOR_RE = re.compile(
    r'(?x)' + PROPOSITION_SEPARATOR, re.UNICODE)
SENTENCE_TERMINATOR_RE = re.compile(r'(?x)' + SENTENCE_TERMINATOR, re.UNICODE)
SPLIT_RE = re.compile(r'''(?x)
(
  %s   | # A URL
  %s   | # A smiley
  %s   | # One of these is considered a separator
  [()] | # Parentesis
  %s   | # Several of these in a row also
  \s+    # Last resort, whitespace.
)''' % (URL, SMILEY, PROPOSITION_SEPARATOR, SENTENCE_TERMINATOR), re.UNICODE)

class MarkovToken(object):
    def __init__(self, token, tag=None):
        self.token = token
        self.tag = tag
        #self.replaced = False
        if PROPOSITION_SEPARATOR_RE.match(token):
            self.space_before, self.end = False, False
        elif SENTENCE_TERMINATOR_RE.match(token):
            self.space_before, self.end = False, True
        else:
            self.space_before, self.end = True, False

    def output(self):
        if self.space_before:
            return [' ', self.token]
        else:
            return [self.token]

    def __str__(self):
        return self.token

    def __repr__(self):
        return "<token '%s' '%s'>" % (self.token, self.tag)

    #def __eq__(self, other):
        #return (self.token == other.token and
                #self.end == other.end and
                #self.space_before == other.space_before)

    #def __ne__(self, other):
        #return not (self == other)

    #def __hash__(self):
        #return (hash(self.token) ^
                #(hash(self.end) << 2) ^
                #(hash(self.space_before) << 3))


class MarkovTokenFactory(object):
    def __init__(self):
        self.tokens = {}
        self.cnt = {}

    def __call__(self, s):
        self.cnt[s] = self.cnt.get(s, 0) + 1
        if s in self.tokens:
            return self.tokens[s]
        else:
            tok = MarkovToken(s)
            self.tokens[s] = tok
            return tok


class MarkovGenerator(object):
    def __init__(self, context=2):
        self.tokens = {}
        self.context = context
        self.factory = MarkovTokenFactory()

    def lex(self, sentence):
        return [self.factory(x.strip()) for x
                in SPLIT_RE.split(sentence) if x.strip()]

    def markov_sequence(self, tokens, context):
        sequence = collections.deque((None,)*context)
        for token in tokens:
	  if len(token.token.strip('()[]{}<>"')) > 0: # Don't add punctuation that requires matched pairs
	    token.token = token.token.strip('"')
            yield tuple(sequence), token
            if token.end:
                sequence = collections.deque((None,)*context)
            else:
                sequence.popleft()
                sequence.append(token)

    def learn(self, sentence):
        tokens = self.lex(sentence)
        if len(tokens) < 4:
            return
        tokens[-1].end = True
        for context,next in self.markov_sequence(tokens, self.context):
            weight = self.tokens.setdefault(context, {}).setdefault(next, 0)
            self.tokens[context][next] = weight+1

    def say(self, start_word=None):
        sequence = collections.deque((None,)*self.context)
        if start_word:
            sequence.popleft()
            sequence.append(start_word)
            # Tried to start a sentence, but unknown start word.
            if tuple(sequence) not in self.tokens:
                return None
        sentence = []
        words = 0
        used_contexts = {}
        # the "not sentence[-1].end" makes it stop iterating after it gets to a ending token
        while not sentence or not sentence[-1].end:
            context = tuple(sequence)
            next_dict = self.tokens[context]
            total = sum(next_dict.itervalues())
            select = random.randint(1, total+1)
            for next_word,weight in next_dict.iteritems():
                total -= weight
                if total <= select:
                    used_contexts[context] = used_contexts.setdefault(context,0) + 1
                    if used_contexts[context] > 3: return (None,None)  # Avoid infinite loop
                    sentence.append(next_word)
                    sequence.popleft()
                    sequence.append(next_word)
                    if len(next_word.token) > 1:
		      words += 1
                    break
        #return ''.join([''.join(x.output()) for x in sentence])
        return (sentence, words)

    def save(self, filename):
        f = gzip.GzipFile(filename, 'wb')
        data_to_save = (self.context, self.factory, self.tokens)
        pickle.dump(data_to_save, f, -1)
        f.close()

    def load(self, filename):
        f = gzip.GzipFile(filename, 'rb')
        (self.context, self.factory,
         self.tokens) = pickle.load(f)
        f.close()


if __name__ == '__main__':
    import sys
    m = MarkovGenerator(2)
    m.learn(file(sys.argv[1]).read())
    print m.say()
