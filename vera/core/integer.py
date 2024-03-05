from .intervals import *
from dataclasses import dataclass, field
from .expr   import *
from .fpexpr import *
from .block  import *
from .intexpr import *
import sympy
import math

def get_int_var_and_type(node):
    if isinstance(node, FPBox): 
        if isinstance(node.expr, Constant):
            name = node.expr.value

        elif isinstance(node.expr, Var):
            name = node.expr.name
        else:
            ident = node.expr.ident
            name = "%s%d" % (node.expr.op_name, ident)

        int_sc = 2**(-node.type.int_bits)
        if node.type.signed:
            typ = SignedIntType(node.type.int_bits, scale=node.type.scale*int_sc)
        else:
            typ = UnsignedIntType(node.type.int_bits, scale=node.type.scale*int_sc)

        return name,typ

    else:
        raise Exception("can only resolve boxed variables")

def constval_to_int(value,typ):
    unsc_val = value/typ.scale
    intval = round(unsc_val)
    return intval 

def typecheck_int_type(node,intt,fpt):
    infer_intt = IntType.from_fixed_point_type(fpt)
    if not intt.matches(infer_intt):
        raise Exception("mismatch %s: int-type=%s | fp-type=%s (scale=%f) int-type=%s" \
                    % (node.op_name, intt,fpt,fpt.scale, infer_intt))


def ordered_type_match(e, t):
    return scale_type_match( mult_type_match( sign_type_match(e, t), t), t)

def sign_type_match(e,t):
    if e.type.signed == t.signed:
        return e
    else:
        if not e.type.signed:
            return sign_type_match(ToSInt(expr = e), t)
        else:
            return sign_type_match(ToUSInt(expr = e), t)

def mult_type_match(e,t):


    if e.type.nbits == t.nbits:
        return e
    else:
        if(e.type.nbits < t.nbits):
            nbits = t.nbits - e.type.nbits
            assert nbits > 0
            return mult_type_match(PadL(nbits = nbits, expr = e, value=0), t)
        else:
            nbits = e.type.nbits - t.nbits
            assert nbits > 0
            return mult_type_match(TruncVal(nbits = nbits, expr = e), t)
        
def scale_type_match(e, t):

    
    if abs(e.type.scale - t.scale) < (min(e.type.scale,t.scale) / 2):

        return e
    else:
        if( math.log2(e.type.scale) < math.log2(t.scale)):
            nbits = round(math.log2(t.scale)) - round(math.log2(e.type.scale))
            assert nbits > 0
            if(nbits > 0):
                return scale_type_match(TruncR(nbits=nbits, expr = e), t)
            else:
                return scale_type_match(PadR(nbits=-nbits, expr = e, value = 0), t)
        else:
            nbits = round(math.log2(e.type.scale)) - round(math.log2(t.scale))
            assert nbits > 0


            if(nbits > 0):
                return scale_type_match(PadR(nbits=nbits, expr = e, value = 0), t)
            else:
                return scale_type_match(TruncR(nbits=-nbits, expr = e), t)



        

def fpexpr_to_intexpr(blk,expr):

    def rec(e):

        return fpexpr_to_intexpr(blk,e)

    if isinstance(expr, Var):
        newV = Var(expr.name)
        newV.type = IntType.from_fixed_point_type(expr.type)
 
        return newV

    elif isinstance(expr, Constant):
        constE = Constant(expr.value)
        constE.type = IntType.from_fixed_point_type(expr.type)
        return constE
    
    elif isinstance(expr, Param):
        paramE = Param(name=expr.name, value=expr.value)
        paramE.type = IntType.from_fixed_point_type(expr.type)
        return paramE
   
    elif isinstance(expr, Product):
        nlhs = rec(expr.lhs)
        nrhs = rec(expr.rhs)
        #nlhs and nrhs really need to be the same n_bits

        nexpr = Product(nlhs,nrhs)
        nexpr.type = IntType.from_fixed_point_type(expr.type)
        nexpr.lhs = mult_type_match(nexpr.lhs,nexpr.type)
        nexpr.rhs = mult_type_match(nexpr.rhs,nexpr.type)

        typecheck_int_type(nexpr, nexpr.type, expr.type)

        return nexpr

    elif isinstance(expr, Difference):
        nlhs = rec(expr.lhs)
        nrhs = rec(expr.rhs)
        nexpr = Difference(nlhs,nrhs)
        nexpr.type = IntType.from_fixed_point_type(expr.type)

        typecheck_int_type(nexpr, nexpr.type, expr.type)
        return nexpr
    
    elif isinstance(expr, FpQuotient):
        nlhs = rec(expr.lhs)
        nrhs = rec(expr.rhs)
        
        scale = Constant( int( 1 / nrhs.type.scale ) )
        scale.type = nlhs.type
        scale = rec(scale)

        norm_expr = Product( nlhs, scale )
        norm_expr.type = IntType( nbits = 2 * nlhs.type.nbits + 2 * int(nlhs.type.signed), scale = nlhs.type.scale, signed = nlhs.type.signed)

        norm_expr.lhs = mult_type_match(norm_expr.lhs, norm_expr.type)
        norm_expr.rhs = mult_type_match(norm_expr.rhs, norm_expr.type)

        nexpr = IntQuotient( mult_type_match(scale_type_match(norm_expr, IntType.from_fixed_point_type(expr.type)), IntType.from_fixed_point_type(expr.type)), nrhs )
        nexpr.type = IntType.from_fixed_point_type(expr.type)
        nexpr.lhs = mult_type_match(nexpr.lhs,nexpr.type)
        nexpr.rhs = mult_type_match(nexpr.rhs,nexpr.type)

        typecheck_int_type(nexpr, nexpr.type, expr.type)
        return nexpr
    
    elif isinstance(expr, FpReciprocal):
        nexpr = rec(expr.expr)

        recip = IntReciprocal(expr = nexpr)
        recip.type = IntType.from_fixed_point_type(expr.type)

        
        typecheck_int_type(recip, recip.type, expr.type)
        return recip
    

    elif isinstance(expr, Negation):
        nexpr = rec(expr.expr)
        neg = Negation(nexpr)
        neg.type = IntType.from_fixed_point_type(expr.type)

        

        return neg

    elif isinstance(expr, FPToSigned):
        orig_type = expr.type
        nexpr = rec(expr.expr)
        
        tosgn = ToSInt(expr = nexpr)
        typecheck_int_type(tosgn,tosgn.type, expr.type)
        return tosgn

    elif isinstance(expr, FPExtendFrac):
        nexpr = rec(expr.expr)
        xtendF = PadR(expr=nexpr,nbits=expr.nbits,value=0)
        expected_type = IntType.from_fixed_point_type(expr.type)
        sexpr = mult_type_match(scale_type_match(xtendF, expected_type), expected_type)

        typecheck_int_type(sexpr,sexpr.type, expr.type)
        return sexpr
 
    elif isinstance(expr, FPTruncFrac):
        nexpr = rec(expr.expr)
        truncExpr = TruncR(expr = nexpr,nbits=expr.nbits)

        expected_type = IntType.from_fixed_point_type(expr.type)
        scaledexpr = mult_type_match(scale_type_match(truncExpr, expected_type), expected_type)
        typecheck_int_type(scaledexpr, scaledexpr.type, expr.type)

        return scaledexpr
    
    elif isinstance(expr, FPToUnsigned):#added by will
        nexpr = rec(expr.expr)
        usignF= ToUSInt(expr=nexpr)

        typecheck_int_type(usignF,usignF.type, expr.type)
        return usignF

    elif isinstance(expr, Sum):
        expr_lhs = rec(expr.lhs)
        expr_rhs = rec(expr.rhs)
        sumop = Sum(expr_lhs, expr_rhs)
        sumop.type = IntType.from_fixed_point_type(expr.type)

        assert(expr_lhs.type.nbits == expr_rhs.type.nbits)
        typecheck_int_type(sumop,sumop.type, expr.type)
        return sumop
    
    elif isinstance(expr, MuxC):
        expr_lhs = rec(expr.lhs)
        expr_rhs = rec(expr.rhs)
        expr_cond = rec(expr.cond)

        muxop = MuxC(expr.cond, expr_lhs, expr_rhs)
        muxop.type = IntType.from_fixed_point_type(expr.type)
        return muxop


    elif isinstance(expr, FPExtendInt):
        
        eexpr = rec(expr.expr)
        exint = PadL(expr=eexpr,nbits=expr.nbits,value=0)

        expected_type = IntType.from_fixed_point_type(expr.type)
        scaledexpr = mult_type_match(scale_type_match(exint, expected_type),expected_type)
        typecheck_int_type(scaledexpr,scaledexpr.type,expr.type)
        return exint
    
    elif isinstance(expr, FPTruncInt):
        eexpr = rec(expr.expr)
        exint = TruncVal(expr=eexpr,nbits=eexpr.type.nbits - expr.type.nbits)

        expected_type = IntType.from_fixed_point_type(expr.type)
        scaledexpr = mult_type_match(scale_type_match(exint, expected_type),expected_type)
        typecheck_int_type(scaledexpr, scaledexpr.type, expr.type)
        
        return exint
    
    elif isinstance(expr, FPTruncL):
        eexpr = rec(expr.expr)
        exint = TruncL(expr=eexpr,nbits=eexpr.type.nbits - expr.type.nbits)

        exint.expr = mult_type_match(scale_type_match(exint.expr, exint.type),exint.type)
        typecheck_int_type(exint, exint.type, expr.type)

        return exint
    
    elif isinstance(expr, FPIncreaseScale):
        eexpr = rec(expr.expr)
        exint = IntIncreaseScale(expr = eexpr, nbits=expr.nbits)
        exint.type = IntType(nbits = eexpr.type.nbits, scale = 2**(round(math.log2(eexpr.type.scale)) + expr.nbits), signed = expr.type.signed)
        exint.expr = mult_type_match(scale_type_match(exint.expr, exint.type),exint.type)
        typecheck_int_type(exint, exint.type, expr.type)
        return exint
    
    else:
        raise Exception("unhandled: %s" % expr.op_name)


def expr_to_var_name(e):
    return "%s%d" % (e.op_name, e.ident)


def decl_relations(int_blk,fp_block):
    
    for rel in fp_block.relations():
        if isinstance(rel, VarAssign):
            newlhs = fpexpr_to_intexpr(int_blk, rel.lhs)

            desired_type = IntType.from_fixed_point_type(rel.lhs.type)
            newrhs = mult_type_match(scale_type_match(fpexpr_to_intexpr(int_blk, rel.rhs), desired_type), desired_type)
            int_blk.decl_relation(VarAssign(newlhs, newrhs))

        elif isinstance(rel, Accumulate):
            newlhs = fpexpr_to_intexpr(int_blk, rel.lhs)
            newrhs = scale_type_match(fpexpr_to_intexpr(int_blk, rel.rhs), IntType.from_fixed_point_type(rel.lhs.type))
            int_blk.decl_relation(Accumulate(newlhs, newrhs))

        else:
            raise Exception("not supported.")




def to_integer(fp_block):
    int_blk = AMSBlock(fp_block.name+'-int')

    for v in fp_block.vars():

        typ = IntType.from_fixed_point_type(v.type)
        int_blk.decl_var(name=v.name, kind=v.kind, type=typ)
    
    for p in fp_block.params():
        typ = IntType.from_fixed_point_type(p.type)
        int_blk.decl_param(name=p.name, value=p.constant)   

        int_blk._params[p.name].constant.type = typ
        int_blk._params[p.name].type = typ
       
    decl_relations(int_blk, fp_block)
    return int_blk 
    