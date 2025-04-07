module MemRWHelper(
  input             r_enable,
  input      [63:0] r_index,
  output reg [63:0] r_data,
  input             w_enable,
  input      [63:0] w_index,
  input      [63:0] w_data,
  input      [63:0] w_mask,
  input             clock
);

`define RAM_ITEMS (2 * 1024 * 1024 * 1024) / 8 // 2^(28) [27:0] [27:3] [2:0]
`define RAM_DATA_WIDTH 64
`define RAM_ADDR_WIDTH $clog2(`RAM_ITEMS)
// reg [63:0] memory [0 : `RAM_SIZE / 8 - 1];
`define MAX_CACHE_LINES 16
`define MAX_CACHE_INDEX $clog2(`MAX_CACHE_LINES)
// 由于是2GiB内存 相当于只考虑r_index % RAM_ITEMS
reg [`MAX_CACHE_LINES-1:0] cache_valid = 0; // 有效位
reg [`MAX_CACHE_INDEX-1:0] cache_index = 0; // 未hit时写入的位置
reg [`RAM_DATA_WIDTH-1:0]  cache_data[0:`MAX_CACHE_LINES]; // 数据
reg [`RAM_ADDR_WIDTH-1:0]  cache_tag [0:`MAX_CACHE_LINES]; // 25位

// TODO: change cache tag to suitable for 2GiB memory address
(* keep *) rand reg [`RAM_DATA_WIDTH-1:0] rand_value;
wire [`MAX_CACHE_LINES-1:0] cache_hit;
wire hit;
// wire [`MAX_CACHE_INDEX-1:0] hit_index[0:`MAX_CACHE_LINES];
wire [`MAX_CACHE_INDEX-1:0] hit_line;
assign hit = |cache_hit;
generate
    genvar i;
    for (i = 0; i < `MAX_CACHE_LINES; i = i+1) begin: cache_hit_generate
        assign cache_hit[i] = cache_valid[i] && cache_tag[i] == r_index[`RAM_ADDR_WIDTH-1:0];
    end
endgenerate
assign hit_line = cache_hit[0] ? 0 :
                  cache_hit[1] ? 1 :
                  cache_hit[2] ? 2 :
                  cache_hit[3] ? 3 :
                  cache_hit[4] ? 4 :
                  cache_hit[5] ? 5 :
                  cache_hit[6] ? 6 :
                  cache_hit[7] ? 7 :
                  cache_hit[8] ? 8 :
                  cache_hit[9] ? 9 :
                  cache_hit[10]? 10:
                  cache_hit[11]? 11:
                  cache_hit[12]? 12:
                  cache_hit[13]? 13:
                  cache_hit[14]? 14:
                  cache_hit[15]? 15:
                                  0;

initial begin
    r_data = 64'h0;
end
always @(posedge glb_clk) begin
    if (r_enable) begin
        if (hit) begin
            r_data <= cache_data[hit_line];
        end
        else begin
            r_data <= rand_value;
            cache_data[cache_index] <= rand_value;
            cache_tag[cache_index]  <= r_index[`RAM_ADDR_WIDTH-1:0];
            cache_valid[cache_index] <= 1'b1;
        end
    end
    if (w_enable) begin
        if (hit) begin
            cache_data[hit_line] <= (w_data & w_mask) | (cache_data[hit_line] & ~w_mask);
        end
        else begin
            cache_data[cache_index] <= (w_data & w_mask) | (rand_value & ~w_mask);
            cache_tag[cache_index]  <= w_index[`RAM_ADDR_WIDTH-1:0];
            cache_valid[cache_index] <= 1'b1;
        end
    end
    if (r_enable || w_enable) begin
        cache_index <= cache_index + 1'b1;
    end
end


endmodule