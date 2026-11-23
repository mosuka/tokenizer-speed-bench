use std::io::BufRead;
use std::io::Write;

use alyze::cjk::nori::{self, DecompoundMode, Options, Tokens};

fn main() {
    let mut lines = vec![];
    for line in std::io::stdin().lock().lines() {
        lines.push(line.unwrap());
    }

    // DecompoundMode::None emits dictionary entries whole, like the lindera
    // ko-dic row; alyze's default is Discard, which splits compound entries
    // into their morphemes. Punctuation is discarded, which is the default.
    let mut options = Options::default();
    options.decompound_mode = DecompoundMode::None;
    // Reused across lines, as alyze intends; tokenize() clears it first.
    let mut tokens = Tokens::new();

    let mut n_words = 0;
    let start = std::time::Instant::now();
    for line in &lines {
        nori::tokenize(line, options, &mut tokens);
        n_words += tokens.len();
    }
    let duration = start.elapsed();

    println!("Elapsed-alyze-nori: {} [sec]", duration.as_secs_f64());
    dbg!(n_words);

    // With BENCH_TOKENS=<file>, write the tokens of every line after the timed
    // loop, one per line with an empty line after each input line, for
    // segmentation.py. The timed loop above is unchanged.
    if let Ok(path) = std::env::var("BENCH_TOKENS") {
        let mut out = std::io::BufWriter::new(std::fs::File::create(path).unwrap());
        for line in &lines {
            nori::tokenize(line, options, &mut tokens);
            for token in tokens.iter() {
                writeln!(out, "{}", &line[token.byte_range.clone()]).unwrap();
            }
            writeln!(out).unwrap();
        }
    }
}
