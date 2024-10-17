
/*verilator tracing_off*/
module GEN_w16_toggle(
  input clock,
  input reset,
  input [16 - 1: 0] valid
);
  parameter COVER_TOTAL = 11747;
  parameter COVER_INDEX;
`ifndef SYNTHESIS
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
      if (valid[5]) begin
        v_cover_toggle(COVER_INDEX + 5);
      end
      if (valid[6]) begin
        v_cover_toggle(COVER_INDEX + 6);
      end
      if (valid[7]) begin
        v_cover_toggle(COVER_INDEX + 7);
      end
      if (valid[8]) begin
        v_cover_toggle(COVER_INDEX + 8);
      end
      if (valid[9]) begin
        v_cover_toggle(COVER_INDEX + 9);
      end
      if (valid[10]) begin
        v_cover_toggle(COVER_INDEX + 10);
      end
      if (valid[11]) begin
        v_cover_toggle(COVER_INDEX + 11);
      end
      if (valid[12]) begin
        v_cover_toggle(COVER_INDEX + 12);
      end
      if (valid[13]) begin
        v_cover_toggle(COVER_INDEX + 13);
      end
      if (valid[14]) begin
        v_cover_toggle(COVER_INDEX + 14);
      end
      if (valid[15]) begin
        v_cover_toggle(COVER_INDEX + 15);
      end
    end
  end
`endif
endmodule
