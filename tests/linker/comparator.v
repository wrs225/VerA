

module comparator
(
  input clk,
  input reset,
  input sys_clk,
  input [10-1:0] p_voltage_real,
  input [10-1:0] n_voltage_real,
  output [1-1:0] out_digital
);

  reg [4-1:0] state_cycle_counter;
  reg [1-1:0] prev_sys_clk;
  reg [32-1:0] fsm;
  localparam fsm_init = 0;
  wire [13-1:0] truncR_0;
  wire [13-1:0] const_1;
  assign const_1 = 13'd4096;
  assign truncR_0 = const_1;
  wire [14-1:0] truncR_2;
  wire [15-1:0] toUsInt_3;
  wire [15-1:0] const_4;
  assign const_4 = 15'd0;
  assign toUsInt_3 = const_4;
  assign truncR_2 = toUsInt_3[11:0];
  assign out_digital = (fsm == 0)? truncR_0[12:12] : truncR_2[13:13];

  always @(posedge clk) begin
    prev_sys_clk <= sys_clk;
  end

  localparam fsm_1 = 1;

  always @(posedge clk) begin
    if(reset) begin
      fsm <= fsm_init;
    end else begin
      case(fsm)
        fsm_init: begin
          if((p_voltage_real > 10'd0) & (p_voltage_real <= n_voltage_real)) begin
            fsm <= fsm_1;
          end 
        end
        fsm_1: begin
          if((p_voltage_real > n_voltage_real) & (p_voltage_real <= 10'd512)) begin
            fsm <= fsm_init;
          end 
        end
      endcase
    end
  end


endmodule

