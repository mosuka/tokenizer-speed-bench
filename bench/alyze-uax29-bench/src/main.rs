use std::io::BufRead;

use alyze::uax29::word::{self, Options};

fn main() {
    let mut lines = vec![];
    for line in std::io::stdin().lock().lines() {
        lines.push(line.unwrap());
    }

    // The UAX #29 word tokenizer reports every span between word boundaries,
    // spaces and punctuation included. Only word-like spans are counted; the
    // timed part is the whole scan either way.
    let mut n_words = 0;
    let start = std::time::Instant::now();
    for line in &lines {
        word::tokenize(line, Options::default(), |_end, props| {
            if props.is_word_like() {
                n_words += 1;
            }
            true
        });
    }
    let duration = start.elapsed();

    println!("Elapsed-alyze-uax29: {} [sec]", duration.as_secs_f64());
    dbg!(n_words);
}
