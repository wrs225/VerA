
from .expr import Expression,VarType
from typing import ClassVar
from dataclasses import dataclass, field
import math
from fixedpoint import FixedPoint, FixedPointOverflowError
import sympy as sym
import copy

@dataclass(frozen=True)
class FixedPointType(VarType):
    fractional : int
    integer : int
    log_scale: int 
    signed:  bool
    type_name : ClassVar[str] = "fixed_point"

    def __post_init__(self):
        
        assert(self.integer >= 0)
        assert(self.fractional >= 0)

    @classmethod
    def from_integer_scale(cls,integer,log_scale,signed):
        if log_scale < 0:
            fractional = abs(log_scale)
        else:
            fractional = 0
        return FixedPointType(fractional=fractional,integer=integer, signed=signed, log_scale=log_scale)
        
    @classmethod
    def from_interval_precision(self,lower,upper,precision):
        is_signed = lower < 0.0

        #nvals = (max(abs(upper), abs(lower))+precision)/precision
        #Will changed this because there was a case when max(|upper|,|lower|) < precision^2 - precision
        nvals = (max(abs(upper),abs(lower)) / precision)

        total_bits = math.ceil(math.log2(nvals)) + 1
        scale_bits = math.floor(math.log2(precision))

        if scale_bits < 0:
            fractional = abs(scale_bits)
            integer = max(total_bits - fractional,0) + int( lower < 0)
        else:
            fractional = 0
            integer = total_bits + scale_bits + int( lower < 0)

        return FixedPointType(fractional=fractional,integer=integer,signed=is_signed, log_scale=scale_bits)

    # number fractional bits
    @property
    def scale(self):
        return 2**(self.log_scale)


    # number fractional bits
    @property
    def n(self):
        return self.n_fractional_bits

    # number integer bits 
    @property
    def m(self):
        return self.n_integer_bits

    @property
    def nbits(self):
        return self.n_fractional_bits + self.n_integer_bits

    @property
    def n_integer_bits(self):
        return self.integer + int(self.signed)

    @property
    def n_fractional_bits(self):
        return self.fractional


    def match(self,fpe):
        return fpe.integer == self.integer and \
            fpe.fractional == self.fractional and \
            fpe.signed == self.signed

    def typecast_value(self,value):
        assert(not value is None)
        return self.from_real(float(value))

    def typecheck_value(self,value):
        msg = "value=%f type=%s m=%d n=%d repr=(m=%s,n=%s,sgn=%s)" % (value, self, self.m, self.n, value.m, value.n, value.signed)
        assert isinstance(value, FixedPoint)
        if not self.signed and value.signed:
            raise Exception("mismatch on sign type=%s value=%s\n  %s" % (self.signed, value.signed,msg))

        if self.m != value.m:
            raise Exception("integer size mismatch type=%d value=%d\n   %s" % (self.m,value.m,msg))

        if self.n != value.n:
            raise Exception("fractional size mismatch type=%d value=%d   %s" % (self.n,value.n,msg))


    def to_real(self,value):
        if isinstance(value,FixedPoint):
            return float(value)
        else:
            return value


    def from_real(self,value):
        if isinstance(value,FixedPoint):
            nvalue = float(value)
        else:
            nvalue = int(round(float(value)/self.scale))*self.scale

        fpn = FixedPoint(nvalue, m=self.m, n=self.n, signed=self.signed, mismatch_alert='ignore')
        self.typecheck_value(fpn)
        if abs(float(fpn) - value) > self.scale:
            print("[WARN] precision requirement violated: orig-value=%f, fp-value=%f, scale=%f" % (value,float(fpn),self.scale))

        return fpn


@dataclass
class FPOp(Expression):
    expr : Expression

    def children(self):
        return [self.expr]


@dataclass
class FPTruncFrac(FPOp):
    nbits : int
    op_name : ClassVar[str]= "truncF"

    @property
    def type(self):
        fpt = self.expr.type
        assert(fpt.fractional - self.nbits >= 0)
        return FixedPointType(integer=fpt.integer, fractional=fpt.fractional - self.nbits, \
                            log_scale=fpt.log_scale + self.nbits, \
                            signed=fpt.signed)
 
    def execute(self,args):
        value = FixedPoint(self.expr.execute(args), mismatch_alert='ignore')
        new_bitvec= bin(value.bits >> self.nbits)

        new_value = FixedPoint(new_bitvec, n=self.expr.type.n - self.nbits, m=self.expr.type.m, signed=self.expr.type.signed, mismatch_alert='ignore')
        
        self.type.typecheck_value(new_value)
        if abs(self.expr.type.to_real(value) - self.type.to_real(new_value)) > self.type.scale:
            raise Exception("Fractional truncate produced incorrect value: original=%f, truncated=%f" % (float(value), float(new_value)))


        return new_value

    def pretty_print(self):
        return "truncF(%s,%d)" % (self.expr.pretty_print(), self.nbits)




@dataclass
class FPExtendFrac(FPOp):
    nbits : int
    op_name : ClassVar[str]= "extF"

    @property
    def type(self):
        fpt = self.expr.type
        return FixedPointType(integer=fpt.integer, fractional=fpt.fractional + self.nbits, \
                            log_scale=fpt.log_scale - self.nbits, \
                            signed=fpt.signed)

 
    def execute(self,args):
        value = FixedPoint(self.expr.execute(args), mismatch_alert='ignore')
        new_bitvec=bin(value.bits << self.nbits)

        new_value = FixedPoint(new_bitvec, n=self.expr.type.n + self.nbits, m=self.expr.type.m, signed=self.expr.type.signed, mismatch_alert='ignore')
        self.type.typecheck_value(new_value)
        if abs(self.expr.type.to_real(value) - self.expr.type.to_real(new_value)) > 1e-6:
            raise Exception("Fractional extend produced incorrect value")

        return new_value

    def pretty_print(self):
        return "xtendF(%s,%d)" % (self.expr.pretty_print(), self.nbits)

@dataclass
class FPExtendInt(FPOp):
    nbits : int
    op_name : ClassVar[str]= "extI"

    @property
    def type(self):
        fpt = self.expr.type
        return FixedPointType.from_integer_scale(integer= fpt.integer + self.nbits, log_scale=fpt.log_scale, signed=fpt.signed)
   
    def pretty_print(self):
        return "xtendInt(%s,%d)" % (self.expr.pretty_print(), self.nbits)

    #Added by will
    def execute(self, args):
        value = float(self.expr.execute(args))
        new_value = FixedPoint( value, n=self.expr.type.n , m=self.expr.type.m + self.nbits, signed=self.expr.type.signed, mismatch_alert='ignore')
        self.type.typecheck_value(new_value)
        if abs(self.expr.type.to_real(value) - self.expr.type.to_real(new_value)) > 1e-6:
            raise Exception("Fractional extend produced incorrect value")
        return new_value
    
#This feels... risky -will
@dataclass
class FPTruncInt(FPOp):
    nbits : int
    op_name : ClassVar[str]= "TruncI"

    @property
    def type(self):
        fpt = self.expr.type
        return FixedPointType.from_integer_scale(integer= fpt.integer - self.nbits, log_scale=fpt.log_scale, signed=fpt.signed)
    
    #Added by will
    def execute(self, args):

        value = float(self.expr.execute(args))

        new_value = FixedPoint( value, n=self.type.n , m=self.type.m, signed=self.type.signed, mismatch_alert='ignore')

        self.type.typecheck_value(new_value)
        #If we are clamping the value here, I believe we should not care because the difference should be large.
        """
        if abs(self.expr.type.to_real(value) - self.expr.type.to_real(new_value)) > 1e-6:
            print(abs(self.expr.type.to_real(value) - self.expr.type.to_real(new_value)))
            raise Exception("Fractional extend produced incorrect value")
        """
        return new_value
        
    def pretty_print(self):
        return "fptruncint(%s)" % (self.expr.pretty_print())
    




@dataclass
class FPToSigned(FPOp):
    expr : Expression
    op_name : ClassVar[str]= "toSgn"

    @property
    def type(self):
        fpt = self.expr.type
        if not fpt.signed:
            
            fpt = copy.deepcopy(self.expr.type)
            return FixedPointType.from_integer_scale(integer=fpt.integer,log_scale=fpt.log_scale,signed=True)
        else:
            return fpt
 
    def execute(self,args):
        value = self.expr.execute(args)
        new_value = FixedPoint(float(value),n=self.expr.type.n , m=self.expr.type.m + 1, signed=True, mismatch_alert='ignore')
        self.type.typecheck_value(new_value)
        if abs(self.expr.type.to_real(value) - self.expr.type.to_real(new_value)) > 1e-6:
            raise Exception("Sign extend produced incorrect value")


        return new_value


    def pretty_print(self):
        return "toSigned(%s)" % (self.expr.pretty_print())

@dataclass
class FPToUnsigned(FPOp): #FP Operation,
    expr : Expression
    op_name : ClassVar[str]= "toUSgn"

    @property
    def type(self):
        fpt = self.expr.type
        return FixedPointType.from_integer_scale(integer=fpt.integer,log_scale=fpt.log_scale,signed=False)


    
    def pretty_print(self):
        return "fptounsigned(%s)" % (self.expr.pretty_print())
    
    def execute(self,args):
        value = float(self.expr.execute(args))

        new_value = FixedPoint(value,n=self.expr.type.n, m=self.expr.type.m - 1, signed=False, mismatch_alert='ignore')
        
        self.type.typecheck_value(new_value)
        if abs(self.expr.type.to_real(value) - self.expr.type.to_real(new_value)) > 1e-6:
            raise Exception("Sign extend produced incorrect value")
        
        return new_value
    
@dataclass
class FpQuotient(Expression):
    lhs: Expression
    rhs: Expression
    type  = None
    op_name : ClassVar[str]= "fpdiv"

    def children(self):
        return [self.lhs, self.rhs]

    @property
    def sympy(self) -> sym.Expr:
        return self.lhs.sympy / self.rhs.sympy

    @property
    def variables(self) -> "Set[Real]":
        return self.lhs.variables | self.rhs.variables
    
    def pretty_print(self):
        return "({}) / ({})".format(self.lhs.pretty_print(), self.rhs.pretty_print())
    
    
    def execute(self, args):
        result_float = float(self.lhs.execute(args)) / float(self.rhs.execute(args)) 

        result = FixedPoint(result_float, m=self.lhs.type.m + self.rhs.type.n + self.rhs.type.m + bool(self.rhs.type.signed or self.lhs.type.signed), n=self.lhs.type.n, signed=self.type.signed, mismatch_alert='ignore')

        tc_result = self.type.typecast_value(result)
        self.type.typecheck_value(tc_result)
        return tc_result

@dataclass
class FpReciprocal(Expression):
    expr: Expression
    type = None
    op_name : ClassVar[str] = 'fprecip'

    def children(self):
        [self.expr]
    
    def sympy(self) -> sym.Expr:
        return 1 / self.expr.sympy
    
    @property
    def variables(self) -> "Set[Real]":
        return self.expr
    
    def pretty_print(self):
        return " 1 / ( {} )".format(self.expr.pretty_print())

    def execute(self, args):
        fxp_expr = self.expr.execute(args)
        result_float = (1 / float(fxp_expr)) #1/fp_expr

        result = FixedPoint(result_float, m = self.expr.type.n + int(self.expr.type.signed), n = self.expr.type.m, signed = self.expr.type.signed, mismatch_alert='ignore')

        tc_result = self.type.typecast_value(result)
        self.type.typecheck_value(tc_result)
        return tc_result

@dataclass
class FPTruncL(FPOp): 
    nbits: int
    op_name : ClassVar[str] = 'fpTruncL'

    @property
    def type(self):
        fpt = self.expr.type
        overflow = fpt.integer - self.nbits
        if(overflow >= 0 ):
            integer = overflow
        else:
            integer = 0
            fractional = -overflow
        restype = FixedPointType.from_integer_scale(integer=integer,log_scale=fpt.log_scale,signed=fpt.signed)

        return restype
    
    def pretty_print(self):
        return "fpTruncL(%s)" % (self.expr.pretty_print())
    
    def execute(self,args):
        value = self.expr.execute(args)
        rettype = FixedPoint(float(value),n=self.type.n, m=self.type.m, signed=self.type.signed, mismatch_alert='ignore')

        return rettype
    


@dataclass
class  FPIncreaseScale(FPOp):
    nbits: int
    op_name : ClassVar[str] = 'fpIncScale'

    @property
    def type(self):
        return FixedPointType.from_integer_scale(integer=self.expr.type.integer, log_scale =self.expr.type.log_scale + self.nbits, signed=self.expr.type.signed)
    
    def pretty_print(self):
        return "{}({})".format(self.op_name, self.expr.pretty_print())
    
    def execute(self,args):
        return self.expr.execute(args)