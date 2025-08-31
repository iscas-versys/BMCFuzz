
`ifndef SYNTHESIS
import "DPI-C" function void sd_setaddr(input int addr);
import "DPI-C" function void sd_read(output int data);
`endif // SYNTHESIS

module SDCardHelper (
  input clock,
  input io_setAddr,
  input [31:0] io_addr,
  input io_ren,
  output reg [31:0] io_data
);

`ifndef SYNTHESIS
  always@(negedge clock) begin
    if (io_ren) sd_read(io_data);
  end
  always@(posedge clock) begin
    if (io_setAddr) sd_setaddr(io_addr);
  end
`endif // SYNTHESIS

endmodule
     
