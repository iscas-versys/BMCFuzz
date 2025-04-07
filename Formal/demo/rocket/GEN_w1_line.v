
/*verilator tracing_off*/
module GEN_w1_line(
  input clock,
  input reset,
  input valid
);
  parameter COVER_TOTAL = 1358;
  parameter COVER_INDEX;
`ifndef SYNTHESIS
`ifdef DIFFTEST
  import "DPI-C" function void v_cover_line (
    longint cover_index
  );
  always @(posedge gbl_clk) begin
    if (!reset && valid) begin
      v_cover_line(COVER_INDEX);
    end
  end
`endif
`endif
endmodule
