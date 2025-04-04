
/*verilator tracing_off*/
module GEN_w2_toggle(
  input clock,
  input reset,
  input [2 - 1: 0] valid
);
  parameter COVER_TOTAL = 28338;
  parameter COVER_INDEX;
`ifndef SYNTHESIS
`ifdef DIFFTEST
  import "DPI-C" function void v_cover_toggle (
    longint cover_index
  );
  always @(posedge gbl_clk) begin
    if (!reset) begin
            if (valid[0]) begin
        v_cover_toggle(COVER_INDEX + 0);
      end
      if (valid[1]) begin
        v_cover_toggle(COVER_INDEX + 1);
      end
    end
  end
`endif
`endif
endmodule
