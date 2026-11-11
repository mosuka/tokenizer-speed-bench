use std::io::BufRead;

use alyze::cjk::kuromoji::{self, Mode, Options, Tokens};

fn main() {
    let mut lines = vec![];
    for line in std::io::stdin().lock().lines() {
        lines.push(line.unwrap());
    }

    // Normal mode does not decompound, like the lindera, mecab and vibrato
    // rows; alyze's default is Search mode. Punctuation is discarded, which is
    // the default.
    let mut options = Options::default();
    options.mode = Mode::Normal;
    // Reused across lines, as alyze intends; tokenize() clears it first.
    let mut tokens = Tokens::new();

    let mut n_words = 0;
    let start = std::time::Instant::now();
    for line in &lines {
        kuromoji::tokenize(line, options, &mut tokens);
        n_words += tokens.len();
    }
    let duration = start.elapsed();

    println!("Elapsed-alyze-kuromoji: {} [sec]", duration.as_secs_f64());
    dbg!(n_words);
}
