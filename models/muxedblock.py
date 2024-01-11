import pythams.core.block as blocklib
from pythams.core.expr import *
import pythams.core.intervals as intervallib
import pythams.core.fixedpoint as fxplib
import pythams.core.integer as intlib 
import pythams.core.rtl as rtllib 

def generate_block(input_voltage = 3.3, rel_prec = 0.0000001, timestep = 1e-4):
    
    scf = 40
    
    mux_out = blocklib.AMSBlock("muxed_output")
    #w = vco.decl_input(Real("w"))
    #out = vco.decl_output(Real("out"))


    in_digital = mux_out.decl_var("in_digital", kind=blocklib.VarKind.Input, type=DigitalType(nbits=1))
    out_analog = mux_out.decl_var("out_analog", kind=blocklib.VarKind.Output, type=RealType(lower=-3.3*scf,upper=3.3*scf,prec=rel_prec))
        
    mux_out.decl_relation(VarAssign(out_analog, Mux(in_digital, Constant(3.3), Constant(0.0))))
    
    return mux_out
