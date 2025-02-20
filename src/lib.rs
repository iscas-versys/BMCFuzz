/**
 * Copyright (c) 2023 Institute of Computing Technology, Chinese Academy of Sciences
 * xfuzz is licensed under Mulan PSL v2.
 * You can use this software according to the terms and conditions of the Mulan PSL v2.
 * You may obtain a copy of Mulan PSL v2 at:
 *          http://license.coscl.org.cn/MulanPSL2
 * THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
 * EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
 * MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
 * See the Mulan PSL v2 for more details.
 */
mod coverage;
mod fuzzer;
mod harness;
mod monitor;
// mod csr_transition;

use clap::Parser;

use std::env;

#[derive(Parser, Default, Debug)]
struct Arguments {
    // Fuzzer options
    #[clap(default_value_t = false, short, long)]
    fuzzing: bool,
    #[clap(default_value_t = String::from("llvm.branch"), short, long)]
    coverage: String,
    #[clap(default_value_t = false, short, long)]
    verbose: bool,
    #[clap(long)]
    max_iters: Option<u64>,
    #[clap(long)]
    max_runs: Option<u64>,
    #[clap(default_value_t = false, long)]
    random_input: bool,
    #[clap(default_value_t = String::from("./corpus"), long)]
    corpus_input: String,
    #[clap(long)]
    corpus_output: Option<String>,
    #[clap(default_value_t = false, long)]
    continue_on_errors: bool,
    #[clap(default_value_t = false, long)]
    save_errors: bool,
    #[clap(default_value_t = -1.0, long)]
    formal_cover_rate: f64,
    #[clap(default_value_t = false, long)]
    insert_nop: bool,
    #[clap(default_value_t = false, long)]
    only_fuzz: bool,

    // Run options
    #[clap(default_value_t = 1, long)]
    repeat: usize,
    #[clap(default_value_t = false, long)]
    auto_exit: bool,
    extra_args: Vec<String>,
}

#[no_mangle]
fn main() -> i32 {
    let args = Arguments::parse();

    let mut workloads: Vec<String> = Vec::new();
    let mut emu_args: Vec<String> = Vec::new();

    let mut is_emu = false;
    for arg in args.extra_args {
        if arg.starts_with("-") {
            is_emu = true;
        }

        if is_emu {
            emu_args.push(arg);
            // println!("{:?}", emu_args);
        } else {
            workloads.push(arg);
        }
    }

    println!("set_sim_env Begin\n");
    harness::set_sim_env(args.coverage, args.verbose, args.max_runs, emu_args);
    println!("set_sim_env End\n");
    let mut has_failed = 0;

    println!("workloads.len():{}", workloads.len());
    if workloads.len() > 0 {
        for _ in 0..args.repeat {
            let ret = harness::sim_run_multiple(&workloads, args.auto_exit);
            if ret != 0 {
                has_failed = 1;
                if args.auto_exit {
                    return ret;
                }
            }
        }
        // coverage::cover_display();
        if !args.fuzzing {
            let noop_home = env::var("NOOP_HOME").unwrap();
            let cover_points_output = format!("{}/tmp/sim_run_cover_points.csv", noop_home);
            harness::store_cover_points(cover_points_output.to_string());
        }
    }

    if args.fuzzing {
        let corpus_input = if args.corpus_input == "random" {
            None
        } else {
            Some(args.corpus_input)
        };
        println!("random_input: {:?}", args.random_input);
        println!("max_iters: {:?}", args.max_iters);
        println!("corpus_input: {:?}", corpus_input);
        println!("corpus_output: {:?}", args.corpus_output);
        println!("continue_on_errors: {:?}", args.continue_on_errors);
        println!("save_errors: {:?}", args.save_errors);
        println!("formal_cover_rate: {:?}", args.formal_cover_rate);
        println!("insert nop: {:?}", args.insert_nop);
        harness::set_formal_cover_rate(args.formal_cover_rate);
        harness::set_insert_nop(args.insert_nop);
        harness::set_only_fuzz(args.only_fuzz);
        harness::set_cover_points();
        if corpus_input.is_some() {
            harness::set_corpus_num(corpus_input.clone().unwrap());
        }
        fuzzer::run_fuzzer(
            args.random_input,
            args.max_iters,
            corpus_input,
            args.corpus_output,
            args.continue_on_errors,
            args.save_errors,
        );
    }

    return has_failed;
}
