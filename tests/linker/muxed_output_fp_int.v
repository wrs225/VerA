

module muxed_output_fp_int
(
  input clk,
  input reset,
  input [1-1:0] in_digital,
  output [34-1:0] out_analog
);

  wire [34-1:0] padr_0;
  wire [13-1:0] padr_bits_1;
  assign padr_bits_1 = 0;
  wire [21-1:0] padl_2;
  wire [16-1:0] padl_bits_3;
  wire [16-1:0] mux_4;
  wire [16-1:0] padl_5;
  wire [15-1:0] padl_bits_6;
  wire [1-1:0] toSInt_7;
  assign toSInt_7 = 0;
  wire [15-1:0] toSInt_imm_8;
  wire [14-1:0] const_9;
  assign const_9 = 14'd6758;
  assign toSInt_imm_8 = { toSInt_7, const_9 };
  assign padl_bits_6 = toSInt_imm_8;
  assign padl_5 = { { 1{ padl_bits_6[14] } }, padl_bits_6 };
  wire [16-1:0] padr_10;
  wire [4-1:0] padr_bits_11;
  assign padr_bits_11 = 0;
  wire [12-1:0] padl_12;
  wire [9-1:0] padl_bits_13;
  wire [9-1:0] const_14;
  assign const_14 = 9'd0;
  assign padl_bits_13 = const_14;
  assign padl_12 = { { 3{ padl_bits_13[8] } }, padl_bits_13 };
  assign padr_10 = { padl_12, padr_bits_11 };
  assign mux_4 = (in_digital)? padl_5 : padr_10;
  assign padl_bits_3 = mux_4;
  assign padl_2 = { { 5{ padl_bits_3[15] } }, padl_bits_3 };
  assign padr_0 = { padl_2, padr_bits_1 };
  assign out_analog = padr_0;

endmodule

