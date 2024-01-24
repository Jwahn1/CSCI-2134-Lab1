#!/usr/bin/python

from __future__ import print_function
import splatlex
import splatparse
import splateval
import splatref
import splatlambda
import sys 

verbose = "-v" in sys.argv

try:
  l = splatparse.parse( sys.stdin.read() )
  if l != None:
    print( splateval.correct( l.eval( splateval.top_ref ) ) )
except splatlex.ScanError as p:
  print("{} at line {} col {} : {}".format(p.msg,p.tok.line,p.tok.col,p.tok))
except splatparse.ParseError as p:
  if verbose:
    print( "Syntax error on line " + str( p.tok.line ) + ", col " + \
          str( p.tok.col ) + " : " + str( p ) )
  else:
    print( "Syntax Error" )
except splateval.EvalError as p:
  print( "Evaluation Error while evaluating " + str( p ) + " on line " +\
          str( p.line ) + ", column " + str( p.col ) )
