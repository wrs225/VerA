`include "comparator.v"
`include "muxed_output_fp_int.v"

module a_simple_module
(

    output wire output_digital,
    output real valuesfsdafs,
    input wire [10-1:0] p_voltage_real
);

real a_cool_variable;

assign valuesfsdafs = a_cool_variable;

reg [15:0] a_cool_register; 

/*
module comparator
(
  input clk,
  input reset,
  input sys_clk,
  input [10-1:0] p_voltage_real,
  input [10-1:0] n_voltage_real,
  output [1-1:0] out_digital
);
Create instance with all ports present but not connected to anything
*/
comparator cool_module_instance (
    .clk(),
    .reset(),
    .sys_clk(),
    .p_voltage_real(asfgasdfg),
    .n_voltage_real(),
    .out_digital()
);

/*module muxed_output_fp_int
(
  input clk,
  input reset,
  input [1-1:0] in_digital,
  output [34-1:0] out_analog
); */
muxed_output_fp_int cool_module_instance2 (
    .clk(),
    .reset(),
    .in_digital(),
    .out_analog(a_cool_variable)
);




endmodule