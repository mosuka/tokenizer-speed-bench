use std::io::BufRead;

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
}
