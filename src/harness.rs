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

use std::{env, time::Instant};
use std::ffi::CString;
use std::process::Command;
use std::fs;
// use std::io::{self, Write};

use crate::coverage::*;
use crate::monitor::store_testcase;


use libafl::prelude::*;
use libc::*;

use csv::{Reader, Writer};
use chrono::Local;

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

    println!("Sim args: {:?}", sim_args);

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

fn clone_to_run_sim(workload: &String) -> i32 {
    let fuzzer = format!("{}/build/fuzzer", env::var("NOOP_HOME").unwrap());
    let image: String = workload.clone();
    // prepare the simulation arguments in Vec<String> format
    let mut sim_args: Vec<String> = vec!["-c".to_string(), unsafe{COVER_NAME.clone().unwrap()} , "--".to_string(), image.to_string()]
        .iter()
        .map(|s| s.to_string())
        .collect();
    unsafe { sim_args.extend(SIM_ARGS.iter().cloned()) };
    // send simulation arguments to sim_main and get the return code
    let fuzz_id = unsafe { NUM_RUNS };
    sim_args.push("--fuzz-id".to_string());
    sim_args.push(fuzz_id.to_string());

    let ret = Command::new(fuzzer)
        .args(sim_args)
        .output()
        .expect("failed to execute process");

    println!("child stdout:\n{}\n", String::from_utf8_lossy(&ret.stdout));
    println!("child stderr:\n{}\n", String::from_utf8_lossy(&ret.stderr));

    cover_accumulate_from_file();

    if ret.status.success() {
        return 0
    }
    else {
        return -1
    }
    
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
pub static mut CONTINUE_ON_ERRORS: bool = false;
pub static mut SAVE_ERRORS: bool = false;
pub static mut NUM_RUNS: u64 = 0;
pub static mut MAX_RUNS: u64 = u64::MAX;
pub static mut FORMAL_COVER_RATE: f64 = 0.0;
pub static mut INSERT_NOP: bool = false;
pub static mut ONLY_FUZZ: bool = false;
pub static mut COVER_NAME: Option<String> = None;

pub static mut CORPUS_NUM: u64 = 0;

pub static mut COVERAGE_CHECK_TIME: Option<Instant> = None;

pub(crate) fn fuzz_harness(input: &BytesInput) -> ExitKind {
    // insert c.nop in the beginning of the input
    let mut input_bytes = input.bytes().to_vec();
    input_bytes.insert(0, 0x00);
    input_bytes.insert(0, 0x01);

    let new_input: BytesInput;
    if unsafe { USE_RANDOM_INPUT } {
        let random_bytes: Vec<u8> = (0..1024).map(|_| rand::random::<u8>()).collect();
        let b = BytesInput::new(random_bytes);
        new_input = b;
    } else {
        if unsafe { INSERT_NOP } {
            new_input = BytesInput::new(input_bytes);
        } else {
            new_input = input.clone();
        }
    };

    let ret: i32;
    let fuzz_id = unsafe { NUM_RUNS };
    if unsafe{ ONLY_FUZZ } {
        ret = sim_run_from_memory(&new_input);
        let duration = unsafe { COVERAGE_CHECK_TIME.as_ref().unwrap().elapsed().as_secs_f64() };
        if duration > 20.0 {
            unsafe { COVERAGE_CHECK_TIME = Some(Instant::now()) };
            let cover_points_output = format!("{}/tmp/fuzz_coverage.csv", env::var("NOOP_HOME").unwrap());
            store_cover_points(cover_points_output);
        }
    } else {
        let fuzz_run_dir = format!("{}/tmp/fuzz_run", env::var("NOOP_HOME").unwrap());
        let fuzz_run_id_dir = format!("{}/{}", fuzz_run_dir, fuzz_id);
        if fs::read_dir(&fuzz_run_id_dir).is_ok() {
            fs::remove_dir_all(&fuzz_run_id_dir).unwrap();
        }
        fs::create_dir_all(&fuzz_run_id_dir).unwrap();
        fs::create_dir_all(fuzz_run_id_dir.clone()+"/csr_wave").unwrap();
        fs::create_dir_all(fuzz_run_id_dir.clone()+"/csr_snapshot").unwrap();
        fs::create_dir_all(fuzz_run_id_dir.clone()+"/csr_transition").unwrap();
        store_testcase(&new_input, &fuzz_run_dir, Some("fuzz_testcase".to_string()));
        ret = clone_to_run_sim(&format!("{}/fuzz_testcase", fuzz_run_dir));
    }

    // get coverage
    // cover_display();
    // io::stdout().flush().unwrap();

    // save the target testcase into disk
    if ret != 0 {
        println!("<<<<<< Bug triggered >>>>>>");
        if unsafe { SAVE_ERRORS } {
            println!("<<<<<< Save the testcase >>>>>>");
            let timestamp = Local::now().format("%Y-%m-%d-%H-%M-%S").to_string();
            let testcase_name = format!("{}_{}", timestamp, fuzz_id);
            println!("Testcase name: {}", testcase_name);
            store_testcase(&new_input, &"errors".to_string(), Some(testcase_name));
        }
    }

    // panic if return code is non-zero (this is for fuzzers to catch crashes)
    let do_panic = unsafe { !CONTINUE_ON_ERRORS && ret != 0 };
    if do_panic {
        println!("<<<<<< Bug triggered >>>>>>");
        // store the accumulated coverage points
        store_cover_points(env::var("COVER_POINTS_OUT").unwrap()+"/cover_points.csv");
        // unsafe { display_uncovered_points() }
        panic!("<<<<<< Bug triggered >>>>>>");
    }

    // panic to exit the fuzzer if fuzz_cover_rate < formal_cover_rate
    cover_update_cover_rate();
    let mut fuzz_cover_rate = cover_get_cover_rate();
    if unsafe{NUM_RUNS < CORPUS_NUM} {
        unsafe {println!("RUNS:{}, CORPUS_NUM:{} not enough", NUM_RUNS, CORPUS_NUM) };
        fuzz_cover_rate = 100.0;
    }
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
        store_cover_points(env::var("COVER_POINTS_OUT").unwrap()+"/cover_points.csv");

        panic!("Exit due to fuzz_cover_rate < formal_cover_rate");
    }

    // panic to exit the fuzzer if max_runs is reached
    unsafe { NUM_RUNS += 1 };
    let do_exit = unsafe { NUM_RUNS >= MAX_RUNS };
    if do_exit {
        println!("Exit due to max_runs == 0");
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
        store_cover_points(env::var("COVER_POINTS_OUT").unwrap()+"/cover_points.csv");

        panic!("Exit due to max_runs == 0");
    }

    ExitKind::Ok
}

pub(crate) fn set_sim_env(
    coverage: String,
    verbose: bool,
    max_runs: Option<u64>,
    emu_args: Vec<String>,
) {
    let cover_name = CString::new(coverage.as_bytes()).unwrap();
    println!("cover type:{}", coverage);
    unsafe { COVER_NAME = Some(coverage) };
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

pub(crate) fn store_cover_points(cover_points_output: String) {
    let accumulated_points = cover_get_accumulated_points();
    let mut wtr = Writer::from_path(cover_points_output).unwrap();
    // write header
    wtr.write_record(&["Index", "Covered"]).unwrap();
    // write records
    for (i, covered) in accumulated_points.iter().enumerate() {
        wtr.write_record(&[i.to_string(), covered.to_string()])
            .unwrap();
    }
    wtr.flush().unwrap();
}

pub(crate) fn set_formal_cover_rate(rate: f64) {
    unsafe { FORMAL_COVER_RATE = rate };
}

pub(crate) fn set_insert_nop(insert_nop: bool) {
    unsafe { INSERT_NOP = insert_nop };
}

pub(crate) fn set_only_fuzz(only_fuzz: bool) {
    unsafe { ONLY_FUZZ = only_fuzz };
}

pub(crate) fn set_corpus_num(corpus_dir: String) {
    let entries = fs::read_dir(corpus_dir).unwrap();
    let count = entries.filter(|entry| entry.is_ok()).count();
    unsafe { CORPUS_NUM = count as u64 };
    println!("Set init corpus runs:{}", count);
}

pub(crate) fn set_cover_points() {
    // read the accumulated coverage points from the file
    unsafe { COVERAGE_CHECK_TIME = Some(Instant::now()) };
    let cover_file_path = env::var("COVER_POINTS_OUT").unwrap()+"/cover_points.csv";
    if fs::metadata(&cover_file_path).is_err() {
        println!("No cover points file found");
        return;
    }
    let mut rdr = Reader::from_path(cover_file_path).unwrap();
    let len = unsafe { get_cover_number() as usize };
    let mut accumulated_points = vec![0; len];
    // read header
    rdr.headers().unwrap();
    for result in rdr.records() {
        let record = result.unwrap();
        let idx = record[0].parse::<usize>().unwrap();
        let covered = record[1].parse::<i8>().unwrap();
        accumulated_points[idx] = covered;
    }
    cover_set_accumulated(accumulated_points);
}
