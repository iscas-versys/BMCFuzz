
/*verilator tracing_off*/
module GEN_w64_toggle(
  input clock,
  input reset,
  input [64 - 1: 0] valid
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
      if (valid[27]) begin
        v_cover_toggle(COVER_INDEX + 27);
      end
      if (valid[28]) begin
        v_cover_toggle(COVER_INDEX + 28);
      end
      if (valid[29]) begin
        v_cover_toggle(COVER_INDEX + 29);
      end
      if (valid[30]) begin
        v_cover_toggle(COVER_INDEX + 30);
      end
      if (valid[31]) begin
        v_cover_toggle(COVER_INDEX + 31);
      end
      if (valid[32]) begin
        v_cover_toggle(COVER_INDEX + 32);
      end
      if (valid[33]) begin
        v_cover_toggle(COVER_INDEX + 33);
      end
      if (valid[34]) begin
        v_cover_toggle(COVER_INDEX + 34);
      end
      if (valid[35]) begin
        v_cover_toggle(COVER_INDEX + 35);
      end
      if (valid[36]) begin
        v_cover_toggle(COVER_INDEX + 36);
      end
      if (valid[37]) begin
        v_cover_toggle(COVER_INDEX + 37);
      end
      if (valid[38]) begin
        v_cover_toggle(COVER_INDEX + 38);
      end
      if (valid[39]) begin
        v_cover_toggle(COVER_INDEX + 39);
      end
      if (valid[40]) begin
        v_cover_toggle(COVER_INDEX + 40);
      end
      if (valid[41]) begin
        v_cover_toggle(COVER_INDEX + 41);
      end
      if (valid[42]) begin
        v_cover_toggle(COVER_INDEX + 42);
      end
      if (valid[43]) begin
        v_cover_toggle(COVER_INDEX + 43);
      end
      if (valid[44]) begin
        v_cover_toggle(COVER_INDEX + 44);
      end
      if (valid[45]) begin
        v_cover_toggle(COVER_INDEX + 45);
      end
      if (valid[46]) begin
        v_cover_toggle(COVER_INDEX + 46);
      end
      if (valid[47]) begin
        v_cover_toggle(COVER_INDEX + 47);
      end
      if (valid[48]) begin
        v_cover_toggle(COVER_INDEX + 48);
      end
      if (valid[49]) begin
        v_cover_toggle(COVER_INDEX + 49);
      end
      if (valid[50]) begin
        v_cover_toggle(COVER_INDEX + 50);
      end
      if (valid[51]) begin
        v_cover_toggle(COVER_INDEX + 51);
      end
      if (valid[52]) begin
        v_cover_toggle(COVER_INDEX + 52);
      end
      if (valid[53]) begin
        v_cover_toggle(COVER_INDEX + 53);
      end
      if (valid[54]) begin
        v_cover_toggle(COVER_INDEX + 54);
      end
      if (valid[55]) begin
        v_cover_toggle(COVER_INDEX + 55);
      end
      if (valid[56]) begin
        v_cover_toggle(COVER_INDEX + 56);
      end
      if (valid[57]) begin
        v_cover_toggle(COVER_INDEX + 57);
      end
      if (valid[58]) begin
        v_cover_toggle(COVER_INDEX + 58);
      end
      if (valid[59]) begin
        v_cover_toggle(COVER_INDEX + 59);
      end
      if (valid[60]) begin
        v_cover_toggle(COVER_INDEX + 60);
      end
      if (valid[61]) begin
        v_cover_toggle(COVER_INDEX + 61);
      end
      if (valid[62]) begin
        v_cover_toggle(COVER_INDEX + 62);
      end
      if (valid[63]) begin
        v_cover_toggle(COVER_INDEX + 63);
      end
    end
  end
`endif
`endif
endmodule
