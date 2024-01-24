#!/usr/bin/python

from __future__ import print_function
import splatlex
import sys
from collections import namedtuple

verbose = "-v" in sys.argv
print_rules = "-r" in sys.argv
scanner = None

class ParseError(Exception):
  def __init__(self, value, tok):
    self.value = value
    self.tok = tok

  def __str__(self):
    return repr(self.value)


def rule( r ):
  if print_rules:
    print( r )


class EList:
  def __init__( self ):
    self.list = []
    self.parse()

  def parse( self ):
    rule( "E_LIST -> EXPR E_TAIL" )
  
    self.list.append( parseExpr() )
    self.parseETail()
   
  def parseETail( self ):
    tok = scanner.lookahead()
    if tok == '}' or tok == "":
      rule( "E_TAIL -> epsilon" )
      return
  
    rule( "E_TAIL -> E_LIST" )
    self.parse()

   
OpLevel = namedtuple( 'OpLevel', ['expr', 'head', 'tail', 'ops', 'next' ] )

fact_lvl = OpLevel( "FACT", "VALUE", "F_TAIL", { '*', '/' }, None )
term_lvl = OpLevel( "TERM", "FACT", "T_TAIL", { '+', '-' }, fact_lvl )
rel_lvl = OpLevel( "RELOP", "TERM", "R_TAIL", { '<', '>', '=', '#' }, term_lvl )
and_lvl = OpLevel( "ANDOP", "RELOP", "A_TAIL", { '&' }, rel_lvl )
top_lvl = OpLevel( "S_EXPR", "ANDOP", "S_TAIL", { '|' }, and_lvl )
 
 
class SimpleExpr:
  def __init__( self, op_lvl = top_lvl ):
    self.atoms = []
    self.parse( op_lvl )

  def parse( self, op_lvl ):
    rule( op_lvl.expr + " -> " + op_lvl.head + " " + op_lvl.tail  )
    if op_lvl.next != None:
      self.atoms.append( SimpleExpr( op_lvl.next ) )
    else:
      self.atoms.append( parseValue() )

    self.parseTail( op_lvl )

  def parseTail( self, op_lvl ):
    if scanner.lookahead() in op_lvl.ops:
      tok = scanner.next_token()
      rule( op_lvl.tail + " -> '" + tok + "' " + op_lvl.expr )
      self.atoms.append( tok )
      self.parse( op_lvl )
    else:
      rule( op_lvl.tail + " -> epsilon"  )

  def pack( self ):
    if len( self.atoms ) == 1 :
      if isinstance( self.atoms[0], SimpleExpr ):
        return self.atoms[0].pack()
      else:
        return self.atoms[0]
    else:
      return self

class ListExpr:
  def __init__( self ):
    rule( "LIST -> '[' ARGS ']'" )

    scanner.next_token()
    self.args = []

    parseArgs( self.args, ']' )
    scanner.next_token()          # closing ']' token


class UnaryExpr:
  def __init__( self ):
    self.op = scanner.next_token()
    rule( "UNARY -> '" + self.op + "' VALUE"  )
    self.expr = parseValue()


class LiteralExpr:
  def __init__( self ):
    tok = scanner.next_token()
    if tok.isdigit():
      rule( "LITERAL -> int(" + tok + ")"  )
      self.val = int( tok )
    elif tok[0] == '"':
      rule( "LITERAL -> string(" + tok + ")"  )
      self.val = tok[1:-1]
    elif tok == 'true':
      rule( "LITERAL -> 'true'"  )
      self.val = True
    elif tok == 'false':
      rule( "LITERAL -> 'false'"  )
      self.val = False
    elif tok == 'nil':
      rule( "LITERAL -> 'nil'"  )
      self.val = None


class SymbolExpr:
  def __init__( self ):
    self.sym = scanner.next_token()
    rule( "SYMBOL -> symbol(" + self.sym +")" )
    if self.sym in splatlex.reserved or self.sym.isdigit():
      raise ParseError( "Invalid symbol name", self.sym )


def parseS():
  tok = scanner.lookahead()
  if tok == "":
    rule( "S -> epsilon" )
    return None
  
  rule( "S -> E_LIST" )
  return EList()
  

class DefExpr:
  def __init__( self ):
    rule( "DEF -> 'def' SYMBOL EXPR" )
    scanner.next_token()

    self.sym = SymbolExpr()
    tok = scanner.next_token()
    if tok != '=':
      raise ParseError( "Expecting '='", tok )

    self.expr = parseExpr()


class AssignExpr:
  def __init__( self, is_expr ):
    if is_expr:
      rule( "ASSIGN -> 'set' SYMBOL '=' EXPR" )
      scanner.next_token()

    self.sym = SymbolExpr()
    tok = scanner.next_token()
    if tok != '=':
      raise ParseError( "Expecting '='", tok )

    self.expr = parseExpr()


class LambdaExpr:
  def __init__( self ):
    rule( "LAMBDA -> 'lambda' '(' PARAMS ')'  BODY" )
    scanner.next_token()

    tok = scanner.next_token()
    if tok != '(':
      raise ParseError( "Expecting '('", tok )

    self.parseParams()

    tok = scanner.next_token()
    if tok != ')':
      raise ParseError( "Expecting ')'", tok )

    self.body = parseBody()

  def parseParams( self ):
    self.params = []
    tok = scanner.lookahead()

    if tok == ')':
      rule( "PARAMS -> epsilon" )
    else:
      rule( "PARAMS -> SYMBOL P_LIST" )
      self.params.append( SymbolExpr() )
      self.parsePList()

  def parsePList( self ):
    tok = scanner.lookahead()

    if tok == ')':
      rule( "P_LIST -> epsilon" )
    elif tok == ',':
      rule( "P_LIST -> ',' SYMBOL P_LIST" )
      scanner.next_token()
      self.params.append( SymbolExpr() )
      self.parsePList()
    else:
      raise ParseError( "Expecting ',' or ')'", tok )


class LetExpr:
  def __init__( self ):
    tok = scanner.next_token()
    self.rec = tok == 'letrec'
    rule( "LET -> '" + str(tok) + "' V_LIST BODY" )

    self.vars = []
    self.parseVList()
    self.body = parseBody()
  
  def parseVList( self ):
    rule( "V_LIST -> SYM '=' EXPR V_TAIL" )
    self.vars.append( AssignExpr( False ) )
    self.parseVTail()

  def parseVTail( self ):
    if scanner.lookahead() == ',':
      rule( "V_TAIL -> ',' V_LIST" )
      scanner.next_token()
      self.parseVList()
    else:
      rule( "V_TAIL -> epsilon" )


class IfExpr:
  def __init__( self ):
    self.cond = None
    self.next = None

    tok = scanner.next_token()
    if tok == 'if':
      rule( "IF -> 'if' EXPR BODY ELIF ELSE"  )
      self.tok = scanner.lookahead()
      self.cond = parseExpr()
    elif tok == 'elseif':
      rule( "ELIF -> 'elseif' EXPR BODY ELIF"  )
      self.tok = scanner.lookahead()
      self.cond = parseExpr()
    elif tok == 'else':
      rule( "ELSE -> 'ELSE' BODY"  )

    self.body = parseBody()

    tok = scanner.lookahead()
    if self.cond != None:
      if tok == 'elseif':
        self.next = IfExpr()
      else:
        rule( "ELIF -> epsilon"  )
        if scanner.lookahead() == 'else':
          self.next = IfExpr()
        else:
          rule( "ELSE -> epsilon"  )


class GuardExpr:
  def __init__( self ):
    rule( "GUARD -> 'guard' SYMBOL BODY CATCH"  )
    scanner.next_token()
    self.exvar = SymbolExpr()
    self.body = parseBody()
    tok = scanner.lookahead()
    if tok != 'catch':
      raise ParseError( "Expecting 'catch' clause", tok )
    self.catches = CatchExpr()


class CatchExpr:
  def __init__( self ):
    scanner.next_token()
    self.tok = scanner.lookahead()
    if self.tok == '{':
      rule( "CATCH -> 'catch' BODY" )
      self.expr = None
    else:
      rule( "CATCH -> 'catch' EXPR BODY" )
      self.expr = parseExpr()

    self.body = parseBody()
    if scanner.lookahead() == 'catch':
      self.next = CatchExpr()
    else:
      rule( "CATCH -> epsilon"  )
      self.next = None


class RaiseExpr:
  def __init__( self ):
    rule( "RAISE -> 'raise' EXPR"  )
    scanner.next_token()
    self.expr = parseExpr()


class CallExpr:
  def __init__( self ):
    rule( "CALL -> '@' EXPR '(' ARGS ')'" )
    scanner.next_token()
    self.loc =  parseExpr()
    self.args = []

    self.tok = scanner.next_token()
    if self.tok != '(':
      raise ParseError( "Expecting '(' in call", self.tok )

    parseArgs( self.args, ')' )
    scanner.next_token()          # closing ')' token


ok_sexpr = { '!', '@', '-', '(', '[', 'true', 'false', 'nil' }

def parseExpr():
  tok = scanner.lookahead()
 
  if tok == 'def':
    rule( "EXPR -> DEF" )
    return DefExpr()
  elif tok == 'set':
    rule( "EXPR -> ASSIGN" )
    return AssignExpr( True )
  elif tok == 'lambda':
    rule( "EXPR -> LAMBDA" )
    return LambdaExpr()
  elif tok == 'let' or tok == 'letrec':
    rule( "EXPR -> LET" )
    return LetExpr()
  elif tok == 'if':
    rule( "EXPR -> IF" )
    return IfExpr()
  elif tok == 'guard':
    rule( "EXPR -> GUARD" )
    return GuardExpr()
  elif tok == 'raise':
    rule( "EXPR -> RAISE" )
    return RaiseExpr()
  elif tok in ok_sexpr or tok not in splatlex.reserved: 
    rule( "EXPR -> S_EXPR" )
    return SimpleExpr().pack()  # collapse some needless lists
  else:
    raise ParseError( "Invalid expression", tok )


def parseBody():
  tok = scanner.next_token()
  if tok != '{':
    raise ParseError( "Expecting '{' at start of block", tok )

  rule( "BODY -> '{' E_LIST '}'" )
  l = EList()

  tok = scanner.next_token() 
  if tok != '}':
    raise ParseError( "Expecting '}' at end of block", tok )

  return l


def parseValue():
  tok = scanner.lookahead()
  if tok == "":
    raise ParseError( "Unexpected end of program", tok )
  elif tok == "@":
    rule( "VALUE -> CALL" )
    return CallExpr()
  elif tok == "(":
    rule( "VALUE -> '(' EXPR ')'" )
    scanner.next_token()
    e = parseExpr()
    tok = scanner.next_token() 
    if tok != ')':
      raise ParseError( "Expecting ')' after expression", tok )
    return e
  elif tok == '[':
    rule( "VALUE -> LIST" )
    return ListExpr()
  elif tok == "-" or tok == '!':   # unary operation
    rule( "VALUE -> UNARY" )
    return UnaryExpr()
  elif tok.isdigit() or tok[0] == '"' or tok in splatlex.literals:  # literal
    rule( "VALUE -> LITERAL" )
    return LiteralExpr()
  elif tok.isidentifier():                           # identifier
    rule( "VALUE -> SYMBOL" )
    return SymbolExpr()
  else:                                              # error
    raise ParseError( "Unexpected token ", tok )



def parseArgs( args, brkt ):
  if scanner.lookahead() == brkt:  
    rule( "ARGS -> epsilon" )
  else:
    rule( "ARGS -> EXPR A_LIST" )
    args.append( parseExpr() )
    parseAList( args, brkt )
 
      
def parseAList( args, brkt ):
  tok = scanner.lookahead()
  if tok == brkt:  
    rule( "A_LIST -> epsilon" )
  elif tok == ',':
    rule( "A_LIST -> ',' EXPR A_LIST" )
    scanner.next_token()
    args.append( parseExpr() )
    parseAList( args, brkt )
  else:
    raise ParseError("Expecting ',' or '" +str(brkt)+ "' after list item", tok)


def parse(stream):
  global scanner
  scanner = splatlex.Scanner( stream )
  l = parseS()
  tok = scanner.lookahead()
  if tok != "":
    raise ParseError( "Extraneous input", tok )
  return l


if __name__ == "__main__":
  print_rules = True
  try:
    parse( sys.stdin.read() )
  except splatlex.ScanError as p:
    print("{} at line {} col {} : {}".format(p.msg,p.tok.line,p.tok.col,p.tok))
  except ParseError as p:
    if verbose:
      print( "Syntax error on line " + str( p.tok.line ) + ", col " + \
            str( p.tok.col ) + " : " + str( p ) )
    else:
      print( "Syntax Error" )
