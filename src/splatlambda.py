#!/usr/bin/python

import copy, types
import splatparse
import splateval
import splatref


class Lambda:
  def __init__(self, ref, params, exprs ):
    self.ref = ref
    self.params = copy.deepcopy( params )
    self.exprs = copy.deepcopy( exprs )

  def __str__(self):
    return "<lambda>"


def LambdaExpr_eval( self, env ):
  return Lambda( env, self.params, self.body )


def CallExpr_eval( self, env ):
  loc = self.loc.eval( env )
  if isinstance( loc, types.LambdaType ):
    if len( self.args ) != loc.__code__.co_argcount:
      raise EvalError( "Incorrect number of arguments", self.tok.line,
                       self.tok.col )
    args = []
    for a in self.args:
      args.append( a.eval( env ) )
    return loc( *args )
  elif isinstance( loc, Lambda ):
    call_env = splatref.RefEnv( loc.ref )
    args = iter( self.args )
    for p in loc.params:
      call_env.define( p, args.next().eval( env ) )

    return loc.exprs.eval( call_env )
  else:
    raise EvalError( "Cannot call a non-lambda expression", self.tok.line,
                        self.tok.col )
 
   
def print_arg( arg ):
  print arg
  return arg


splateval.top_ref.define( 'head', lambda lst : lst[0] )
splateval.top_ref.define( 'tail', lambda lst : lst[1:] )
splateval.top_ref.define( 'prepend', lambda head, tail : [head] + tail )
splateval.top_ref.define( 'print', print_arg )

splatparse.LambdaExpr.eval = LambdaExpr_eval
splatparse.CallExpr.eval = CallExpr_eval


