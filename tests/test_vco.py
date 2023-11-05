import pythams.core.block as blocklib
from pythams.core.expr import *
import pythams.core.intervals as intervallib
import pythams.core.fixedpoint as fxplib
import pythams.core.integer as intlib 
import pythams.core.rtl as rtllib 

import matplotlib.pyplot as plt
from pymtl3 import *
import sys

sys.path.insert(0, '../models')
import vco as vco

def validate_model(blk,timestep,figname):
    print(blk)
    xi,vi = 3.3,0.0
    xs = []
    vs = []
    ts = []
    cycles_per_sec = round(1/timestep)
    max_cycles = 10*cycles_per_sec
    for t in range(max_cycles):
    
        values = blocklib.execute_block(blk,{"w":3.3, "x": xi, "v": vi})
        ts.append(t*timestep)
        xs.append(xi)
        vs.append(vi)


        
        xi = values["x"]
        vi = values["v"]

    
    print(len(vs))
    xs.append(xi)
    vs.append(vi)
    ts.append(max_cycles*timestep)

    plt.plot(ts,xs, label='xs')
    plt.plot(ts,vs, label='vs')
    plt.legend(loc='best')
    plt.savefig(figname)
    plt.clf()


def validate_pymtl_model(rtlblk,timestep,figname):
    outs = []
    ts = []
    cycles_per_sec = round(1/timestep)
    max_cycles = 30*cycles_per_sec
    for t in range(max_cycles):
        values = rtlblk.pymtl_sim_tick({"w":Bits(rtlblk.block.get_var('w').type.nbits, v=rtlblk.scale_value_to_int(0.999,rtlblk.block.get_var('w').type))})
        ts.append(t*timestep)
        outi = values["out"]
        outs.append(rtlblk.scale_value_to_real(outi, rtlblk.block.get_var('out').type))

   

    plt.plot(ts,outs)
    plt.show()
    #plt.savefig(figname)
    #plt.clf()


block = vco.generate_block()
ival_reg = intervallib.compute_intervals_for_block(block,rel_prec=0.000001)
print("------ Real-valued AMS Block -----")
print(block)
print("\n")
input("press any key to run simulation..")
validate_model(block, 1e-4, "orig_dynamics.png")

print(block.relations())

fp_block = fxplib.to_fixed_point(ival_reg, block)
print("------ Fixed Point AMS Block -----")
print(fp_block)
print("\n")
input("press any key to run simulation..")
validate_model(fp_block, 1e-4, "fp_dynamics.png")

print(fp_block.vars())
for i in fp_block.relations():
    print(i.pretty_print())

#raise Exception


int_block = intlib.to_integer(fp_block)
print("------ Integer AMS Block -----")
print(int_block)
print("\n")
input("press any key to run simulation..")
validate_model(int_block, 1e-4, "int_dynamics.png")

for i in int_block.relations():
    print(i.pretty_print())

for v in int_block.vars():
    print(v)


  
rtl_block = rtllib.RTLBlock(int_block, {'x':0.79, 'v':0.00})

rtl_block.generate_verilog_src("./")
rtl_block.generate_pymtl_wrapper()
rtl_block.pymtl_sim_begin()
validate_pymtl_model(rtl_block,timestep,"rtl_dynamics.png")