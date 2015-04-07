import sys
import argparse
import json

prog_desc = """\
This is the NOISE keyword parser program.

This program converts lists of keywords into a file that is usable by 
noise_generate.py. Each keyword list can be given a different weight depending 
on how often you want words from that list to appear in the generated text.

Let's say you have three keyword lists, 'people', 'places', and 'things'. You 
want words in the 'things' list to appear twice as often as words from the 
'people' or 'places' lists. You would run:

python noise_keyword_parse.py -c people -w 0.25 -i people.txt -o keywords.txt
python noise_keyword_parse.py -c places -w 0.25 -i places.txt -o keywords.txt
python noise_keyword_parse.py -c things -w 0.5 -i things.txt -o keywords.txt

You would then pass keywords.txt to noise_generate.py with the 
'--keywords-file' flag.
"""

def keyword_parser(argv):
  parser = argparse.ArgumentParser(description=prog_desc,formatter_class=argparse.RawDescriptionHelpFormatter,prog='noise_keyword_parse.py')
  parser.add_argument('-c','--category',type=str,help='Category name for the input keyword list',required=True)
  parser.add_argument('-w','--weight',type=float,help='Weight to give the keyword list (e.g. 0.2). All the weights in a keyword file must add up to 1')
  parser.add_argument('-i','--input-file',type=file,help='Input file of keywords to use. Each keyword should be on a new line.',required=True)
  parser.add_argument('-o','--output-file',type=str,help='Output file to append keyword list',required=True)
  args = parser.parse_args(argv)
  
  try:
    output_file = open(args.output_file,'r')
    kw = json.load(output_file)
    output_file.close()
  except:
    kw = {}
  
  if not args.category in kw:
    kw[args.category] = {}
    kw[args.category]['keywords'] = []
  kw[args.category]['weight'] = args.weight
  keywords = args.input_file.read().splitlines()
  keywords = [x.decode('utf8') for x in keywords]
  for keyword in keywords:
    if not keyword in kw[args.category]['keywords']:
      kw[args.category]['keywords'].append(keyword)
  
  try:
    import io
    with io.open(args.output_file,'w',encoding='utf-8') as f:
      f.write(unicode(json.dumps(kw,ensure_ascii=False)))
  except Exception, exc:
    sys.exit("Failed to write keywords to output file %s: %s" % (args.output_file,str(exc)))
  
  return "Successfully wrote keywords to output file"

if __name__ == '__main__':
  print(keyword_parser(sys.argv[1:]))