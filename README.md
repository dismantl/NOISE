NOISE
=====

Introduction
------------

NOISE was written in July of 2013 as a way to create "real-looking" text based upon a collection of reference texts, which can then be used in emails, tweets, web searches, IRC chats, or any other medium you can think of that makes it a bit too easy to profile an individual's communication habits. Currently, NOISE only has email and Twitter dispatchers for generated texts.

How does it work?
-----------------

You give NOISE one or more texts to use as a reference. The more texts, and longer texts, the better. NOISE then uses this collection of reference texts, called a corpus, to generate new, "real-looking" text, using an algorithm called a "Markov Chain". If you provide an optional set of keywords you want used in the generated text, NOISE will then replace any proper nouns in the generated text with a random selection of keywords from your list. NOISE will then email these generated texts to recipients of your choice, on a periodic but somewhat random schedule.

Installation
------------

NOISE requires python version 2.7, the NumPy library, and the Natural Language Toolkit. See their websites for installation instructions:

* Python: http://python.org/download/
* NumPy: http://www.scipy.org/install.html
* NLTK: http://nltk.org/install.html (Requires `maxent_treebank_pos_tagger` from NLTK Data)

For Debian-based systems, dependencies can be installed as follows:

`sudo apt-get update && sudo apt-get install python2.7 python-pip`
`sudo pip install numpy nltk`
`python -m nltk.downloader maxent_treebank_pos_tagger`

How to use
----------

NOISE currently comes with five different programs, which can all be run on their own:

* **noise.py**: This is the main NOISE program, which uses noise_generate, noise_dispatch, and noise_tweet. It reads in a configuration file as its only parameter. This is probably what you'll want to run.
* **noise_generate.py**: This takes a collection of reference texts (called a "corpus"), and generates "real-looking" text based upon the corpus using Markov chains.
* **noise_dispatch.py**: The dispatcher simply connects to a mail server and sends an email based on the given parameters.
* **noise_tweet.py**: This program will tweet something on Twitter...
* **noise_keyword_parser.py**: This program takes lists of keywords as input and creates a weighted keywords file, to be used in noise.py or noise_generate.py.

NOISE comes with a default configuration file `noise.default.conf` that you can modify to meet your needs, and also has explanations of all the relevant options. NOISE can then be run as so:  
`python noise.py -c noise.conf`

NOISE can also be run over Tor, in case you don't want your identity revealed. You must have Tor running with a SOCKS proxy in order to do this. Torsocks is the recommended way to run NOISE over Tor:

`torsocks python noise.py -c noise.conf`

**NOTE**: Tor does not provide perfect anonymity. Please see their full list of warnings before using Tor: https://www.torproject.org/download/download-easy.html.en#warning. Obviously, don't use a personally identifiable email address with NOISE if you want to stay anonymous.

Corpus & Keywords
-----------------

It's up to you to provide your own corpus and keywords file. NLTK.org ships with some corpora you can use for free (see http://nltk.org/data.html).

Credits & License
-----------------

NOISE is GPLv3 licensed. See LICENSE.txt

NOISE was created by Dan Staples (dismantl): http://disman.tl/ / noise@disman.tl.  
The Markov code comes from https://code.google.com/p/kartoffelsalad/.  
SOCKS proxy functionality from https://code.google.com/p/socksipy-branch/.

Changelog
---------

28 July 2013: Initial release.  
30 July 2013: Added recurring dispatch schedule and more documentation.  
4 August 2013: noise.py can now generate fake PGP-encrypted emails.  
9 August 2013: Added STARTTLS, new config option, misc bug fix  
13 August 2013: Performance improvements, misc bug fixes, added min-keywords option  
17 August 2013: Major code refactoring, added Twitter dispatcher, misc fixes  
