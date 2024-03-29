from uncertainties import ufloat
from uncertainties.umath import  *
from dataclasses import dataclass, field
from .expr  import *
from .block import *
from .fpexpr import *
import sympy
import math

class IntervalPrecRegistery:

    @dataclass
    class IntervalPrecInfo:
        upper: float
        lower: float
        precision: float
        interval_expr: ufloat = None
        precision_expr: ufloat = None

        def initialize(self):

            self.interval_expr = ufloat((self.upper+self.lower)/2, abs(self.upper-self.lower)/2)
            self.precision_expr = ufloat((self.upper+self.lower)/2, abs(self.upper-self.lower)/2 + self.precision)

        def check(self):
            assert(self.precision > 0.0)
            assert(self.upper >= self.lower)


    def __init__(self):
        self.info = {}

    def decl_info(self,ident,lower,upper,precision):
        self.info[ident] = IntervalPrecRegistery.IntervalPrecInfo(lower=lower, upper=upper,precision=precision)
        self.info[ident].initialize()
        self.info[ident].check()
        return self.info[ident]

    def decl_sym_info(self,ident,interval_expr, precision_expr, relative_precision=0.0001):
        
        upper = interval_expr.nominal_value + interval_expr.std_dev
        lower = interval_expr.nominal_value - interval_expr.std_dev
        fwd_precision = precision_expr.std_dev
        
        
        if(upper - lower == 0.0):
            print(upper)
            print(lower)
            print("in_thing")
            targ_precision = relative_precision
        else:
            print(upper-lower)
            targ_precision = (upper-lower)*relative_precision

        """ This part should be fine to comment out, right?
        if not (fwd_precision <= targ_precision):
            raise Exception("cannot attain desired precision: forward prop=%f, target=%f\n  expr=%s"  \
            % (fwd_precision,targ_precision,precision_expr))
        """
        self.info[ident] = IntervalPrecRegistery.IntervalPrecInfo(lower=lower, upper=upper,precision=targ_precision, \
                                interval_expr=interval_expr, precision_expr=precision_expr)


        self.info[ident].check()
        return self.info[ident]

    def get_info(self,ident):
        return self.info[ident]

    def variables(self):
        return filter(lambda x: isinstance(x,str), self.info.keys())
 
    def expr_ids(self):
        return filter(lambda x: isinstance(x,int), self.info.keys())
        
    def __repr__(self):
        args = []
        for ident, info in self.info.items():
            args.append("%s %s" % (ident,info))
        return "\n".join(args)

def build_interval_symtbl(block):
    reg = IntervalPrecRegistery()
    for v in block.vars():
        if v.type.isType(RealType):
            lower,upper = v.type.interval
            reg.decl_info(v.name, lower, upper, v.type.prec)
        elif v.type.isType(DigitalType):
            lower, upper = v.type.interval
            reg.decl_info(v.name, lower, upper, v.type.prec)
    for p in block.params():
        if p.type.isType(RealType):
            lower,upper = p.type.interval
            reg.decl_info(p.name, lower, upper, p.type.prec)
    return reg

def propagate_expr(reg, e,rel_prec):
    
    print(e)
    if isinstance(e, Constant) or isinstance(e, Param):
        if(e.value != 0):
            lb = e.value - (abs(e.value)*rel_prec)
            ub = e.value + (abs(e.value)*rel_prec)
            info = reg.decl_info(e.ident, lb, ub, abs(ub - lb)*rel_prec)
            e.type = RealType(lower=info.lower, upper=info.upper, prec=info.precision)
        else:
            lb = -rel_prec/2
            ub = rel_prec/2
            info = reg.decl_info(e.ident, lb, ub, rel_prec)
            e.type = RealType(lower=info.lower, upper=info.upper, prec=info.precision)
    elif isinstance(e, MuxC):
        comp = e.children()
        propagate_expr(reg, comp[0], rel_prec)
        propagate_expr(reg, comp[1], rel_prec)
        propagate_expr(reg, comp[2], rel_prec)
        
        reg.decl_info(e.ident, min(comp[1].type.lower,comp[2].type.lower), max(comp[1].type.upper,comp[2].type.upper), min(comp[1].type.prec,comp[2].type.prec))
        e.type = RealType(lower=min(comp[1].type.lower,comp[2].type.lower), upper=max(comp[1].type.upper,comp[2].type.upper), prec=min(comp[1].type.prec,comp[2].type.prec))
    else:
        expr = e.sympy
        print("expr: {}".format(expr))
        vs = list(expr.free_symbols)
        print(vs)
        ival_args = list(map(lambda v: reg.get_info(v.name).interval_expr, vs))
        prec_args = list(map(lambda v: reg.get_info(v.name).precision_expr, vs))

        
        lambd = sympy.lambdify(vs,expr)
        ival_expr = lambd(*ival_args)
        prec_expr = lambd(*prec_args)

        print()

        info=reg.decl_sym_info(e.ident, interval_expr=ival_expr, precision_expr=prec_expr, relative_precision=rel_prec)
        e.type = RealType(lower=info.lower, upper=info.upper, prec=info.precision)

def real_type_from_expr(blk,expr,rel_prec=0.01):
    reg = build_interval_symtbl(blk)
    propagate_expr(reg,expr,rel_prec)
    info = reg.get_info(expr.ident)
    return RealType(lower=info.lower, upper=info.upper,prec=info.precision)



def compute_intervals_for_block(block, rel_prec):
    reg = build_interval_symtbl(block)
    for rel in block.relations():
        if isinstance(rel,VarAssign):
            for node in rel.rhs.nodes():

                propagate_expr(reg,node, rel_prec)
            
            info = reg.get_info(rel.rhs.ident)

            reg.decl_info(rel.ident,info.lower, info.upper, info.precision)
            #reg.decl_info(rel.lhs.name,info.lower,info.upper, info.precision) woah a bug with this
        elif isinstance(rel, Integrate):
            for node in rel.rhs.nodes():
                propagate_expr(reg, node, rel_prec)
            info = reg.get_info(rel.rhs.ident)
            reg.decl_info(rel.ident,info.lower, info.upper, info.precision)

        else:
            raise Exception("unsupported")
        
    return reg