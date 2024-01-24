#!/usr/bin/python

import splatlex
import splatparse
import splateval


class RefEnv:
  zeroStr = splatlex.Str( "" )
  zeroStr.line = 0
  zeroStr.col = 0

  def __init__( self, prev = None ):
    self.prev = prev
    self.map = dict()

  def getStr( self, s ):
    if isinstance( s, splatlex.Str ):
      return s
    if isinstance( s, str ):
      return splatlex.reStr( s, RefEnv.zeroStr )
    elif isinstance( s, splatparse.SymbolExpr ):
      return s.sym
    else:
      return splatlex.reStr( str( s ), RefEnv.zeroStr )

  def lookup( self, id ):
    id = self.getStr( id )
    if id in self.map:
      return self.map[id]
    elif self.prev != None:
      return self.prev.lookup( id )
    else:
      raise EvalError( "Cannot find: " + str( id ), id.line, id.col )

  def update( self, id, val ):
    id = self.getStr( id )
    if id in self.map:
      self.map[id] = val
    elif self.prev != None:
      self.prev.update( id, val )
    else:
      raise EvalError( "Cannot find: " + str( id ), id.line, id.col  )

  def define( self, id, val ):
    id = self.getStr( id )
    if id in self.map:
      raise EvalError( "Duplicate symbol defined: " + id, id.line, id.col )
    self.map[id] = val


def DefExpr_eval( self, env ):
  val = self.expr.eval( env )
  env.define( self.sym, val )
  return val


def AssignExpr_eval( self, env, add_env = None ):
  val = self.expr.eval( env )
  if add_env != None:
    add_env.define( self.sym, val )
  else:
    env.update( self.sym, val )
  return val


def LetExpr_eval( self, env ):
  let_env = RefEnv( env )
  if self.rec:
    env = let_env

  for v in self.vars:
    v.eval( env, let_env )

  return self.body.eval( let_env )


def SymbolExpr_eval( self, env ):
  return env.lookup( self.sym )


splateval.top_ref = RefEnv()

splatparse.DefExpr.eval = DefExpr_eval
splatparse.AssignExpr.eval = AssignExpr_eval
splatparse.LetExpr.eval = LetExpr_eval
splatparse.SymbolExpr.eval = SymbolExpr_eval
