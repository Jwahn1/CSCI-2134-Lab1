#!/usr/bin/python

import types
import splatparse
import splateval
import splatref


class SplatException(Exception):
  def __init__(self, ex):
    self.exval = ex

  def __str__(self):
    return repr(self.exval)


def GuardExpr_eval( self, env ):
  try:
    return self.body.eval( env )
  except SplatException as ex:
    env = splatref.RefEnv( env )
    env.define( self.exvar, ex.exval )
    return self.catches.eval( env, ex.exval )


def CatchExpr_eval( self, env, ex ):
  if self.expr == None:
    return self.body.eval( env )

  cond = self.expr.eval( env )
  if type( cond ) != type( True ):
    raise splateval.EvalError( "Catch condition does not yield a boolean", 
                               self.tok.line, self.tok.col )
  if cond:
    return self.body.eval( env )
  elif self.next != None:
    return self.next.eval( env, ex )
  else:
    raise SplatException( ex )
      

def RaiseExpr_eval( self, env ):
  raise SplatException( self.expr.eval( env ) )


splatparse.GuardExpr.eval = GuardExpr_eval
splatparse.CatchExpr.eval = CatchExpr_eval
splatparse.RaiseExpr.eval = RaiseExpr_eval
