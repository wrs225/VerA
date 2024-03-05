

module a_simple_module
(
  output wire output_digital,
  output [34-1:0] valuesfsdafs,
  input wire [10-1:0] p_voltage_real
);

  real a_cool_variable;
  assign valuesfsdafs = a_cool_variable;
  reg [15:0] a_cool_register;

  comparator cool_module_instance
  (
    .clk(),
    .reset(),
    .sys_clk(),
    .p_voltage_real(asfgasdfg),
    .n_voltage_real(),
    .out_digital()
  );


  muxed_output_fp_int cool_module_instance2
  (
    .clk(),
    .reset(),
    .in_digital(),
    .out_analog(a_cool_variable)
  );


endmodule

