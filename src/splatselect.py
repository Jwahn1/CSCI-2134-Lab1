#!/usr/bin/python

import types
import splatparse


def IfExpr_eval( self, env ):
  cond = True
  if self.cond != None:
    cond = self.cond.eval( env )
    if type( cond ) != type( True ):
      raise EvalError( "Condition not boolean", self.tok.line, self.tok.col )

  if cond:
    return self.body.eval( env )
  elif self.next != None:
    return self.next.eval( env )
  else:
    return False


splatparse.IfExpr.eval = IfExpr_eval
