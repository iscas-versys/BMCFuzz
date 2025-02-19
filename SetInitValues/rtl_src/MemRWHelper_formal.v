`define DISABLE_DIFFTEST_RAM_DPIC
`ifdef SYNTHESIS
  `define DISABLE_DIFFTEST_RAM_DPIC
`endif

`ifndef DISABLE_DIFFTEST_RAM_DPIC
import "DPI-C" function longint difftest_ram_read(input longint rIdx);
`endif // DISABLE_DIFFTEST_RAM_DPIC


`ifndef DISABLE_DIFFTEST_RAM_DPIC
import "DPI-C" function void difftest_ram_write
(
  input  longint index,
  input  longint data,
  input  longint mask
);
`endif // DISABLE_DIFFTEST_RAM_DPIC

module MemRWHelper(
  
input             r_enable,
input      [63:0] r_index,
output reg [63:0] r_data,

  
input         w_enable,
input  [63:0] w_index,
input  [63:0] w_data,
input  [63:0] w_mask,

  input clock
);
initial begin
    r_data = 64'h0;
end
  
`ifdef DISABLE_DIFFTEST_RAM_DPIC
`ifdef PALLADIUM
  initial $ixc_ctrl("tb_import", "$display");
`endif // PALLADIUM

// 2GB memory
`define RAM_SIZE (2 * 1024 * 1024 * 1024)
reg [63:0] memory [0 : `RAM_SIZE / 8 - 1];

`define MEM_TARGET memory



`endif // DISABLE_DIFFTEST_RAM_DPIC

  always @(posedge clock) begin
    
`ifndef DISABLE_DIFFTEST_RAM_DPIC
if (r_enable) begin
  r_data <= difftest_ram_read(r_index);
end
`else
if (r_enable) begin
  r_data <= `MEM_TARGET[r_index];
end
`endif // DISABLE_DIFFTEST_RAM_DPIC

    
`ifndef DISABLE_DIFFTEST_RAM_DPIC
if (w_enable) begin
  difftest_ram_write(w_index, w_data, w_mask);
end
`else
if (w_enable) begin
  `MEM_TARGET[w_index] <= (w_data & w_mask) | (`MEM_TARGET[w_index] & ~w_mask);
end
`endif // DISABLE_DIFFTEST_RAM_DPIC

  end
endmodule
     