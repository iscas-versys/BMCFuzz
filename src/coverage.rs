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

use std::time::Instant;

struct Coverage {
    cover_points: Vec<i8>,
    accumulated: Vec<i8>,
    accumulated_num: usize,
    start_time: Instant,
}

impl Coverage {
    pub fn new(n_cover: usize) -> Self {
        Self {
            cover_points: vec![0; n_cover],
            accumulated: vec![0; n_cover],
            accumulated_num: 0,
            start_time: Instant::now(),
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

    pub fn display(&self) {
        // println!("Total Covered Points: {:?}", self.accumulated);
        println!(
            "Total Coverage:       {:.3}%",
            self.get_accumulative_coverage()
        );
    }

    pub fn get_cover_rate(&self) -> f64 {
        let duration = self.start_time.elapsed().as_secs_f64();
        println!("Covered Points: {:?}", self.accumulated_num);
        println!("Duration: {:.3}s", duration);
        println!("Cover Rate: {:.3} points/s", self.accumulated_num as f64 / duration);
        self.accumulated_num as f64 / duration
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

pub(crate) fn cover_display() {
    unsafe { ICOVERAGE.as_ref().unwrap().display() }
}

pub(crate) fn cover_get_accumulated_points() -> Vec<i8> {
    unsafe { ICOVERAGE.as_ref().unwrap().accumulated.clone() }
}

pub(crate) fn cover_get_cover_rate() -> f64 {
    unsafe { ICOVERAGE.as_ref().unwrap().get_cover_rate() }
}
