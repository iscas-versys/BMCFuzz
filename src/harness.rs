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
extern crate libc;
extern crate rand;

use std::ffi::CString;
// use std::io::{self, Write};

use crate::coverage::*;
use crate::monitor::store_testcase;

use libafl::prelude::*;
use libc::*;

// use std::fs::File;
// use std::os::unix::io::AsRawFd; // 用于获取文件的文件描述符
use csv::{Writer, Reader};

extern "C" {
    pub fn sim_main(argc: c_int, argv: *const *const c_char) -> c_int;

    pub fn get_cover_number() -> c_uint;

    pub fn update_stats(bitmap: *mut c_char);

    // pub fn display_uncovered_points();

    pub fn set_cover_feedback(name: *const c_char);

    pub fn enable_sim_verbose();

    pub fn disable_sim_verbose();
}

static mut SIM_ARGS: Vec<String> = vec![];

fn sim_run(workload: &String) -> i32 {
    // prepare the simulation arguments in Vec<String> format
    let mut sim_args: Vec<String> = vec!["emu".to_string(), "-i".to_string(), workload.to_string()]
        .iter()
        .map(|s| s.to_string())
        .collect();
    unsafe { sim_args.extend(SIM_ARGS.iter().cloned()) };

    // convert the simulation arguments into c_char**
    let sim_args: Vec<_> = sim_args
        .iter()
        .map(|s| CString::new(s.as_bytes()).unwrap())
        .collect();
    let mut p_argv: Vec<_> = sim_args.iter().map(|arg| arg.as_ptr()).collect();
    p_argv.push(std::ptr::null());

    // send simulation arguments to sim_main and get the return code
    let ret = unsafe { sim_main(sim_args.len() as i32, p_argv.as_ptr()) };
    unsafe { update_stats(cover_as_mut_ptr()) }
    cover_accumulate();

    ret
}

fn sim_run_from_memory(input: &BytesInput) -> i32 {
    // create a workload-in-memory name for the input bytes
    let wim_bytes = input.bytes();
    let wim_addr = wim_bytes.as_ptr();
    let wim_size = wim_bytes.len() as u64;
    let wim_name = format!("wim@{wim_addr:p}+0x{wim_size:x}");
    // pass the in-memory workload to sim_run
    sim_run(&wim_name)
}

pub(crate) fn sim_run_multiple(workloads: &Vec<String>, auto_exit: bool) -> i32 {
    let mut ret = 0;
    for workload in workloads.iter() {
        ret = sim_run(workload);
        if ret != 0 {
            println!("{} exits abnormally with return code: {}", workload, ret);
            if auto_exit {
                break;
            }
        }
    }
    return ret;
}

pub static mut USE_RANDOM_INPUT: bool = false;
pub static mut CONTINUE_ON_ERRORS: bool = true;
pub static mut SAVE_ERRORS: bool = true;
// pub static mut NUM_RUNS: u64 = 0;
pub static mut MAX_RUNS: u64 = u64::MAX;

pub static mut COVER_POINTS_OUTPUT: Option<String> = None;
pub static mut FORMAL_COVER_RATE: f64 = 0.0;

pub(crate) fn fuzz_harness(input: &BytesInput) -> ExitKind {
    // insert c.nop in the beginning of the input
    let mut input_bytes = input.bytes().to_vec();
    input_bytes.insert(0, 0x00);
    input_bytes.insert(0, 0x01);
    let new_input = BytesInput::new(input_bytes);

    let ret = if unsafe { USE_RANDOM_INPUT } {
        let random_bytes: Vec<u8> = (0..1024).map(|_| rand::random::<u8>()).collect();
        let b = BytesInput::new(random_bytes);
        sim_run_from_memory(&b)
    } else {
        sim_run_from_memory(&new_input)
    };

    // get coverage
    // cover_display();
    // io::stdout().flush().unwrap();

    // panic if return code is non-zero (this is for fuzzers to catch crashes)
    let do_panic = unsafe { !CONTINUE_ON_ERRORS && ret != 0 };
    if do_panic {
        println!("<<<<<< Bug triggered >>>>>>");
        // store the accumulated coverage points
        if unsafe { COVER_POINTS_OUTPUT.is_some() } {
            store_cover_points(unsafe { COVER_POINTS_OUTPUT.as_ref().unwrap().clone() + "/cover_points.csv" });
        }
        // unsafe { display_uncovered_points() }
        panic!("<<<<<< Bug triggered >>>>>>");
    }

    // save the target testcase into disk
    let do_save = unsafe { SAVE_ERRORS && ret != 0 };
    if do_save {
        println!("<<<<<< Bug triggered >>>>>>");
        println!("<<<<<< Save the testcase >>>>>>");
        store_testcase(&new_input, &"errors".to_string(), None);
    }

    // panic to exit the fuzzer if fuzz_cover_rate < formal_cover_rate
    cover_update_cover_rate();
    let fuzz_cover_rate = cover_get_cover_rate();
    if fuzz_cover_rate < unsafe { FORMAL_COVER_RATE } {
        println!("Exit due to fuzz_cover_rate < formal_cover_rate");
        // stdout -> file & display uncovered points
        // let cover_file_path = unsafe { COVER_POINTS_OUTPUT.as_ref().unwrap().clone() + "/cover.log" };
        // let cover_file = File::create(cover_file_path).unwrap();
        // let fd = cover_file.as_raw_fd();
        // let stdout = unsafe { dup(STDOUT_FILENO) };
        // unsafe { dup2(fd, STDOUT_FILENO) };
        // unsafe { display_uncovered_points() }
        // unsafe { dup2(stdout, STDOUT_FILENO) };
        // unsafe { close(stdout) };

        // store the accumulated coverage points
        if unsafe { COVER_POINTS_OUTPUT.is_some() } {
            store_cover_points(unsafe { COVER_POINTS_OUTPUT.as_ref().unwrap().clone() + "/cover_points.csv" });
        }

        panic!("Exit due to fuzz_cover_rate < formal_cover_rate");
    }

    // panic to exit the fuzzer if max_runs is reached
    // unsafe { NUM_RUNS += 1 };
    // let do_exit = unsafe { NUM_RUNS >= MAX_RUNS };
    // if do_exit {
    //     println!("Exit due to max_runs == 0");
    //     // stdout -> file & display uncovered points
    //     let cover_file_path = unsafe { COVER_POINTS_OUTPUT.as_ref().unwrap().clone() + "/cover.log" };
    //     let cover_file = File::create(cover_file_path).unwrap();
    //     let fd = cover_file.as_raw_fd();
    //     let stdout = unsafe { dup(STDOUT_FILENO) };
    //     unsafe { dup2(fd, STDOUT_FILENO) };
    //     unsafe { display_uncovered_points() }
    //     unsafe { dup2(stdout, STDOUT_FILENO) };
    //     unsafe { close(stdout) };

    //     // store the accumulated coverage points
    //     if unsafe { COVER_POINTS_OUTPUT.is_some() } {
    //         store_cover_points(unsafe { COVER_POINTS_OUTPUT.as_ref().unwrap().clone() + "/cover_points.csv" });
    //     }

    //     panic!("Exit due to max_runs == 0");
    // }

    ExitKind::Ok
}

pub(crate) fn set_sim_env(
    coverage: String,
    verbose: bool,
    max_runs: Option<u64>,
    emu_args: Vec<String>,
) {
    let cover_name = CString::new(coverage.as_bytes()).unwrap();
    println!("{}", coverage);
    unsafe { set_cover_feedback(cover_name.as_ptr()) }

    if verbose {
        unsafe { enable_sim_verbose() }
    } else {
        unsafe { disable_sim_verbose() }
    }

    if max_runs.is_some() {
        unsafe { MAX_RUNS = max_runs.unwrap() };
    }

    unsafe {
        SIM_ARGS = emu_args;
    }

    println!("Before Cover Init\n");
    cover_init();
}

fn store_cover_points(cover_points_output: String) {
    let accumulated_points = cover_get_accumulated_points();
    let mut wtr = Writer::from_path(cover_points_output).unwrap();
    // write header
    wtr.write_record(&["Index", "Covered"]).unwrap();
    // write records
    for (i, covered) in accumulated_points.iter().enumerate() {
        wtr.write_record(&[i.to_string(), covered.to_string()]).unwrap();
    }
    wtr.flush().unwrap();
}

pub(crate) fn set_fuzz_cover_output(output: Option<String>) {
    unsafe { COVER_POINTS_OUTPUT = output };
}

pub(crate) fn set_formal_cover_rate(rate: f64) {
    unsafe { FORMAL_COVER_RATE = rate };
}

pub(crate) fn set_cover_points() {
    // read the accumulated coverage points from the file
    let cover_file_path = unsafe{ COVER_POINTS_OUTPUT.as_ref().unwrap().clone() + "/cover_points.csv" };
    let mut rdr = Reader::from_path(cover_file_path).unwrap();
    let len = unsafe{ get_cover_number() as usize };
    let mut accumulated_points = vec![0; len];
    // read header
    rdr.headers().unwrap();
    let mut count = 0;
    for result in rdr.records() {
        let record = result.unwrap();
        let idx = record[0].parse::<usize>().unwrap();
        let covered = record[1].parse::<i8>().unwrap();
        if count < 100 {
            println!("{}: {}", idx, covered);
            count += 1;
        }
        accumulated_points[idx] = covered;
    }
    cover_set_accumulated(accumulated_points);
}
