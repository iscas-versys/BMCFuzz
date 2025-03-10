module FormalTop;
(* gclk *) wire gbl_clk;
wire clock;
wire reset;
wire [63:0] difftest_exit;
wire [63:0] difftest_step;
wire difftest_perfCtrl_clean;
wire difftest_perfCtrl_dump;
wire [63:0] difftest_logCtrl_begin;
wire [63:0] difftest_logCtrl_end;
wire [63:0] difftest_logCtrl_level;
wire difftest_uart_out_valid;
wire [7:0] difftest_uart_out_ch;
wire difftest_uart_in_valid;
wire [7:0] difftest_uart_in_ch;

reg reg_reset = 1'b1;
always @(posedge gbl_clk) begin
  if (reg_reset) begin
    reg_reset <= 1'b0;
  end
end

assign clock = gbl_clk;
assign reset = reg_reset;
assign difftest_perfCtrl_clean = 1'b0;
assign difftest_perfCtrl_dump = 1'b0;
assign difftest_logCtrl_begin = 64'h0;
assign difftest_logCtrl_end = 64'h0;
assign difftest_logCtrl_level = 64'h0;
assign difftest_uart_in_ch = 8'h0;

SimTop dut(
  .clock,
  .reset,
  .difftest_exit,
  .difftest_step,
  .difftest_perfCtrl_clean,
  .difftest_perfCtrl_dump,
  .difftest_logCtrl_begin,
  .difftest_logCtrl_end,
  .difftest_logCtrl_level,
  .difftest_uart_out_valid,
  .difftest_uart_out_ch,
  .difftest_uart_in_valid,
  .difftest_uart_in_ch
);
endmodule