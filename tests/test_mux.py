import pythams.core.block as blocklib
from pythams.core.expr import *
import pythams.core.intervals as intervallib
import pythams.core.fixedpoint as fxplib
import pythams.core.integer as intlib 
import pythams.core.rtl as rtllib 

import matplotlib.pyplot as plt
from pymtl3 import *
import sys

from models.muxedblock import generate_block

def validate_model(blk,timestep,figname):

    in_digital = 0
    in_digital_arr = []
    out_analog_arr = []
    ts = []
    cycles_per_sec = round(1/timestep)
    max_cycles = 10*cycles_per_sec

    
    for t in range(max_cycles):
    
        values = blocklib.execute_block(blk, {"in_digital": in_digital})
        ts.append(t*timestep)
        out_analog_arr.append(values["out_analog"])
        in_digital_arr.append(in_digital)


    plt.plot(ts,in_digital_arr , label='in_digital')
    plt.plot(ts,out_analog_arr,  label='out_analog' )
    plt.legend(loc='best')
    plt.savefig(figname)
    plt.clf()

muxedblock_model = generate_block()


ival_reg = intervallib.compute_intervals_for_block(muxedblock_model, rel_prec = 0.01)

input("press any key to run simulation")
validate_model(muxedblock_model, 0.0001, "muxedblock_model.png")



