use std::io::BufRead;
use std::io::Write;

use vaporetto::{Predictor, Sentence};

fn main() {
    let predictor_data = include_bytes!(concat!(env!("OUT_DIR"), "/predictor.bin"));
    let (predictor, _) =
        unsafe { Predictor::deserialize_from_slice_unchecked(predictor_data) }.unwrap();

    let mut lines = vec![];
    for line in std::io::stdin().lock().lines() {
        lines.push(line.unwrap());
    }

    let mut s = Sentence::from_raw(" ").unwrap();
    let mut n_words = 0;
    // The timed loop consumes the lines; keep a copy for writing the tokens,
    // made before the timer starts and only when BENCH_TOKENS is set.
    let token_lines = std::env::var_os("BENCH_TOKENS").map(|_| lines.clone());

    let start = std::time::Instant::now();
    for line in lines {
        s.update_raw(line).unwrap();
        predictor.predict(&mut s);
        n_words += s.iter_tokens().count();
    }
    let duration = start.elapsed();

    println!("Elapsed-vaporetto: {} [sec]", duration.as_secs_f64());
    dbg!(n_words);

    // With BENCH_TOKENS=<file>, write the tokens of every line after the timed
    // loop, one per line with an empty line after each input line, for
    // segmentation.py. The timed loop above is unchanged.
    if let (Ok(path), Some(token_lines)) = (std::env::var("BENCH_TOKENS"), token_lines) {
        let mut out = std::io::BufWriter::new(std::fs::File::create(path).unwrap());
        for line in &token_lines {
            s.update_raw(line.clone()).unwrap();
            predictor.predict(&mut s);
            for token in s.iter_tokens() {
                writeln!(out, "{}", token.surface()).unwrap();
            }
            writeln!(out).unwrap();
        }
    }
}
