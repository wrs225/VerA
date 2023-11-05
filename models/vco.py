import pythams.core.block as blocklib
from pythams.core.expr import *
import pythams.core.intervals as intervallib
import pythams.core.fixedpoint as fxplib
import pythams.core.integer as intlib 
import pythams.core.rtl as rtllib 

def generate_block(input_voltage = 3.3, rel_prec = 0.0000001, timestep = 1e-4):
    
    scf = 40
    
    vco = blocklib.AMSBlock("vco")
    #w = vco.decl_input(Real("w"))
    #out = vco.decl_output(Real("out"))
    
    gain = vco.decl_param("gain",Constant(0.75))
    d    = vco.decl_param("damping_resistance",Constant(0.0036))

    w = vco.decl_var("w", kind=blocklib.VarKind.Input, type=RealType(0,3.3,prec=rel_prec)) #total kludge to get the product lower above 0.00
    x = vco.decl_var("x", kind=blocklib.VarKind.StateVar, type=RealType(lower=-3.3*scf,upper=3.3*scf,prec=rel_prec))
    v = vco.decl_var("v", kind=blocklib.VarKind.StateVar, type=RealType(lower=-3.3*scf,upper=3.3*scf,prec=rel_prec))

    out = vco.decl_var("out", kind=blocklib.VarKind.Output, type=x.type)
    dvdt = vco.decl_var("dvdt", kind=blocklib.VarKind.Transient,  \
            type=intervallib.real_type_from_expr(vco, -(gain * w * w * gain)*(x), rel_prec=rel_prec))
    dxdt = vco.decl_var("dxdt", kind=blocklib.VarKind.Transient, \
            type=intervallib.real_type_from_expr(vco, v, rel_prec=rel_prec))
    
    expr = VarAssign(dvdt, -(gain * w * w * gain)*(x))

    vco.decl_relation(expr)
    vco.decl_relation(VarAssign(dxdt, v))
    vco.decl_relation(VarAssign(out, x))
    vco.decl_relation(Integrate(v, dvdt, timestep=timestep))
    vco.decl_relation(Integrate(x, dxdt, timestep=timestep))
    
    return vco
