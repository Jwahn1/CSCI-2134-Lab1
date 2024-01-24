#!/usr/bin/python

import splatparse
from collections import namedtuple


class EvalError(Exception):
  def __init__(self, value, line, col ):
    self.value = value
    self.line = line
    self.col = col

  def __str__(self):
    return repr(self.value)


OpFunc = namedtuple( 'OpFunc', ['typ', 'op'] )
OpTypInt = type( 1 )
OpTypBool = type( True )
operators = { '+' : OpFunc( None, lambda a, b : a + b ),
              '-' : OpFunc( OpTypInt, lambda a, b : a - b ),
              '*' : OpFunc( OpTypInt, lambda a, b : a * b ),
              '/' : OpFunc( OpTypInt, lambda a, b : a / b ),
              '&' : OpFunc( OpTypBool, lambda a, b : a & b ),
              '|' : OpFunc( OpTypBool, lambda a, b : a | b ),
              '!' : OpFunc( OpTypBool, lambda a, b : not b ),
              '<' : OpFunc( None, lambda a, b : a < b ),
              '>' : OpFunc( None, lambda a, b : a > b ),
              '=' : OpFunc( None, lambda a, b : a == b ),
              '#' : OpFunc( None, lambda a, b : a != b )
              }


def EList_eval( self, env ):
  v = None
  for e in self.list:
    v = e.eval( env )
  return v
   

def SimpleExpr_eval( self, env ):
  atoms = iter( self.atoms )
  acc = next( atoms ).eval( env )

  while True:
    try:
      op = next( atoms )
      val = next( atoms ).eval( env )
    except StopIteration:
      return acc

    func = operators[op]
    if type( acc ) != type( val ):
      raise EvalError( "Operand type " + str( type( acc ) ) + " != " +\
                       str( type( val ) ), op.line, op.col )
    elif func.typ != None and type( acc ) != func.typ:
      raise EvalError( "Operand types are not correct", op.line, op.col )
    
    acc = func.op( acc, val )


def ListExpr_eval( self, env ):
  return [ a.eval( env ) for a in self.args ]

  
def UnaryExpr_eval( self, env ):
  acc = self.expr.eval( env )
  func = operators[self.op]
  if func.typ != None and type( acc ) != func.typ:
    raise EvalError( "Operand types are not correct", self.op.line, self.op.col)

  return func.op( 0, acc )


def LiteralExpr_eval( self, env ):
  return self.val


def SymbolExpr_eval( self, env ):
  return self.sym


def correct( v ):
  if isinstance( v, list ):
    return [correct(i) for i in v]
  elif isinstance( v, bool ):
    if v:
      return 'true'
    else:
      return 'false'
  elif v == None:
    return 'nil'
  else:
    return v


splatparse.EList.eval = EList_eval
splatparse.SimpleExpr.eval = SimpleExpr_eval
splatparse.ListExpr.eval = ListExpr_eval
splatparse.UnaryExpr.eval = UnaryExpr_eval
splatparse.LiteralExpr.eval = LiteralExpr_eval
splatparse.SymbolExpr.eval = SymbolExpr_eval

top_ref = None
