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
use crate::harness::get_cover_number;

use std::collections::VecDeque;
use std::time::Instant;
use std::env;

use csv::Reader;

const RATE_WINDOW_SIZE: usize = 100;

struct Coverage {
    cover_points: Vec<i8>,
    accumulated: Vec<i8>,
    accumulated_num: usize,
    pre_accumulated_num: usize,
    start_time: Instant,
    rate_window: VecDeque<f64>,
    rate_sum: f64,
}

impl Coverage {
    pub fn new(n_cover: usize) -> Self {
        Self {
            cover_points: vec![0; n_cover],
            accumulated: vec![0; n_cover],
            accumulated_num: 0,
            pre_accumulated_num: 0,
            start_time: Instant::now(),
            rate_window: VecDeque::with_capacity(RATE_WINDOW_SIZE),
            rate_sum: 0.0,
        }
    }

    pub fn set_accumulated(&mut self, accumulated: Vec<i8>) {
        self.accumulated = accumulated;
    }

    pub fn len(&self) -> usize {
        self.cover_points.capacity()
    }

    pub fn as_mut_ptr(&self) -> *mut i8 {
        self.cover_points.as_ptr().cast_mut()
    }

    pub fn accumulate(&mut self) {
        for (i, covered) in self.cover_points.iter().enumerate() {
            if *covered != 0 as i8 && self.accumulated[i] == 0 {
                self.accumulated[i] = 1;
                self.accumulated_num += 1;
            }
        }
    }

    pub fn get_accumulative_coverage(&self) -> f64 {
        let mut covered_num: usize = 0;
        for covered in self.accumulated.iter() {
            if *covered != 0 as i8 {
                covered_num += 1;
            }
        }
        100.0 * covered_num as f64 / self.len() as f64
    }

    pub fn accumulate_from_file(&mut self) {
        let cover_points_file = format!("{}/tmp/sim_run_cover_points.csv", env::var("NOOP_HOME").unwrap());
        let mut reader = Reader::from_path(cover_points_file).unwrap();
        reader.headers().unwrap();
        for record in reader.records() {
            let record = record.unwrap();
            let index: usize = record[0].parse().unwrap();
            let covered: i8 = record[1].parse().unwrap();
            if covered != 0 && self.accumulated[index] == 0 {
                self.accumulated[index] = 1;
                self.accumulated_num += 1;
            }
        }
    }

    pub fn display_coverage(&self) {
        // println!("Total Covered Points: {:?}", self.accumulated);
        println!(
            "Total Coverage:       {:.3}%",
            100.0 * self.accumulated_num as f64 / self.len() as f64
        );
    }

    pub fn update_cover_rate(&mut self) {
        let duration = self.start_time.elapsed().as_secs_f64();
        self.start_time = Instant::now();
        let new_cover_rate = (self.accumulated_num - self.pre_accumulated_num) as f64 / duration;
        self.pre_accumulated_num = self.accumulated_num;
        if self.rate_window.len() == RATE_WINDOW_SIZE {
            if let Some(old_cover_rate) = self.rate_window.pop_front() {
                self.rate_sum -= old_cover_rate;
            }
        }
        self.rate_window.push_back(new_cover_rate);
        self.rate_sum += new_cover_rate;
        println!("Covered Points: {}", self.accumulated_num);
        self.display_coverage();
        println!(
            "Cover Rate: {:.3} per second",
            self.rate_sum / self.rate_window.len() as f64
        );
    }

    pub fn get_cover_rate(&self) -> f64 {
        if self.rate_window.len() < RATE_WINDOW_SIZE {
            println!(
                "Cover Rate Window Size: {}(not enough)",
                self.rate_window.len()
            );
            100.0
        } else {
            self.rate_sum / self.rate_window.len() as f64
        }
    }
}

static mut ICOVERAGE: Option<Coverage> = None;

pub(crate) fn cover_init() {
    unsafe { ICOVERAGE = Some(Coverage::new(get_cover_number() as usize)) };
}

pub(crate) fn cover_set_accumulated(accumulated: Vec<i8>) {
    unsafe { ICOVERAGE.as_mut().unwrap().set_accumulated(accumulated) }
}

pub(crate) fn cover_len() -> usize {
    unsafe { ICOVERAGE.as_ref().unwrap().len() }
}

pub(crate) fn cover_as_mut_ptr() -> *mut i8 {
    unsafe { ICOVERAGE.as_ref().unwrap().as_mut_ptr() }
}

pub(crate) fn cover_accumulate() {
    unsafe { ICOVERAGE.as_mut().unwrap().accumulate() }
}

pub(crate) fn cover_accumulate_from_file() {
    unsafe { ICOVERAGE.as_mut().unwrap().accumulate_from_file() }
}

pub(crate) fn cover_display() {
    unsafe { ICOVERAGE.as_ref().unwrap().display_coverage() }
}

pub(crate) fn cover_get_accumulated_points() -> Vec<i8> {
    unsafe { ICOVERAGE.as_ref().unwrap().accumulated.clone() }
}

pub(crate) fn cover_update_cover_rate() {
    unsafe { ICOVERAGE.as_mut().unwrap().update_cover_rate() }
}

pub(crate) fn cover_get_cover_rate() -> f64 {
    unsafe { ICOVERAGE.as_ref().unwrap().get_cover_rate() }
}
