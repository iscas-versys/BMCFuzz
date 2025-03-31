
/*verilator tracing_off*/
module GEN_w5_toggle(
  input clock,
  input reset,
  input [5 - 1: 0] valid
);
  parameter COVER_TOTAL = 10906;
  parameter COVER_INDEX;
`ifndef SYNTHESIS
`ifdef DIFFTEST
  import "DPI-C" function void v_cover_toggle (
    longint cover_index
  );
  always @(posedge clock) begin
    if (!reset) begin
            if (valid[0]) begin
        v_cover_toggle(COVER_INDEX + 0);
      end
      if (valid[1]) begin
        v_cover_toggle(COVER_INDEX + 1);
      end
      if (valid[2]) begin
        v_cover_toggle(COVER_INDEX + 2);
      end
      if (valid[3]) begin
        v_cover_toggle(COVER_INDEX + 3);
      end
      if (valid[4]) begin
        v_cover_toggle(COVER_INDEX + 4);
      end
    end
  end
`endif
`endif
endmodule
