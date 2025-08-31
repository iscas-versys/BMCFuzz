
`ifdef SYNTHESIS
  `define DISABLE_DIFFTEST_FLASH_DPIC
`endif // SYNTHESIS
`ifndef DISABLE_DIFFTEST_FLASH_DPIC
import "DPI-C" function void flash_read
(
  input int unsigned addr,
  output longint unsigned data
);
`endif // DISABLE_DIFFTEST_FLASH_DPIC

module FlashHelper (
  input clock,
  input r_en,
  input [31:0] r_addr,
  output reg [63:0] r_data
);

`ifndef DISABLE_DIFFTEST_FLASH_DPIC
  always @(posedge clock) begin
    if (r_en) flash_read(r_addr, r_data);
  end
`else
`ifdef PALLADIUM
  initial $ixc_ctrl("tb_import", "$display");
`endif // PALLADIUM
  // 512K entries. 4MB size.
  `define FLASH_SIZE (4 * 1024 * 1024)
  reg [7:0] flash_mem [0 : `FLASH_SIZE - 1];

  for (genvar i = 0; i < 8; i++) begin
    always @(posedge clock) begin
      if (r_en) r_data[8 * i + 7 : 8 * i] <= flash_mem[r_addr + i];
    end
  end

  reg [7:0] flash_initval [0:11]; // Use when flash is not specified

  initial begin
      /** no specified flash_path, use defualt 3 instructions **/
      // addiw   t0,zero,1
      // slli    to,to,  0x1f
      // jr      t0
      // Used for pc = 0x8000_0000
      // flash_mem[0] = 64'h01f292930010029b
      // flash_mem[1] = 64'h00028067
      flash_initval = {8'h9b, 8'h02, 8'h10, 8'h00, 8'h93, 8'h92, 8'hf2, 8'h01, 8'h67, 8'h80, 8'h02, 8'h00};
      for (integer i = 0; i < 12; i = i + 1) begin
          flash_mem[i] = flash_initval[i];
      end
  end
`endif // DISABLE_DIFFTEST_FLASH_DPIC

endmodule
     
