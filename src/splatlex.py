#!/usr/bin/python

from __future__ import print_function

singletons = { '!', '&', '|', '*', '+', '-', '/', ',', '@',
               '(', ')', '[', ']', '{', '}', '=', '<', '>', '#' }
literals = { 'true', 'false', 'nil' }
keywords = { 'let', 'letrec', 'def', 'set', 'lambda', 'if', 'elseif', 'else',
             'guard', 'raise', 'catch' }
reserved = set().union( singletons, literals, keywords )
bad_expr = {'&', '|', '*', '+', '/', ',', ')', ']', '{', '}', 
            '=', '<', '>', '#', 'elseif', 'else', 'guard' }

class Str(str):
  pass


class ScanError(Exception):
  def __init__(self, msg, tok):
    self.msg = msg
    self.tok = tok

  def __str__(self):
    return repr(self.msg)


def reStr( s, t ):
  r = Str( s )
  r.line = t.line
  r.col = t.col
  return r


def _char_generator( program ):
  line = 1
  col = 0
  for b in program:
    c = Str( b )
    col = col + 1
    if c == '\n':
      line = line + 1
      col = 0

    c.line = line
    c.col = col
    yield c

  c = Str( "" )
  c.line = line
  c.col = col
  yield c


def _scan( stream, acc, cond ):
  c = next( stream )
  while cond( acc, c ):
    acc = acc + c
    c = next( stream )
  return acc, c
 
 
def _scanner( program ):
  stream = _char_generator( program )
  numtest = lambda acc, c: c.isdigit()
  symtest = lambda acc, c: c.isalpha() or c.isdigit() or c == '_'
  strtest = lambda acc, c: c != '"' and c != "" 

  c = next(stream)
  while c != "":
    first = c
    acc = c

    if c.isspace():
      c = next(stream)
      continue
    elif c in singletons:
      c = next(stream)
    elif c == '"':
      acc, c = _scan( stream, acc, strtest )
      if c != "":
        acc = acc + c
        c = next(stream)
    elif c.isdigit():
      acc, c = _scan( stream, acc, numtest )
    elif c.isalpha() or c == '_':
      acc, c = _scan( stream, acc, symtest )
    else:
      raise ScanError('Unexpected character', c)
  
    yield reStr( acc, first )

  yield c


class Scanner(object):
  def __init__(self, stream):
    self.tokens = _scanner( stream )
    self.cur_token = None

  def lookahead(self):
    if self.cur_token == None:
      try:
        self.cur_token = next( self.tokens )
      except StopIteration:
        self.cur_token = None

    return self.cur_token

  def next_token(self):
    n = self.lookahead()
    self.cur_token = None
    return n


if __name__ == "__main__":
  import sys
  try:
    s = Scanner( sys.stdin.read() )
    while s.lookahead() != "":
      print( s.next_token() )
  except ScanError as p:
    print("{} at line {} col {} : {}".format(p.msg,p.tok.line,p.tok.col,p.tok))
