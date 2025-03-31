
/*verilator tracing_off*/
module GEN_w27_toggle(
  input clock,
  input reset,
  input [27 - 1: 0] valid
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
      if (valid[16]) begin
        v_cover_toggle(COVER_INDEX + 16);
      end
      if (valid[17]) begin
        v_cover_toggle(COVER_INDEX + 17);
      end
      if (valid[18]) begin
        v_cover_toggle(COVER_INDEX + 18);
      end
      if (valid[19]) begin
        v_cover_toggle(COVER_INDEX + 19);
      end
      if (valid[20]) begin
        v_cover_toggle(COVER_INDEX + 20);
      end
      if (valid[21]) begin
        v_cover_toggle(COVER_INDEX + 21);
      end
      if (valid[22]) begin
        v_cover_toggle(COVER_INDEX + 22);
      end
      if (valid[23]) begin
        v_cover_toggle(COVER_INDEX + 23);
      end
      if (valid[24]) begin
        v_cover_toggle(COVER_INDEX + 24);
      end
      if (valid[25]) begin
        v_cover_toggle(COVER_INDEX + 25);
      end
      if (valid[26]) begin
        v_cover_toggle(COVER_INDEX + 26);
      end
    end
  end
`endif
`endif
endmodule
