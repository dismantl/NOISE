import sys
from noise_dispatch import twitter_dispatcher

if __name__ == '__main__':
  d = twitter_dispatcher(sys.argv[1:])
  print d.dispatch()