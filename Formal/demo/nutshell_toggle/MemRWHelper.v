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
  // reg [63:0] memory [0 : `RAM_SIZE / 8 - 1];
  `define MAX_LINES 8
  // 由于是2GiB内存 相当于只考虑r_index % RAM_ITEMS
  // 直接相联缓存：最多 8 行
  reg [63:0] cache_data [0:`MAX_LINES]; // 数据
  reg [24:0] cache_tag  [0:`MAX_LINES]; // 25位
  reg        cache_valid[0:`MAX_LINES]; // 有效位

  // TODO: change cache tag to suitable for 2GiB memory address
  (* keep *) rand reg [63:0] rand_value;
  wire [2:0] h_index_r = r_index[2:0];
  wire [2:0] h_index_w = w_index[2:0];
  // 初始化缓存
  integer i;
  initial begin
    for (i = 0; i < `MAX_LINES; i = i + 1) begin
      cache_data[i] = 64'b0;
      cache_tag[i]  = 24'b0;
      cache_valid[i] = 1'b0;
    end
    r_data = 64'h0;
  end


  always @(posedge glb_clk) begin
    if (r_enable) begin
      // 检查缓存是否命中
      if (cache_valid[h_index_r] && cache_tag[h_index_r] == r_index[27:3]) begin
        r_data <= cache_data[h_index_r]; // 缓存命中，返回缓存数据
      end else begin
        r_data <= rand_value; // 缓存未命中，返回随机值
        // 将随机值存入缓存
        cache_data[h_index_r] <= rand_value;
        cache_tag[h_index_r]  <= r_index[27:3];
        cache_valid[h_index_r] <= 1'b1;
      end
    end
    if (w_enable) begin
      // 更新缓存
      cache_data[h_index_w] <= (w_data & w_mask) | (cache_data[h_index_w] & ~w_mask);
      cache_tag[h_index_w]  <= w_index[27:3];
      cache_valid[h_index_w] <= 1'b1;
    end
  end

endmodule