import vera.core.block as blocklib
from vera.core.expr import *
import vera.core.intervals as intervallib
import vera.core.fixedpoint as fxplib
import vera.core.integer as intlib 
import vera.core.rtl as rtllib 

import matplotlib.pyplot as plt
from pymtl3 import *
import sys

from models.muxedblock import generate_block
from tqdm import tqdm

def validate_model(blk,timestep,figname):

    in_digital = 1
    in_digital_arr = []
    out_analog_arr = []
    ts = []
    cycles_per_sec = round(1/timestep)
    max_cycles = 10*cycles_per_sec

    
    for t in tqdm(range(max_cycles)):
        
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
input("press any key to run simulation")

ival_reg = intervallib.compute_intervals_for_block(muxedblock_model, rel_prec = 0.01)


validate_model(muxedblock_model, 0.0001, "muxedblock_model.png")



input("press any key to run simulation")
muxedblock_fp = fxplib.to_fixed_point(ival_reg,muxedblock_model)

validate_model(muxedblock_fp, 1, "muxedblock_fp.png")



input("press any key to run simulation")
muxedblock_int = intlib.to_integer(muxedblock_fp)
validate_model(muxedblock_int, 1, "muxedblock_int.png")

input("press any key to run simulation")
rtl_block = rtllib.RTLBlock(muxedblock_int, {})


if __name__ == "__main__":
    rtl_block.generate_verilog_src(sys.argv[1])
    rtl_block.generate_pymtl_wrapper()
    rtl_block.pymtl_sim_begin()